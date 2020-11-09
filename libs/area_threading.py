import os
from threading import Thread
from libs.area_reporting import AreaReporting as AreaEngine
import logging

logger = logging.getLogger(__name__)


def run_area_processing(config, pipe, areas):
    pid = os.getpid()
    logger.info(f"[{pid}] taking on notifications for {len(areas)} areas")
    threads = []
    for area in areas:
        engine = AreaThread(config, area)
        engine.start()
        threads.append(engine)

    # Wait for a signal to die
    pipe.recv()
    logger.info(f"[{pid}] will stop area alerts and die")
    for t in threads:
        t.stop()

    logger.info(f"[{pid}] Goodbye!")


class AreaThread(Thread):
    def __init__(self, config, area):
        Thread.__init__(self)
        self.engine = None
        self.config = config
        self.area = area

    def run(self):
        self.engine = AreaEngine(self.config, self.area)
        self.engine.process_area()

    def stop(self):
        self.engine.stop_process_area()
        self.join()
