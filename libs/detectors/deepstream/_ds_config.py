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
DsConfig and GstConfig wrappers live here (they wrap ConfigEngine).
"""

import os
import logging

from math import (
    log,
    ceil,
    sqrt,
)

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import (
    Gst,
)

from typing import (
    TYPE_CHECKING,
    Any,
    Tuple,
    Iterable,
    Mapping,
    Union,
    List,
)
if TYPE_CHECKING:
    from libs.config_engine import ConfigEngine
else:
    ConfigEngine = None

__all__ = [
    'DsConfig',
    'ElemConfig',
    'GstConfig',
]

from libs.detectors.deepstream._ds_utils import find_deepstream

Path = Union[str, os.PathLike]
ElemConfig = Mapping[str, Any]

logger = logging.getLogger(__name__)

def calc_rows_and_columns(num_sources: int) -> int:
    """
    Calculate rows and columns values from a number of sources.

    Returns:
        (int) math.ceil(math.sqrt(num_sources))
    """
    if not num_sources:
        return 1
    return int(ceil(sqrt(num_sources)))


def calc_tile_resolution(out_res: Tuple[int, int], rows_and_columns: int) -> Tuple[int, int]:
    """
    Return the optimal resolution for the stream muxer to scale input sources to.
    (same as the resolution for a tile).
    """
    return out_res[0] // rows_and_columns, out_res[1] // rows_and_columns


class GstConfig(object):
    """
    GstConfig is a simple class to wrap a ConfigEngine and provide
     for a GstEngine.

    Arguments:
        master_config:
            The master :obj:`ConfigEngine`_ to use internally.
    """

    SRC_TYPE = 'uridecodebin'
    MUXER_TYPE = 'concat'  # using this just because it has request pads
    INFER_TYPE = 'identity'
    DISTANCE_TYPE = 'identity'
    PAYLOAD_TYPE = 'identity'
    BROKER_TYPE = 'identity'
    OSD_CONVERTER_TYPE = 'identity'
    TILER_TYPE = 'identity'
    OSD_TYPE = 'identity'
    TRACKER_TYPE = 'identity'

    def __init__(self, master_config: ConfigEngine):
        self.master_config = master_config
        self.validate()

    @property
    def src_configs(self) -> List[ElemConfig]:
        """
        Returns:
            A list containing an ElemConfig for each 'Source' Section
            in self.master_config
        """
        ret = []
        for section, content in self.master_config.config.items():
            if section.startswith('Source') and 'VideoPath' in content:
                video_path = content['VideoPath']
                if os.path.isfile(video_path):
                    video_path = f'file://{os.path.abspath(video_path)}'
                ret.append({
                    'uri': video_path,
                })
        return ret

    @property
    def class_ids(self) -> str:
        """
        Returns:
            the class IDs from the master config.
        """
        return self.master_config.config['Detector']['ClassID']

    @property
    def infer_configs(self) -> List[ElemConfig]:
        """
        Default implementation.

        Returns:
            a list with a single empty :obj:`ElemConfig`
        """
        return [dict(),]

    def _blank_config(self) -> ElemConfig:
        """
        Default implementation.

        Returns:
            a new empty :obj:`ElemConfig`
        """
        return dict()

    muxer_config = property(_blank_config)
    tracker_config = property(_blank_config)
    tiler_config = property(_blank_config)
    osd_config = property(_blank_config)
    osd_converter_config = property(_blank_config)
    sink_config = property(_blank_config)
    distance_config = property(_blank_config)
    payload_config = property(_blank_config)
    broker_config = property(_blank_config)

    @property
    def rows_and_columns(self) -> int:
        """
        Number of rows and columns for the tiler element.

        Calculated based on the number of sources.
        """
        return calc_rows_and_columns(len(self.src_configs))

    @property
    def tile_resolution(self) -> Tuple[int, int]:
        """
        Resolution of an individual video tile.

        Calculated based on the resolution and number of sources.
        """
        return calc_tile_resolution(self.out_resolution, self.rows_and_columns)

    @property
    def out_resolution(self) -> Tuple[int, int]:
        """
        Output video resolution as a 2 tuple of width, height.

        Read from self.master_config.config['App']
        """
        return tuple(int(i) for i in self.master_config.config['App']['Resolution'].split(','))

    def validate(self):
        """
        Validate `self`. Called by __init__.

        Checks:
            * there is at least one source
            * there is at least one inference element

        Raises:
            ValueError: if `self` is invalid.
        
        Examples:

            If an empty source is supplied, ValueError is raised:

            >>> empty_iterable = tuple()
            >>> src_configs = [{'prop': 'val'},]
            >>> config = GstConfig(empty_iterable, src_configs)
            Traceback (most recent call last):
                ...
            ValueError: at least one inference config is required
        """
        if not self.infer_configs:
            raise ValueError(
                "at least one 'Detector' section is required in the .ini")
        if not self.src_configs:
            raise ValueError(
                "at least one 'Source' section is required in the .ini")


class DsConfig(GstConfig):
    """
    DeepStream implementation of GstConfig.

    'batch-size' will may be overridden on element configs to match
    the number of sources in the master config.

    Arguments:
        max_batch_size (int):
            The maximum allowed batch size parameter.
            Defaults to 32, but this should probably be
            lower on platforms like Jetson Nano for best
            performance.
    """
    SRC_TYPE = 'uridecodebin'
    MUXER_TYPE = 'nvstreammux'
    INFER_TYPE = 'nvinfer'
    DISTANCE_TYPE = 'dsdistance'
    PAYLOAD_TYPE = 'dsprotopayload'
    BROKER_TYPE = 'payloadbroker'
    OSD_CONVERTER_TYPE = 'nvvideoconvert'
    TILER_TYPE = 'nvmultistreamtiler'
    OSD_TYPE = 'nvdsosd'
    TRACKER_TYPE = 'nvtracker'

    DS_VER, DS_ROOT = find_deepstream()
    DS_CONF_PATH = os.path.join(DS_ROOT, 'samples', 'configs')
    # TODO(mdegans): secure hash validation of all configs, models, paths, etc and copy to immutable path
    # important that the copy is *before* the validation
    RESNET_CONF = os.path.join(DS_CONF_PATH, 'deepstream-app/config_infer_primary.txt')
    RESNET_CONF_NANO = os.path.join(DS_CONF_PATH, 'deepstream-app/config_infer_primary_nano.txt')
    PEOPLENET_CONF = os.path.join(DS_CONF_PATH, 'tlt_pretrained_models/config_infer_primary_peoplenet.txt')

    TRACKER_LIB = 'libnvds_mot_iou.so'
    INFER_INTERVAL = 1

    def __init__(self, *args, max_batch_size=32, **kwargs):
        self.max_batch_size = max_batch_size
        super().__init__(*args, **kwargs)

    @property
    def muxer_config(self) -> ElemConfig:
        return {
            'width': self.tile_resolution[0],
            'height': self.tile_resolution[1],
            'batch-size': self.batch_size,
            'enable-padding': True,  # maintain apsect raidou
            'live-source': True,
            'attach-sys-ts': True,
        }

    @property
    def tracker_config(self) -> ElemConfig:
        return {
            'll-lib-file': os.path.join(self.DS_ROOT, 'lib', self.TRACKER_LIB),
            'enable-batch-process': True,
        }

    @property
    def tiler_config(self) -> ElemConfig:
        return {
            'rows': self.rows_and_columns,
            'columns': self.rows_and_columns,
            'width': self.out_resolution[0],
            'height': self.out_resolution[1],
        }

    @property
    def infer_configs(self) -> List[ElemConfig]:
        """
        Return nvinfer configs.
        """
        infer_configs = []
        # TODO(mdegans): support 'Clasifier' section as secondary detectors
        # this might mean parsing and writing the config files since the
        # unique id is specified in the config.
        detector_cfg = self.master_config.config['Detector']
        model_name = detector_cfg['Name']
        if model_name == 'resnet10':
            # TODO(detect nano and use optimized cfg)
            detector = {
                'config-file-path': self.RESNET_CONF,
            }
        elif model_name == 'peoplenet':
            detector = {
                'config-file-path': self.PEOPLENET_CONF,
            }
        else:
            raise ValueError('Invalid value for Detector "Name"')
        detector['batch-size'] = self.batch_size
        detector['interval'] = self.INFER_INTERVAL
        infer_configs.append(detector)
        return infer_configs

    @property
    def batch_size(self) -> int:
        """
        Return the optimal batch size.
        (next power of two up from the number of sources).

        TODO(mdegans): it's unclear if this is actually optimal
          and under what circumstances (depends on model, afaik)
          tests must be run to see if it's better to use the number
          of sources directly.

        NOTE(mdegans): Nvidia sets it to a static 30 in their config
          so it may be a power of two is not optimal here. Some of
          their test apps use the number of sources. Benchmarking
          is probably the easiest way to settle this.

        Control the max by setting max_batch_size.
        """
        optimal = pow(2, ceil(log(len(self.src_configs))/log(2)))
        return min(optimal, self.max_batch_size)

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
