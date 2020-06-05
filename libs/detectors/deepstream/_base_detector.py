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
Contains Detector, the base class for all detectors (in the deepstream branch, anyway).
"""

import abc
import logging
import os
import sys
import urllib.parse
import urllib.request
import itertools

from libs.distance_pb2 import (
    BBox,
    Frame,
    Person,
)
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
)

OnFrameCallback = Callable[[Frame], Any]
Callable.__doc__ = """
Signature an on-frame callback accepting a fra.
"""

__all__ = ['BaseDetector', 'OnFrameCallback']

class BaseDetector(abc.ABC):
    """
    A base class for all Detectors. The following should be overridden:

    PLATFORM the model platform (eg. edgetpu, jetson, x86)
    DEFAULT_MODEL_FILE with the desired model filename
    DEFAULT_MODEL_URL with the url path minus filename of the model

    load_model() to load the model. This is called for you on __init__.

    Something should also call on_frame() with a sequence of sd.Detection

    Arguments:
        config (:obj:`sd.core.ConfigEngine`):
            the global config class
        on_frame (:obj:`OnFrameCallback`):
            A callback to call on every frame. 
    """

    PLATFORM = None  # type: Tuple
    DEFAULT_MODEL_FILE = None  # type: str
    DEFAULT_MODEL_URL = None  # type: str

    # this works differently in the deepstream branch
    MODEL_DIR = '/repo/data'

    def __init__(self, config, on_frame:OnFrameCallback=None):
        # set the config
        self.config = config

        # assign the on_frame callback if any
        if on_frame is not None:
            self.on_frame = on_frame

        # set up a logger on the class
        self.logger = logging.getLogger(self.__class__.__name__)

        # download the model if necessary
        if not os.path.isfile(self.model_file):
            self.logger.info(
                f'model does not exist under: "{self.model_path}" '
                f'downloading from  "{self.model_url}"')
            os.makedirs(self.model_path, mode=0o755, exist_ok=True)
            urllib.request.urlretrieve(self.model_url, self.model_file)

        # add a frame counter
        self._frame_count = itertools.count()

        # load the model
        self.load_model()

    @property
    def detector_config(self) -> Dict:
        """:return: the 'Detector' section from self.config"""
        return self.config.get_section_dict('Detector')

    @property
    def name(self) -> str:
        """:return: the detector name."""
        return self.detector_config['Name']

    @property
    def model_path(self) -> Optional[str]:
        """:return: the folder containing the model."""
        try:
            cfg_model_path = self.detector_config['ModelPath']
            if cfg_model_path:  # not None and greater than zero in length
                return cfg_model_path
        except KeyError:
            pass
        return os.path.join(self.MODEL_DIR, self.PLATFORM)

    @property
    def model_file(self) -> Optional[str]:
        """:return: the model filename."""
        return os.path.join(self.model_path, self.DEFAULT_MODEL_FILE)

    @property
    def model_url(self) -> str:
        """:return: a parsed url pointing to a downloadable model"""
        # this is done to validate it's at least a valid uri
        # TODO(mdegans?): move to config class
        return urllib.parse.urlunparse(urllib.parse.urlparse(
            self.DEFAULT_MODEL_URL + self.DEFAULT_MODEL_FILE))

    @property
    def class_id(self) -> int:
        """:return: the class id to detect."""
        return int(self.detector_config['ClassID'])

    @property
    def score_threshold(self) -> float:
        """:return: the detection minimum threshold (MinScore)."""
        return float(self.detector_config['MinScore'])
    min_score = score_threshold   # an alias for ease of access

    @property
    @abc.abstractmethod
    def sources(self) -> List[str]:
        """:return: the active sources."""

    @sources.setter
    @abc.abstractmethod
    def sources(self, source: Sequence[str]):
        """Set the active sources"""

    @property
    @abc.abstractmethod
    def fps(self) -> int:
        """:return: the current fps"""

    @abc.abstractmethod
    def load_model(self):
        """load the model. Called by default implementation of __init__."""

    @abc.abstractmethod
    def start(self):
        """
        Start the detector (should do inferences and call on_frame).
        """
        pass

    @abc.abstractmethod
    def stop(self):
        """
        Start the detector (should do inferences and call on_frame).
        """
        pass

    def on_frame(self, frame: Frame):  # pylint: disable=method-hidden
        """
        Calculate distances between detections and updates UI.
        This default implementation just logs serialized frames to the DEBUG
        level and is called if on_frame is not specified on __init__.

        Arguments:
            frame (:obj:`Frame`): frame level deserialized protobuf metadata.
        """
        self.logger.debug({'frame_proto': frame.SerializeToString()})
        pass
