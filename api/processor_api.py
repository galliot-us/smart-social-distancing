import uvicorn
import os
import logging

from fastapi import Depends, FastAPI, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from share.commands import Commands

from libs.utils.loggers import get_area_log_directory, get_source_log_directory, get_screenshots_directory, \
    get_config_source_directory, get_config_areas_directory
from api.utils import bad_request_serializer

from .dependencies import validate_token
from .queue_manager import QueueManager
from .routers.app import app_router, dashboard_sync_router
from .routers.api import api_router
from .routers.areas import areas_router
from .routers.area_loggers import area_loggers_router
from .routers.auth import auth_router
from .routers.core import core_router
from .routers.cameras import cameras_router
from .routers.classifier import classifier_router
from .routers.config import config_router
from .routers.detector import detector_router
from .routers.export import export_router
from .routers.metrics import area_metrics_router, camera_metrics_router
from .routers.periodic_tasks import periodic_tasks_router
from .routers.slack import slack_router
from .routers.source_loggers import source_loggers_router
from .routers.source_post_processors import source_post_processors_router
from .routers.static import static_router
from .routers.tracker import tracker_router
from .routers.ml_models import ml_model_router
from .settings import Settings

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)


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
        self.app = self.create_fastapi_app()

    def create_fastapi_app(self):
        os.environ["SourceLogDirectory"] = get_source_log_directory(self.settings.config)
        os.environ["SourceConfigDirectory"] = get_config_source_directory(self.settings.config)
        os.environ["AreaLogDirectory"] = get_area_log_directory(self.settings.config)
        os.environ["AreaConfigDirectory"] = get_config_areas_directory(self.settings.config)
        os.environ["ScreenshotsDirectory"] = get_screenshots_directory(self.settings.config)

        os.environ["HeatmapResolution"] = self.settings.config.get_section_dict("App")["HeatmapResolution"]
        os.environ["Resolution"] = self.settings.config.get_section_dict("App")["Resolution"]

        # Create and return a fastapi instance
        app = FastAPI()
        dependencies = []
        if self.settings.config.get_boolean("API", "UseAuthToken"):
            dependencies = [Depends(validate_token)]

        app.include_router(config_router, prefix="/config", tags=["Config"], dependencies=dependencies)
        app.include_router(cameras_router, prefix="/cameras", tags=["Cameras"], dependencies=dependencies)
        app.include_router(areas_router, prefix="/areas", tags=["Areas"], dependencies=dependencies)
        app.include_router(app_router, prefix="/app", tags=["App"], dependencies=dependencies)
        app.include_router(dashboard_sync_router, prefix="/app", tags=["App"])
        app.include_router(api_router, prefix="/api", tags=["Api"], dependencies=dependencies)
        app.include_router(core_router, prefix="/core", tags=["Core"], dependencies=dependencies)
        app.include_router(detector_router, prefix="/detector", tags=["Detector"], dependencies=dependencies)
        app.include_router(classifier_router, prefix="/classifier", tags=["Classifier"], dependencies=dependencies)
        app.include_router(tracker_router, prefix="/tracker", tags=["Tracker"], dependencies=dependencies)
        app.include_router(source_post_processors_router, prefix="/source_post_processors",
                           tags=["Source Post Processors"], dependencies=dependencies)
        app.include_router(source_loggers_router, prefix="/source_loggers", tags=["Source Loggers"], dependencies=dependencies)
        app.include_router(area_loggers_router, prefix="/area_loggers", tags=["Area Loggers"], dependencies=dependencies)
        app.include_router(periodic_tasks_router, prefix="/periodic_tasks", tags=["Periodic Tasks"], dependencies=dependencies)
        app.include_router(area_metrics_router, prefix="/metrics/areas", tags=["Metrics"], dependencies=dependencies)
        app.include_router(camera_metrics_router, prefix="/metrics/cameras", tags=["Metrics"], dependencies=dependencies)
        app.include_router(export_router, prefix="/export", tags=["Export"], dependencies=dependencies)
        app.include_router(slack_router, prefix="/slack", tags=["Slack"], dependencies=dependencies)
        app.include_router(auth_router, prefix="/auth", tags=["Auth"])
        app.include_router(static_router, prefix="/static", dependencies=dependencies)
        app.include_router(ml_model_router, prefix="/ml_model", tags=["ML Models"], dependencies=dependencies)

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
