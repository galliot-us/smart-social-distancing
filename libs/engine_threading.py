import os
from shutil import rmtree
from threading import Thread
from libs.distancing import Distancing as CvEngine
import logging

logger = logging.getLogger(__name__)


def run_video_processing(config, pipe, sources):
    pid = os.getpid()
    logger.info(f"[{pid}] taking on {len(sources)} cameras")
    threads = []
    for src in sources:
        engine = EngineThread(config, src, len(sources) == 1)
        engine.start()
        threads.append(engine)

    # Wait for a signal to die
    pipe.recv()
    logger.info(f"[{pid}] will stop cameras and die")
    for t in threads:
        t.stop()

    for src in sources:
        logger.info("Clean up video output")
        playlist_path = os.path.join('/repo/data/processor/static/gstreamer/', src['id'])
        birdseye_path = os.path.join('/repo/data/processor/static/gstreamer/', src['id'] + '-birdseye')
        if os.path.exists(playlist_path):
            rmtree(playlist_path)
        if os.path.exists(birdseye_path):
            rmtree(birdseye_path)
    logger.info(f"[{pid}] Goodbye!")


class EngineThread(Thread):
    def __init__(self, config, source, live_feed_enabled=True):
        Thread.__init__(self)
        self.engine = None
        self.config = config
        self.source = source
        self.live_feed_enabled = live_feed_enabled

    def run(self):
        self.engine = CvEngine(self.config, self.source['section'], self.source['loop_video_file'], self.live_feed_enabled)
        self.engine.process_video(self.source['url'])

    def stop(self):
        self.engine.stop_process_video()
        self.join()
