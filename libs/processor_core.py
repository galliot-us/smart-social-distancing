from threading import Thread
from queue import Queue
from multiprocessing.managers import BaseManager
import logging
from share.commands import Commands
from libs.distancing import Distancing as CvEngine

logger = logging.getLogger(__name__)

class QueueManager(BaseManager): pass

class EngineThread(Thread):
    def __init__(self, config):
        Thread.__init__(self)
        self.engine = None
        self.config = config

    def run(self):
        self.engine = CvEngine(self.config)
        self.engine.process_video(self.config.get_section_dict("App").get("VideoPath"))
    
    def stop(self):
        self.engine.stop_process_video()
        self.join()


class ProcessorCore:

    def __init__(self, config):
        self.config = config 
        self._cmd_queue = Queue()
        self._result_queue = Queue()
        self._setup_queues()
        self._tasks = {}
        self._engine = None

    def _setup_queues(self):
        QueueManager.register('get_cmd_queue', callable=lambda: self._cmd_queue)
        QueueManager.register('get_result_queue', callable=lambda: self._result_queue)
        self._host = self.config.get_section_dict("CORE")["Host"]
        self._queue_port = int(self.config.get_section_dict("CORE")["QueuePort"])
        auth_key = self.config.get_section_dict("CORE")["QueueAuthKey"]
        self._queue_manager = QueueManager(address=(self._host, self._queue_port), authkey=auth_key.encode('ascii'))
        self._queue_manager.start()
        self._cmd_queue = self._queue_manager.get_cmd_queue()
        self._result_queue = self._queue_manager.get_result_queue()
        logger.info("Core's queue has been initiated")

       
    def start(self):
        logging.info("Starting processor core")
        self._serve()
        logging.info("processor core has been terminated.")
       

    def _serve(self):
        while True:
            logger.info("Core is listening for commands ... ")
            cmd_code = self._cmd_queue.get()
            logger.info("command received: " + str(cmd_code))
            
            if cmd_code == Commands.PROCESS_VIDEO_CFG:
                if Commands.PROCESS_VIDEO_CFG in self._tasks.keys():
                    logger.warning("Already processing a video! ...")
                    self._result_queue.put(False)
                    continue

                self._tasks[Commands.PROCESS_VIDEO_CFG] = True
                self._engine = EngineThread(self.config)
                self._engine.start()

                logger.info("started to process video ... ")
                self._result_queue.put(True)
                continue
            
            elif cmd_code == Commands.STOP_PROCESS_VIDEO :
                if Commands.PROCESS_VIDEO_CFG in self._tasks.keys():
                    self._engine.stop()
                    del self._tasks[Commands.PROCESS_VIDEO_CFG]
                    logger.info("processing stopped")
                    self._result_queue.put(True)
                    del self._engine
                else:
                    logger.warning("no video is being processed")
                    self._result_queue.put(False)

                continue

            else:
                logger.warning("Invalid core command " + str(cmd_code))
                self._result_queue.put("invalid_cmd_code")
                continue


