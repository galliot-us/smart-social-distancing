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
The DeepStream detector module includes a DeepStream specific implementation
of the BaseDetector class and various utility classes and functions.
"""

# GStreamer needs to be imported before pyds or else there is crash on Gst.init
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
from gi.repository import (
    Gst,
    GLib,
)
from libs.detectors.deepstream._base_detector import *
from libs.detectors.deepstream._ds_utils import *
from libs.detectors.deepstream._pyds import *
from libs.detectors.deepstream._ds_config import *
from libs.detectors.deepstream._gst_engine import *
from libs.detectors.deepstream._ds_engine import *
from libs.detectors.deepstream._detectors import *

__all__ = [
    'BaseDetector',  # _base_detector.py
    'bin_to_pdf',  # _ds_utils.py
    'DsConfig',  # _ds_config.py
    'DsDetector',  # _detectors.py
    'DsEngine',  # _ds_engine.py
    'ElemConfig',  # _ds_config.py
    'find_deepstream',  # _ds_utils.py
    'frame_meta_iterator',  # _ds_engine.py
    'GstConfig',  # _ds_config.py
    'GstEngine',  # _ds_engine.py
    'link_many',  # _ds_engine.py
    'obj_meta_iterator',  # _ds_engine.py
    'OnFrameCallback',  # _base_detector.py
    'PYDS_INSTRUCTIONS',  # _pyds.py
    'PYDS_PATH',  # _pyds.py
    'pyds',  # _pyds.py
]
