from threading import Thread
from queue import Queue
from multiprocessing.managers import BaseManager
import logging
from share.commands import Commands
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
        self._tasks = {}
       

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
            
            if cmd_code == Commands.RESTART:
                # Do everything necessary ... make sure all threads in tasks are stopped 
                if Commands.PROCESS_VIDEO_CFG in self._tasks.keys():
                    logger.warning("currently processing a video, stopping ...")
                    self._engine.stop_process_video()
                
                # TODO: Be sure you have done proper action before this so all threads are stopped
                self._tasks = {}
                self.config.reload()
                self._engine = CvEngine(self.config)
                logger.info("engine restarted")
                self._result_queue.put(True)
                continue
            
            elif cmd_code == Commands.PROCESS_VIDEO_CFG:
                if Commands.PROCESS_VIDEO_CFG in self._tasks.keys():
                    logger.warning("Already processing a video! ...")
                    self._result_queue.put(False)
                    continue

                self._tasks[Commands.PROCESS_VIDEO_CFG] = Thread(target = self._engine.process_video, \
                                                    args=(self.config.get_section_dict("App").get("VideoPath"),) )
                self._tasks[Commands.PROCESS_VIDEO_CFG].start()
                logger.info("started to process video ... ")
                self._result_queue.put(True)
                continue
            
            elif cmd_code == Commands.STOP_PROCESS_VIDEO :
                if Commands.PROCESS_VIDEO_CFG in self._tasks.keys():
                    self._engine.stop_process_video()
                    del self._tasks[Commands.PROCESS_VIDEO_CFG]
                    logger.info("processing stopped")
                    self._result_queue.put(True)
                else:
                    logger.warning("no video is being processed")
                    self._result_queue.put(False)

                continue

            else:
                logger.warning("Invalid core command " + str(cmd_code))
                self._result_queue.put("invalid_cmd_code")
                continue


