import multiprocessing as mp
from queue import Queue
from multiprocessing.managers import BaseManager
import logging
from share.commands import Commands
from queue import Empty
import schedule
from libs.engine_threading import run_video_processing

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)

class QueueManager(BaseManager):
    pass


class ProcessorCore:

    def __init__(self, config):
        self.config = config
        self._cmd_queue = Queue()
        self._result_queue = Queue()
        self._setup_queues()
        self._tasks = {}
        self._engines = []

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
        logger.info("Core is listening for commands ... ")
        while True:
            try:
                cmd_code = self._cmd_queue.get(timeout=10)
                logger.info("command received: " + str(cmd_code))
                self._handle_command(cmd_code)
            except Empty:
                # Run pending tasks
                schedule.run_pending()

    def _handle_command(self, cmd_code):
        if cmd_code == Commands.PROCESS_VIDEO_CFG:
            if Commands.PROCESS_VIDEO_CFG in self._tasks.keys():
                logger.warning("Already processing a video! ...")
                self._result_queue.put(False)
                return

            self.config.reload()
            self._tasks[Commands.PROCESS_VIDEO_CFG] = True

            self._start_processing()

            logger.info("started to process video ... ")
            self._result_queue.put(True)
        elif cmd_code == Commands.STOP_PROCESS_VIDEO:
            if Commands.PROCESS_VIDEO_CFG in self._tasks.keys():
                self._stop_processing()
                logger.info("Stop scheduled tasks")
                schedule.clear('notification-task')

                del self._tasks[Commands.PROCESS_VIDEO_CFG]
                logger.info("processing stopped")
                self._result_queue.put(True)
            else:
                logger.warning("no video is being processed")
                self._result_queue.put(False)
        else:
            logger.warning("Invalid core command " + str(cmd_code))
            self._result_queue.put("invalid_cmd_code")

    def start_processing_sources(self):
        sources = self.config.get_video_sources()
        if len(sources) == 0:
            return []
        processes = max(1, int(self.config.get_section_dict("App")["MaxProcesses"]))
        if len(sources) < processes:
            processes = len(sources)
        tasks_per_process = len(sources) // processes
        processes_with_additional_task = len(sources) % processes

        index = 0
        engines = []
        for p_index in range(processes):
            extra = 1 if p_index < processes_with_additional_task else 0
            p_src = sources[index:(index + tasks_per_process + extra)]
            index += tasks_per_process + extra
            recv_conn, send_conn = mp.Pipe(False)
            p = mp.Process(target=run_video_processing, args=(self.config, recv_conn, p_src))
            p.start()
            engines.append((send_conn, p))
        return engines

    def _start_processing(self):
        self._engines = self.start_processing_sources()

    def _stop_processing(self):
        for (conn, proc) in self._engines:
            conn.send(True)
            # Terminate the process by waiting at most 2 seconds until we force terminate it.
            proc.join(2)
            if proc.exitcode is None:
                proc.terminate()
            del proc
        self._engines = []
