# Copyright (c) 2020 Michael de Gans
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
GstEngine lives here (multiprocessing.Process subclass).
"""

import os
import functools
import multiprocessing
import queue
import logging

# import gstreamer bidings
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import (
    Gst,
    GLib,
)
from typing import (
    Any,
    Callable,
    Iterable,
    Optional,
    Sequence,
)
from libs.detectors.deepstream._ds_utils import bin_to_pdf
from libs.detectors.deepstream._ds_config import GstConfig

__all__ = [
    'GstEngine',
    'GstLinkError',
    'link_many',
    'PadProbeCallback',
]

PadProbeCallback = Callable[
    [Gst.Pad, Gst.PadProbeInfo, Any],
    Gst.PadProbeReturn,
]
"""
Signature of Gsteamer Pad Probe Callback
"""

# a documentation template for an elemetn creation function
# TODO(mdegans): remove after refactoring elem creation methods
_ELEM_DOC = """
Create {elem_name} Gst.Element and add to the pipeline.

Returns:
    bool: False on failure, True on success.
"""


class GstLinkError(RuntimeError):
    """on failure to link pad or element"""

def link(a: Gst.Element, b: Gst.Element):
    """
    Link Gst.Element a to b

    Use this to avoid the checking for true on exit,
    which is very C, but not very Pythonic.

    (Always Availability of src and sink pads)

    Raises:
        LinkError: on failure to link.
    """
    if not a.link(b):
        raise GstLinkError(f'could not link {a.name} to {b.name}')

def link_many(elements: Iterable[Gst.Element]):
    """
    Link many Gst.Element.
    
    (linear, assumes Always Availability of src and sink pads).

    Returns:
        bool: False on failure, True on success.
    """
    elements = iter(elements)
    last = next(elements)
    for current in elements:
        if not last.link(current):
            raise GstLinkError(f'could not link {last.name} to {current.name}')


class GstEngine(multiprocessing.Process):
    """
    GstEngine is an internal engine for GStreamer.

    It is a subclass of multiprocessing.Process to run a GLib.MainLoop in
    a separate process. There are several reasons for this:
    
    * GStreamer elements can have memory leaks so if and when the processes
      crashes, it can be restarted without having to restart the whole app.
      In general GStreamer is as buggy as it is fast and the quality of elements
      runs the gamut.
    * Python callbacks called by GLib.MainLoop can block the whole MainLoop.
      (The same is true in C, but you can launch CPU bound stuff in a thread, 
      which is not possible in Python due to the GIL). Running GLib.MainLoop
      it in a separate process and putting the results into a queue if a slot
      is empty (dropping the results if not), avoids this problem.
    * Ease of adding and removing new sources. With DeepStream, right now, the
      *easiest* and most reliable way to do this is to relaunch it's process
      with a modified configuration.

    Arguments:
        config (:obj:`GstConfig`):
            GstConfig instance for this engine (wraps sd.core.ConfigEngine).
        debug (bool, optional):
            log all bus messages to the debug level
            (this can mean a lot of spam, but can also be useful if things are
            misbehaving)
        blocking (bool, optional):
            if set to true, attempts to access the .results property will block
            for .queue_timeout seconds waiting for results. If no results are
            ready after that, None is returned. If set to false, and a result is
            not ready, None will be returned immediately.

    Attributes:
        logger (:obj:`logging.Logger`):
            Python logger for the class.
        queue_timeout (int): 
            (default: 15 seconds) timeout for the blocking argument/attribute.
        feed_name (str):
            (default: 'default') the feed name portion of the uri.
        web_root (str):
            The default web root path.
            (default: '/repo/data/web_gui')
        IGNORED_MESSAGES(:obj:`tuple` of :obj:`Gst.MessageType`):
            Gst.MessageType to be ignored by on_bus_message.

    Examples:

        NOTE: the default GstConfig pipeline is:
              uridecodebin ! concat ! identity ... identity ! fakesink,

        Real-world subclasses can override GstConfig to set different source,
        sink, and inference elements. See GstConfig documentation for details.

    """

    IGNORED_MESSAGES = tuple()  # type: Tuple[Gst.MessageType]

    logger = logging.getLogger('GstEngine')
    # TODO(mdegans): make these properties that warn when a set is attempted
    #  after the processs has started since these are copied at that point
    #  (since this is a process) and re-assignment won't work.
    queue_timeout=10
    feed_name = 'default'
    web_root = '/repo/data/web_gui'
    # this is to dump .dot and .pdf
    logdir = '/tmp'

    def __init__(self, config:GstConfig, *args, debug=False, blocking=False, **kwargs):
        self.logger.debug('__init__')
        super().__init__(*args, **kwargs)
        # set debug for optional extra logging
        self._debug = debug

        # the pipeline configuration
        self._gst_config = config  # type: GstConfig

        # GStreamer main stuff
        self._main_loop = None # type: GLib.MainLoop
        self._pipeline = None  # type: Gst.Pipeline
        # GStreamer elements (in order of connection)
        self._sources = []  # type: List[Gst.Element]
        self._muxer = None  # type: Gst.Element
        self._muxer_lock = GLib.Mutex()
        self._infer_elements = []  # type: List[Gst.Element]
        self._tracker = None  # type: Gst.Element
        self._distance = None  # type: Gst.Element
        self._payload = None  # type: Gst.Element
        self._broker = None # type: Gst.Element
        self._osd_converter = None  # type: Gst.Element
        self._tiler = None  # type: Gst.Element
        self._tiler_probe_id = None # type: int
        self._osd = None  # type: Gst.Element
        self._sink = None  # type: Gst.Element

        # process communication primitives
        self._result_queue = multiprocessing.Queue(maxsize=1)
        self._stop_requested = multiprocessing.Event()
        # todo: make this a property with proper ipc:
        # so it can be changed after start
        self.blocking=blocking

    @property
    def results(self) -> Sequence[str]:
        """
        Get results waiting in the queue.

        (may block, depending on self.queue_timeout)

        May return None if no result ready.

        Logs to WARNING level on failure to fetch result.
        """
        try:
            return self._result_queue.get(block=self.blocking, timeout=self.queue_timeout)
        except queue.Empty:
            self.logger.warning("failed to get results from queue (queue.Empty)")
            return None
        except TimeoutError:
            self.logger.info("waiting for results...")
            return None

    def _update_result_queue(self, results: str):
        """
        Called internally by the GStreamer process.

        Update results queue with serialize payload. Should probably be called
        by the subclass implemetation of on_buffer().

        Does not block (because this would block the GLib.MainLoop).

        Can fail if the queue is full in which case the results will
        be dropped and logged to the WARNING level.

        Returns:
            bool: False on failure, True on success.
        """
        if self._result_queue.empty():
            try:
                self._result_queue.put_nowait(results)
                return True
            except queue.Full:
                self.logger.warning({'dropped': results})
                return False

    def on_bus_message(self, bus: Gst.Bus, message: Gst.Message, *_) -> bool:
        """
        Default bus message callback.

        This implementation does the following on each message type:

        Ignored:
            any Gst.MessageType in GstEngine.IGNORED_MESSAGES
        
        Logged:
            Gst.MessageType.STREAM_STATUS
            Gst.MessageType.STATE_CHANGED
            Gst.MessageType.WARNING
            (all others)

        call self._quit():
            Gst.MessageType.EOS
            Gst.MessageType.ERROR
        """
        # TAG and DURATION_CHANGED seem to be the most common
        if message.type in self.IGNORED_MESSAGES:
            pass
        elif message.type == Gst.MessageType.STREAM_STATUS:
            status, owner = message.parse_stream_status()  # type: Gst.StreamStatusType, Gst.Element
            self.logger.debug(f"{owner.name}:status:{status.value_name}")
        elif message.type == Gst.MessageType.STATE_CHANGED:
            old, new, _ = message.parse_state_changed()  # type: Gst.State, Gst.State, Gst.State
            self.logger.debug(
                f"{message.src.name}:state-change:"
                f"{old.value_name}->{new.value_name}")
        elif message.type == Gst.MessageType.EOS:
            self.logger.debug(f"Got EOS")
            self._quit()
        elif message.type == Gst.MessageType.ERROR:
            err, errmsg = message.parse_error()  # type: GLib.Error, str
            self.logger.error(f'{err}: {errmsg}')
            self._quit()
        elif message.type == Gst.MessageType.WARNING:
            err, errmsg = message.parse_warning()  # type: GLib.Error, str
            self.logger.warning(f'{err}: {errmsg}')
        else:
            if self._debug:
                self.logger.debug(
                    f"{message.src.name}:{Gst.MessageType.get_name(message.type)}")
        return True

    def _create_pipeline(self) -> bool:
        """
        Attempt to create pipeline bin.

        Returns:
            bool: False on failure, True on success.
        """
        # create the pipeline and check
        self.logger.debug('creating pipeline')
        self._pipeline = Gst.Pipeline()
        if not self._pipeline:
            self.logger.error('could not create Gst.Pipeline element')
            return False
        return True

    # TODO(mdegans): some of these creation methods can probably be combined

    def _create_sources(self) -> bool:
        # create a source and check
        for conf in self._gst_config.src_configs:
            self.logger.debug(f'creating source: {self._gst_config.SRC_TYPE}')
            src = Gst.ElementFactory.make(self._gst_config.SRC_TYPE)  # type: Gst.Element
            if not src:
                self.logger.error(f'could not create source of type: {self._gst_config.SRC_TYPE}')
                return False

            self.logger.debug('')

            # set properties on the source
            for k, v in conf.items():
                src.set_property(k, v)
            src.set_property('async_handling', True)
            src.set_property('caps', Gst.Caps.from_string("video/x-raw(ANY)"))
            src.set_property('expose-all-streams', False)


            # add the source to the pipeline and check
            self._pipeline.add(src)

            # append the source to the _sources list
            self._sources.append(src)
        return True
    _create_sources.__doc__ = _ELEM_DOC.format(elem_name='`self.config.SRC_TYPE`')

    def _create_element(self, e_type:str) -> Optional[Gst.Element]:
        """
        Create a Gst.Element and add to the pipeline.

        Arguments:
            e_type (str):
                The FOO_TYPE of elememt to add defined on the config class
                as an attribute eg. MUXER_TYPE, SRC_TYPE... This argument is
                case insensitive. choices are: ('muxer', 'src', 'sink')

                Once the element of the corresponding type on the config is
                made using Gst.ElementFactory.make, it will be added to 
                self._pipeline and assigned to self._e_type. 

        Returns:
            A Gst.Element if sucessful, otherwise None.
        
        Raises:
            AttributeError if e_type doesn't exist on the config and the class.
        """
        # NOTE(mdegans): "type" and "name" are confusing variable names considering
        #  GStreamer's and Python's usage of them. Synonyms anybody?
        e_type = e_type.lower()
        e_name = getattr(self._gst_config, f'{e_type.upper()}_TYPE')
        props = getattr(self._gst_config, f'{e_type}_config')  # type: dict
        self.logger.debug(f'creating {e_type}: {e_name} with props: {props}')

        # make an self.gst_config.E_TYPE_TYPE element
        elem = Gst.ElementFactory.make(e_name)
        if not elem:
            self.logger.error(f'could not create {e_type}: {e_name}')
            return

        # set properties on the element
        if props:
            for k, v in props.items():
                elem.set_property(k, v)
        
        # assign the element to self._e_type
        setattr(self, f'_{e_type}', elem)

        # add the element to the pipeline and check
        self._pipeline.add(elem)

        return elem

    def _create_infer_elements(self) -> bool:
        """
        Create GstConfig.INFER_TYPE elements, add them to the pipeline,
        and append them to self._infer_elements for ease of access / linking.

        Returns:
            bool: False on failure, True on success.
        """
        self.logger.debug('creating inference elements')
        for conf in self._gst_config.infer_configs:
            # create and check inference element
            elem = Gst.ElementFactory.make(self._gst_config.INFER_TYPE)  # type: Gst.Element
            if not elem:
                self.logger.error(f"failed to create {self._gst_config.INFER_TYPE} element")
                return False

            # set properties on inference element
            for k, v in conf.items():
                elem.set_property(k, v)

            # add the elements to the pipeline and check
            self._pipeline.add(elem)
            # oddly, add returns false even when the log shows success

            # append the element to the list of inference elements
            self._infer_elements.append(elem)
        return True

    def _create_sink(self, pipe_string: str = None):
        """
        Create a Gst.Bin sink from a pipeline string
        """
        try:
            #TODO(mdegans): urlparse and path join on the paths
            # (to validate the uri and avoid "//" and such)
            public_url = self._gst_config.master_config.config['App']['PublicUrl']
            playlist_root = f'{public_url}/static/gstreamer/{self.feed_name}'
            #TODO(mdegans): make the base path a uri for testing
            video_root = f'{self.web_root}/static/gstreamer/{self.feed_name}'
            if not pipe_string:
                encoder = self._gst_config.master_config.config['App']['Encoder']
                pipe_string = f' {encoder} ! mpegtsmux ! hlssink ' \
                    f'sync=true ' \
                    f'max-files=15 target-duration=5 ' \
                    f'playlist-root={playlist_root} ' \
                    f'location={video_root}/video_%05d.ts ' \
                    f'playlist-location={video_root}/playlist.m3u8'
            self.logger.debug(f'sink bin string: {pipe_string}')
            self._sink = Gst.parse_bin_from_description(pipe_string, True)
            dot_filename = bin_to_pdf(
                self._sink, Gst.DebugGraphDetails.ALL, f'{self.__class__.__name__}.sink.created')
            if dot_filename:
                self.logger.debug(
                    f'.dot file written to {dot_filename}')
            if not self._sink:
                # i don't think it's possble to get here unless gstreamer is
                # broken
                return False
            self._pipeline.add(self._sink)

            return True
        except (GLib.Error, KeyError):
            self.logger.error("sink creation failed", exc_info=True)
            return False

    def _create_all(self) -> int:
        """
        Create and link the pipeline from self.config.

        Returns:
            bool: False on failure, True on success.
        """
        create_funcs = (
            self._create_pipeline,
            self._create_sources,
            functools.partial(self._create_element, 'muxer'),
            functools.partial(self._create_element, 'tracker'),
            self._create_infer_elements,
            functools.partial(self._create_element, 'distance'),
            functools.partial(self._create_element, 'payload'),
            functools.partial(self._create_element, 'broker'),
            functools.partial(self._create_element, 'osd_converter'),
            functools.partial(self._create_element, 'tiler'),
            functools.partial(self._create_element, 'osd'),
            self._create_sink,
        )

        for i, f in enumerate(create_funcs):
            if not f():
                self.logger.error(
                    f"Failed to create DsEngine pipeline at step {i}")
                return False
        return True

    def _on_source_src_pad_create(self, element: Gst.Element, src_pad: Gst.Pad):
        """
        Callback to link sources to the muxer.
        """
        # a lock is required so that identical pads are not requested.
        # GLib.Mutex is required because python's isn't respected by GLib's MainLoop
        self._muxer_lock.lock()
        try:
            self.logger.debug(f'{element.name} new pad: {src_pad.name}')
            self.logger.debug(
                f'{src_pad.name} caps:{src_pad.props.caps}')
            muxer_sink_pad_name = f'sink_{self._muxer.numsinkpads}'
            self.logger.debug(f'{self._muxer.name}:requesting pad:{muxer_sink_pad_name}')
            muxer_sink = self._muxer.get_request_pad(muxer_sink_pad_name)
            if not muxer_sink:
                self.logger.error(
                    f"failed to get request pad from {self._muxer.name}")
            self.logger.debug(
                f'{muxer_sink.name} caps:{muxer_sink.props.caps}')
            ret = src_pad.link(muxer_sink)
            if not ret == Gst.PadLinkReturn.OK:
                self.logger.error(
                    f"failed to link source to muxer becase {ret.value_name}")
                self._quit()
        finally:
            self._muxer_lock.unlock()

    def _link_pipeline(self) -> bool:
        """
        Attempt to link the entire pipeline.

        Returns:
            bool: False on failure, True on success.
        """
        self.logger.debug('linking pipeline')

        # arrange for the sources to link to the muxer when they are ready
        # (uridecodebin has "Sometimes" pads so needs to be linked by callback)
        for source in self._sources:  # type: Gst.Element
            source.connect('pad-added', self._on_source_src_pad_create)

        try:
            # link the muxer to the first inference element
            link(self._muxer, self._infer_elements[0])
            link(self._infer_elements[0], self._tracker)
            # if there are secondary inference elements
            if self._infer_elements[1:]:
                link_many((self._tracker, *self._infer_elements[1:]))
                # link the final inference element to distancing engine
                link(self._infer_elements[-1], self._distance)
            else:
                # link tracker directly to the distancing element
                link(self._tracker, self._distance)
            link(self._distance, self._payload)
            # TODO(mdegans): rename osd_converter
            # (this requires some changes elsewhere)
            link(self._payload, self._osd_converter)
            link(self._osd_converter, self._tiler)
            link(self._tiler, self._osd)
            link(self._osd, self._sink)
        except GstLinkError as err:
            self.logger.error(f"pipeline link fail because: {err}")
            return False
        self.logger.debug('linking pipeline successful')
        return True

    def on_buffer(self, pad: Gst.Pad, info: Gst.PadProbeInfo, _: None, ) -> Gst.PadProbeReturn:
        """
        Default source pad probe buffer callback for the sink.

        Simply returns Gst.PadProbeReturn.OK, signaling the buffer
        shuould continue down the pipeline.
        """
        return Gst.PadProbeReturn.OK

    def stop(self):
        """Stop the GstEngine process."""
        self.logger.info('requesting stop')
        self._stop_requested.set()

    def _quit(self) -> Gst.StateChangeReturn:
        """
        Quit the GLib.MainLoop and set the pipeline to NULL.

        Called by _on_stop. A separate function for testing purposes.
        """
        self.logger.info(f'{self.__class__.__name__} quitting.')
        if self._main_loop and self._main_loop.is_running():
            self._main_loop.quit()
        if self._pipeline:
            self._write_pdf('quit')
            self.logger.debug('shifting pipeline to NULL state')
            ret = self._pipeline.set_state(Gst.State.NULL)
            if ret == Gst.StateChangeReturn.ASYNC:
                ret = self._pipeline.get_state(10)
            if ret == Gst.StateChangeReturn.SUCCESS:
                return
            else:
                self.logger.error(
                    'Failed to quit cleanly. Self terminating.')
                self.terminate()  # send SIGINT to self

    def _on_stop(self):
        """
        Callback to shut down the process if stop() has been called.
        """
        if self._stop_requested.is_set():
            self.logger.info(f'stopping {self.__class__.__name__}')
            self._quit()
            # clear stop_requested state
            self._stop_requested.clear()
            self.logger.info(f'{self.__class__.__name__} cleanly stopped')

    def _write_pdf(self, suffix: str):
        # create a debug pdf from the pipeline
        dot_filename = bin_to_pdf(
            self._pipeline, Gst.DebugGraphDetails.ALL, f'{self.__class__.__name__}.pipeline.{suffix}')
        if dot_filename:
            self.logger.debug(
                f'.dot file written to {dot_filename}')

    def run(self):
        """Called on start(). Do not call this directly."""
        self.logger.debug('run() called. Initializing Gstreamer.')

        # set the .dot file dump path (this must be done prior to Gst.init)
        if 'GST_DEBUG_DUMP_DOT_DIR' not in os.environ:
            os.environ['GST_DEBUG_DUMP_DOT_DIR'] = self.logdir

        # initialize GStreamer
        Gst.init_check(None)

        # create pipeline,
        # create and add all elements:
        if not self._create_all():
            self.logger.debug('could not create pipeline')
            return self._quit()

        # register bus message callback
        bus = self._pipeline.get_bus()
        if not bus:
            self.logger.error('could not get bus')
            return self._quit()

        self.logger.debug('registering bus message callback')
        bus.add_watch(GLib.PRIORITY_DEFAULT, self.on_bus_message, None)

        # link all pipeline elements:
        if not self._link_pipeline():
            self.logger.error('could not link pipeline')
            return self._quit()

        # register pad probe buffer callback on the tiler
        self.logger.debug('registering self.on_buffer() callback on osd sink pad')
        tiler_sink_pad = self._tiler.get_static_pad('sink')
        if not tiler_sink_pad:
            self.logger.error('could not get osd sink pad')
            return self._quit()

        self._tiler_probe_id = tiler_sink_pad.add_probe(
            Gst.PadProbeType.BUFFER, self.on_buffer, None)

        # register callback to check for the stop event when idle.
        # TODO(mdegans): test to see if a higher priority is needed.
        self.logger.debug('registering self._on_stop() idle callback with GLib MainLoop')
        GLib.idle_add(self._on_stop)

        # write a pdf before we attempt to start the pipeline
        self._write_pdf('linked')

        # set the pipeline to the playing state
        self.logger.debug('setting pipeline to PLAYING state')
        self._pipeline.set_state(Gst.State.PLAYING)

        # write a pipeline after set the pipeline to PLAYING
        self._write_pdf('playing')

        # create and run the main loop.
        # this has a built-in signal handler for SIGINT
        self.logger.debug('creating the GLib.MainLoop')
        self._main_loop = GLib.MainLoop()
        self.logger.debug('starting the GLib.MainLoop')
        self._main_loop.run()
        self.logger.info("complete.")
