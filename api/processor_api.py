import uvicorn
import os
import logging

from fastapi import FastAPI, status, Request

from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from share.commands import Commands

from .cameras import cameras_router
from .config import config_router
from .areas import areas_router
from .queue_manager import QueueManager
from .reports import reports_router
from .settings import Settings
from .slack import slack_router

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
        os.environ["LogDirectory"] = self.settings.config.get_section_dict("Logger")["LogDirectory"]
        os.environ["HeatmapResolution"] = self.settings.config.get_section_dict("Logger")["HeatmapResolution"]

        # Create and return a fastapi instance
        app = FastAPI()

        app.include_router(config_router, prefix="/config", tags=["config"])
        app.include_router(cameras_router, prefix="/cameras", tags=["cameras"])
        app.include_router(areas_router, prefix="/areas", tags=["areas"])
        app.include_router(reports_router, prefix="/reports", tags=["reports"])
        app.include_router(slack_router, prefix="/slack", tags=["slack"])

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
            )

        if os.environ.get("DEV_ALLOW_ALL_ORIGINS", False):
            # This option allows React development server (which is served on another port, like 3000) to proxy requests
            # to this server.
            # WARNING: read this before enabling it in your environment:
            # https://medium.com/@stestagg/stealing-secrets-from-developers-using-websockets-254f98d577a0
            from fastapi.middleware.cors import CORSMiddleware
            app.add_middleware(CORSMiddleware, allow_origins="*", allow_credentials=True, allow_methods=["*"],
                               allow_headers=["*"])

        app.mount("/static", StaticFiles(directory="/repo/data/processor/static"), name="static")

        @app.put("/start-process-video", response_model=bool)
        async def process_video_cfg():
            """
            Starts the video processing
            """
            logger.info("process-video-cfg requests on api")
            self.queue_manager.cmd_queue.put(Commands.PROCESS_VIDEO_CFG)
            logger.info("waiting for core's response...")
            result = self.queue_manager.result_queue.get()
            return result

        @app.put("/stop-process-video", response_model=bool)
        async def stop_process_video():
            """
            Stops the video processing
            """
            logger.info("stop-process-video requests on api")
            self.queue_manager.cmd_queue.put(Commands.STOP_PROCESS_VIDEO)
            logger.info("waiting for core's response...")
            result = self.queue_manager.result_queue.get()
            return result

        def custom_openapi():
            openapi_schema = get_openapi(
                title="Smart Social Distancing",
                version="1.0.0",
                description="Processor API schema",
                routes=app.routes
            )
            for value_path in openapi_schema["paths"].values():
                for value in value_path.values():
                    # Remove current 422 error message.
                    # TODO: Display the correct validation error schema
                    value["responses"].pop("422", None)

            app.openapi_schema = openapi_schema
            return app.openapi_schema

        app.openapi = custom_openapi

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
