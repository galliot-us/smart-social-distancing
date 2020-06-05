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
DsDetector lives here
"""

import logging
import itertools
import time

from libs.config_engine import ConfigEngine
from libs.detectors.deepstream import  (
    BaseDetector,
    DsConfig,
    DsEngine,
    OnFrameCallback,
)

from libs.distance_pb2 import (
    Batch,
    Frame,
)

from typing import (
    Dict,
    Tuple,
    Sequence,
)

__all__ = ['DsDetector']

class DsDetector(BaseDetector):
    """
    DeepStream implementation of BaseDetector.
    """

    DEFAULT_MODEL_FILE = 'None'
    DEFAULT_MODEL_URL = 'None'

    engine = None  # type: DsEngine

    def load_model(self):
        """
        init/reinit a DsEngine instance (terminates if necessary).

        Called by start() automatically.
        """
        if self.engine and self.engine.is_alive():
            self.logger.info(
                "restarting engine")
            self.engine.terminate()
            self.engine.join()
        self.engine = DsEngine(DsConfig(self.config))

    # @Hossein I know the other classes don't have this, but it may make sense
    #  to add this start + stop functionality to the base class.
    def start(self, blocking=True, timeout=10):
        """
        Start DsDetector's engine.

        Arguments:
            blocking (bool):
                Whether to block this thread while waiting for results. If
                false, busy waits with a sleep(0) in the loop.
                (set False if you want this to spin)
            timeout:
                If blocking is True,  
        """
        self.logger.info(
            f'starting up{" in blocking mode" if blocking else ""}')
        self.engine.blocking=blocking
        self.engine.start()
        self.engine.queue_timeout=10
        batch = Batch()
        while self.engine.is_alive():
            batch_str = self.engine.results
            if not batch_str:
                time.sleep(0)  # this is to switch context if launched in thread
                continue
            batch.ParseFromString(batch_str)
            for frame in batch.frames:  # pylint: disable=no-member
                next(self._frame_count)
                self.on_frame(frame)

    def stop(self):
        self.engine.stop()

    @property
    def fps(self):
        self.logger.warning("fps reporting not yet implemented")
        return 30

    @property
    def sources(self):
        self.logger.warning("getting sources at runtime not yet implemented")
        return []

    @sources.setter
    def sources(self, sources: Sequence[str]):
        self.logger.warning("setting sources at runtime not yet implemented")

if __name__ == "__main__":
    import doctest
    doctest.testmod()
