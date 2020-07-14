from multiprocessing import Process
from queue import Queue
from multiprocessing.managers import BaseManager
import logging

from libs.distancing import Distancing as CvEngine

logger = logging.getLogger(__name__)

class QueueManager(BaseManager): pass

class ProcessorCore:

    def __init__(self, config):
        self.config = config 
        self._cmd_queue = Queue()
        self._result_queue = Queue()
        self._setup_queues()
        self._engine = CvEngine(self.config)
        self._serve_thread = Process(target = self._serve)
        self._tasks = {}
       

    def _setup_queues(self):
        QueueManager.register('get_cmd_queue', callable=lambda: self._cmd_queue)
        QueueManager.register('get_result_queue', callable=lambda: self._result_queue)
        self._host = self.config.get_section_dict("CORE")["Host"]
        self._queue_port = int(self.config.get_section_dict("CORE")["QueuePort"])
        auth_key = self.config.get_section_dict("CORE")["QueueAuthKey"]
        self._queue_manager = QueueManager(address=(self._host, self._queue_port), authkey=auth_key.encode('ascii'))
        self._queue_manager.start()

       
    def start(self):
        logging.info("Starting processor core")
        self._serve_thread.start()
        self._serve_thread.join()
        logging.info("processor core has been terminated.")
        

    def _serve(self):
        while True:
            cmd_text = self._cmd_queue.get()
            logger.info("command received: " + cmd_text)
            if cmd_text == "restart_engine":
                # Do everything necessary ... 
                self._engine.stop_process_video()
                for task in self._tasks: 
                    task.terminate()
                self._engine = CvEngine(self.config)
                logger.info("engine restarted")
                self._result_queue.put(True)

            elif cmd_text == "process_video_cfg":
                self._tasks["process_video_cfg"] = Process(target = self._engine.process_video, \
                                                    args=(config.get_section_dict("App").get("VideoPath"),) )
                self._tasks["process_video_cfg"].start()
                logger.info("started to process video ... ")
                self._result_queue.put(True)

            elif cmd_text == "stop_processing" :
                self._engine.stop_process_video()
                logger.info("engine stopped")
                self._result_queue.put(True)

            else:
                logger.warning("Invalid core command " + cmd_text)
                self._result_queue.put("invalid_cmd")



