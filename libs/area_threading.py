import os
import logging

import time

from datetime import datetime
from threading import Thread
from libs.area_engine import AreaEngine

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
        try:
            self.engine = AreaEngine(self.config, self.area)
            restarts = 0
            max_restarts = int(self.config.get_section_dict("App")["MaxThreadRestarts"])
            if not self.config.get_boolean("App", "ProcessAreas"):
                # Ignore the area processing
                return
            while True:
                try:
                    last_restart_time = datetime.now()
                    self.engine.process_area()
                except Exception as e:
                    logging.error(e, exc_info=True)
                    logging.info(f"Exception processing area {self.area.name}")
                    if (datetime.now() - last_restart_time).total_seconds() > 60:
                        # If the last restart was previous than 1 minute ago, restart the counter.
                        restarts = 0
                    if restarts == max_restarts:
                        raise e
                    # Sleep the thread for 5 seconds and try to process the area again
                    time.sleep(5)
                    logging.info("Restarting the area processing")
                    restarts += 1
        except Exception as e:
            logging.error(e, exc_info=True)
            raise e

    def stop(self):
        self.engine.stop_process_area()
        self.join()
