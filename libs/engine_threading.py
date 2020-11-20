import os
import logging
import time

from datetime import datetime
from shutil import rmtree
from threading import Thread
from libs.distancing import Distancing as CvEngine

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
        self.engine = CvEngine(self.config, self.source['section'], self.live_feed_enabled)
        restarts = 0
        max_restarts = int(self.config.get_section_dict("App")["MaxThreadRestarts"])
        while True:
            try:
                last_restart_time = datetime.now()
                self.engine.process_video(self.source['url'])
            except Exception as e:
                logging.error(e, exc_info=True)
                logging.info(f"Exception processing video for source {self.source['name']}")
                if (datetime.now() - last_restart_time).total_seconds() > 60:
                    # If the last restart was previous than 1 minute ago, restart the counter.
                    restarts = 0
                if restarts == max_restarts:
                    raise e
                # Sleep the thread for 5 seconds and try to process the video again
                time.sleep(5)
                logging.info("Restarting the video processing")
                restarts += 1

    def stop(self):
        self.engine.stop_process_video()
        self.join()
