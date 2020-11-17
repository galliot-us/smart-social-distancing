import logging
import time

from multiprocessing.managers import BaseManager

logger = logging.getLogger(__name__)


class QueueManager:
    instance = None

    class __QueueManager(BaseManager):

        @property
        def cmd_queue(self):
            return self.get_cmd_queue()

        @property
        def result_queue(self):
            return self.get_result_queue()

    def __init__(self, config=None):
        if not QueueManager.instance:
            QueueManager.__QueueManager.register("get_cmd_queue")
            QueueManager.__QueueManager.register("get_result_queue")
            queue_host = config.get_section_dict("CORE")["Host"]
            queue_port = int(config.get_section_dict("CORE")["QueuePort"])
            auth_key = config.get_section_dict("CORE")["QueueAuthKey"]
            QueueManager.instance = QueueManager.__QueueManager(
                address=(queue_host, queue_port), authkey=auth_key.encode("ascii"))
            while True:
                try:
                    QueueManager.instance.connect()
                    break
                except ConnectionRefusedError:
                    logger.warning("Waiting for core's queue to initiate ... ")
                    time.sleep(1)
            logger.info("Connection established to Core's queue")

    def __getattr__(self, name):
        return getattr(self.instance, name)
