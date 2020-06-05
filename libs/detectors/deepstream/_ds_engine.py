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
DsEngine lives here (GstEngine multprocessing.Process subclass)
"""

import configparser
import tempfile
import logging
import queue

# import gstreamer bidings
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import (
    Gst,
    GLib,
)
# import python deepstream
from libs.detectors.deepstream import pyds
# import config stuff
from libs.detectors.deepstream._ds_config import (
    GstConfig,
    DsConfig,
    ElemConfig,
)
# import metadata stuff
from libs.distance_pb2 import (
    Batch,
    Frame,
    Person,
    BBox,
)
from libs.detectors.deepstream._gst_engine import GstEngine
# typing
from typing import (
    Any,
    Callable,
    Iterator,
    Iterable,
    Optional,
    List,
    Mapping,
    TYPE_CHECKING,
)

__all__ = [
    'DsEngine',
    'frame_meta_iterator',
    'obj_meta_iterator',
]

# these two functions below are used by DsEngine to parse pyds metadata

def frame_meta_iterator(frame_meta_list: GLib.List,
                        reverse=False) -> Iterator[pyds.NvDsFrameMeta]:
    """
    Iterate through DeepStream frame metadata GList (doubly linked list).

    Arguments:
        Reverse (bool): iterate in reverse (with .previous)
    """
    # generators catch StopIteration to stop iteration,
    while frame_meta_list is not None:
        yield pyds.glist_get_nvds_frame_meta(frame_meta_list.data)
        # a Glib.List is a doubly linked list where .data is the content
        # and 'next' and 'previous' contain to the next and previous elements
        frame_meta_list = frame_meta_list.next if not reverse else frame_meta_list.previous

def obj_meta_iterator(obj_meta_list: GLib.List,
                      reverse=False) -> Iterator[pyds.NvDsObjectMeta]:
    """
    Iterate through DeepStream object metadata GList (doubly linked list).

    Arguments:
        Reverse (bool): iterate in reverse (with .previous)
    """
    while obj_meta_list is not None:
        yield pyds.glist_get_nvds_object_meta(obj_meta_list.data)
        obj_meta_list = obj_meta_list.next if not reverse else obj_meta_list.previous

def write_config(tmpdir, config:dict) -> str:
    """
    Write a nvinfer config to a .ini file in tmpdir and return the filename.

    The section heading is [property]

    Example:
        >>> config = {
        ...     'model-file': 'foo.caffemodel',
        ...     'proto-file': 'foo.prototxt',
        ...     'labelfile-path': 'foo.labels.txt',
        ...     'int8-calib-file': 'foo_cal_trt.bin',
        ... }
        >>> with tempfile.TemporaryDirectory() as tmp:
        ...     filename = write_config(tmp, config)
        ...     print(filename)
        ...     with open(filename) as f:
        ...         for l in f:
        ...             print(l, end='')
        /tmp/tmp.../config....ini
        [property]
        model-file = foo.caffemodel
        proto-file = foo.prototxt
        labelfile-path = foo.labels.txt
        int8-calib-file = foo_cal_trt.bin
        <BLANKLINE>
    """
    # TODO(mdegans): simple property validation to fail fast
    cp = configparser.ConfigParser()
    cp['property'] = config
    fd, filename = tempfile.mkstemp(
        prefix='config',
        suffix='.ini',
        dir=tmpdir,
        text=True,
    )
    with open(fd, 'w') as f:
        cp.write(f)
    return filename

class DsEngine(GstEngine):
    """
    DeepStream implemetation of GstEngine.
    """

    _tmp = None  # type: tempfile.TemporaryDirectory
    _previous_scores = None

    def _quit(self):
        # cleanup the temporary directory we created on __init__
        self._tmp.cleanup()
        # this can self terminate so it should be called last:
        super()._quit()

    @property
    def tmp(self):
        """
        Path to the /tmp/ds_engine... folder used by this engine.

        This path is normally deleted on self._quit()
        """
        return self._tmp.name

    _previous_broker_results = None
    def on_buffer(self, pad: Gst.Pad, info: Gst.PadProbeInfo, _: None, ) -> Gst.PadProbeReturn:
        """
        Get serialized Batch level protobuf string from self._broker
        and put it in the result queue.

        connected to the tiler element's sink pad
        """
        # get result, and if same as the last, skip it
        # yeah, using a GObject property for this is kind
        # of odd, but it works. In the future I may make a broker
        # and put it in the gi.repository so it'll be easier
        # to do this:
        proto_str = self._broker.get_property("results")
        if proto_str == self._previous_broker_results:
            return Gst.PadProbeReturn.OK
        self._last_on_buffer_result = proto_str
        # we try to update the results queue, but it might be full if
        # the results queue is full becauase the ui process is too slow
        # (I haven't had this happen, but it covers this)
        if not self._update_result_queue(proto_str):
            # note: this can hurt performance depending on your logging
            # backend (anything that blocks, which is a lot.), but really,
            # if we reach this point, something is already hurting,
            # and it's probably better to save the data.
            self.logger.warning({'dropped_batch_proto': proto_str})
            # NOTE(mdegans): we can drop the whole buffer here if we want to drop
            # entire buffers (batches, including images) along with the metadata
            # return Gst.PadProbeReturn.DROP
            pass
        # return pad probe ok, which passes the buffer on
        return Gst.PadProbeReturn.OK

    def run(self):
        self._tmp = tempfile.TemporaryDirectory(prefix='ds_engine')
        super().run()

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
