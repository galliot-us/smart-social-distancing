import uvicorn
import os
import logging

from fastapi import FastAPI, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from share.commands import Commands

from .cameras import cameras_api
from .config import config_api
from .areas import areas_api
from .queue_manager import QueueManager
from .reports import reports_api
from .settings import Settings
from .slack import slack_api

logger = logging.getLogger(__name__)


class ProcessorAPI:
    """
    The ProcessorAPI object implements a fastapi application that should allow configuring, starting and stopping processing,
    and viewing the video stream processed by this processor node.

    :param config: Is a ConfigEngine instance which provides necessary parameters.
    :param engine_instance:  A ConfigEngine object which store all of the config parameters. Access to any parameter
        is possible by calling get_section_dict method.
    """

    def __init__(self):
        self.settings = Settings()
        self.queue_manager = QueueManager(config=self.settings.config)
        self._host = self.settings.config.get_section_dict("API")["Host"]
        self._port = int(self.settings.config.get_section_dict("API")["Port"])
        self._screenshot_directory = self.settings.config.get_section_dict("App")["ScreenshotsDirectory"]
        self.app = self.create_fastapi_app()

    def create_fastapi_app(self):
        os.environ['LogDirectory'] = self.settings.config.get_section_dict("Logger")["LogDirectory"]
        os.environ['HeatmapResolution'] = self.settings.config.get_section_dict("Logger")["HeatmapResolution"]

        # Create and return a fastapi instance
        app = FastAPI()

        app.mount("/config", config_api)
        app.mount("/reports", reports_api)
        app.mount("/cameras", cameras_api)
        app.mount("/areas", areas_api)
        app.mount("/slack", slack_api)

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
            self.queue_manager.cmd_queue.put(Commands.PROCESS_VIDEO_CFG)
            logger.info("waiting for core's response...")
            result = self.queue_manager.result_queue.get()
            return result

        @app.get("/stop-process-video")
        async def stop_process_video():
            logger.info("stop-process-video requests on api")
            self.queue_manager.cmd_queue.put(Commands.STOP_PROCESS_VIDEO)
            logger.info("waiting for core's response...")
            result = self.queue_manager.result_queue.get()
            return result

        return app

    def start(self):
        kwargs = {
            "host": self._host,
            "port": self._port,
            "log_level": "info",
            "access_log": False,
        }
        if self.settings.config.get_boolean("API", "SSLEnabled"):
            # HTTPs is enabled
            kwargs.update({
                "ssl_keyfile": f"{self.settings.config.get_section_dict('API')['SSLKeyFile']}",
                "ssl_certfile": f"{self.settings.config.get_section_dict('API')['SSLCertificateFile']}"
            })
        uvicorn.run(self.app, **kwargs)
