import time
from threading import Thread
from queue import Queue
from multiprocessing.managers import BaseManager
from fastapi import FastAPI, HTTPException, Header, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import uvicorn
import os
import logging
import humps

from typing import Dict
from pydantic import BaseModel
from typing import Optional
from api.models.config_keys import *
from share.commands import Commands

logger = logging.getLogger(__name__)

class QueueManager(BaseManager): pass

class ProcessorAPI:
    """
    The ProcessorAPI object implements a fastapi application that should allow configuring, starting and stopping processing,
    and viewing the video stream processed by this processor node.

    :param config: Is a ConfigEngine instance which provides necessary parameters.
    :param engine_instance:  A ConfigEngine object which store all of the config parameters. Access to any parameter
        is possible by calling get_section_dict method.
    """

    def __init__(self, config):
        self.config = config
        self._setup_queues()
        self._host = self.config.get_section_dict("API")["Host"]
        self._port = int(self.config.get_section_dict("API")["Port"])
        self.app = self.create_fastapi_app()

    def _setup_queues(self):
        QueueManager.register('get_cmd_queue')
        QueueManager.register('get_result_queue')
        self._queue_host = self.config.get_section_dict("CORE")["Host"]
        self._queue_port = int(self.config.get_section_dict("CORE")["QueuePort"])
        auth_key = self.config.get_section_dict("CORE")["QueueAuthKey"]
        self._queue_manager = QueueManager(address=(self._queue_host, self._queue_port), authkey=auth_key.encode('ascii'))
        
        while True:
            try:
                self._queue_manager.connect()
                break
            except ConnectionRefusedError:
                logger.warning("Waiting for core's queue to initiate ... ")
                time.sleep(1)

        logger.info("Connection established to Core's queue")
        self._cmd_queue = self._queue_manager.get_cmd_queue()
        self._result_queue = self._queue_manager.get_result_queue()

    def create_fastapi_app(self):
        # Create and return a fastapi instance
        app = FastAPI()

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
            )

        if os.environ.get('DEV_ALLOW_ALL_ORIGINS', False):
            # This option allows React development server (which is served on another port, like 3000) to proxy requests
            # to this server.
            # WARNING: read this before enabling it in your environment:
            # https://medium.com/@stestagg/stealing-secrets-from-developers-using-websockets-254f98d577a0
            from fastapi.middleware.cors import CORSMiddleware
            app.add_middleware(CORSMiddleware, allow_origins='*', allow_credentials=True, allow_methods=['*'],
                               allow_headers=['*'])

        app.mount("/static", StaticFiles(directory="/repo/data/processor/static"), name="static")

        @app.get("/process-video-cfg")
        async def process_video_cfg():
            logger.info("process-video-cfg requests on api")
            self._cmd_queue.put(Commands.PROCESS_VIDEO_CFG)
            logger.info("waiting for core's response...")
            result = self._result_queue.get()
            return result
        
        @app.get("/stop-process-video")
        async def stop_process_video():
            logger.info("stop-process-video requests on api")
            self._cmd_queue.put(Commands.STOP_PROCESS_VIDEO)
            logger.info("waiting for core's response...")
            result = self._result_queue.get()
            return result
        
        @app.get("/get-config")
        async def get_config():
            logger.info("get-config requests on api")
            sections = self.config.get_sections()
            result = {}
            for section in sections:
                result[section] = self.config.get_section_dict(section)
            return humps.decamelize(result)

        @app.put("/config")
        async def update_config(config: Config):
            config = config.dict(exclude_unset=True, exclude_none=True)
            print(config)

            logger.info("Updating config...")
            self.config.update_config(config)
            self.config.reload()
            
            # TODO: Restart only when necessary
            logger.info("Restarting video processor...")
            self._cmd_queue.put(Commands.STOP_PROCESS_VIDEO)
            stopped = self._result_queue.get()
            if stopped:
                self._cmd_queue.put(Commands.PROCESS_VIDEO_CFG)
                started = self._result_queue.get()
                if not started:
                    # TODO: Raise an error?
                    logger.info("Failed to restart video processor...")
                    pass
            return JSONResponse(content=humps.decamelize(config))

        return app

    def start(self):
        uvicorn.run(self.app, host=self._host, port=self._port, log_level='info', access_log=False)
