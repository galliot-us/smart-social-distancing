import uvicorn
import os
import logging

from fastapi import FastAPI, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from share.commands import Commands
from typing import Optional

from .cameras import cameras_api, map_camera, map_to_camera_file_format
from .areas import areas_api, map_area, map_to_area_file_format
from .models.config_keys import ConfigDTO
from .queue_manager import QueueManager
from .reports import reports_api
from .settings import Settings
from .utils import (
    extract_config, handle_config_response, update_and_restart_config
)

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

        class SlackConfig(BaseModel):
            user_token: str
            channel: Optional[str]

            class Config:
                schema_extra = {
                    'example': {
                        'user_token': 'xxxx-ffff...'
                    }
                }

        # Create and return a fastapi instance
        app = FastAPI()

        app.mount("/reports", reports_api)
        app.mount("/cameras", cameras_api)
        app.mount("/areas", areas_api)

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

        def map_to_config_file_format(config_dto):
            config_dict = dict()
            for count, camera in enumerate(config_dto.cameras):
                config_dict["Source_" + str(count)] = map_to_camera_file_format(camera)
            for count, area in enumerate(config_dto.areas):
                config_dict["Area_" + str(count)] = map_to_area_file_format(area)
            return config_dict

        def map_config(config, options):
            cameras_name = [x for x in config.keys() if x.startswith("Source")]
            areas_name = [x for x in config.keys() if x.startswith("Area")]
            return {
                "host": config.get("API").get("Host"),
                "port": config.get("API").get("Port"),
                "cameras": [map_camera(x, config, options) for x in cameras_name],
                "areas": [map_area(x, config) for x in areas_name]
            }

        def write_user_token(token):
            logger.info("Writing user access token")
            with open("slack_token.txt", "w+") as slack_token:
                slack_token.write(token)

        def enable_slack(token_config):
            write_user_token(token_config.user_token)
            logger.info("Enabling slack notification on processor's config")
            config_dict = dict()
            config_dict["App"] = dict({"EnableSlackNotifications": "yes", "SlackChannel": token_config.channel})
            success = update_and_restart_config(config_dict)

            return handle_config_response(config_dict, success)

        def is_slack_configured():
            if not os.path.exists('slack_token.txt'):
                return False
            with open("slack_token.txt", "r") as user_token:
                value = user_token.read()
                if value:
                    return True
                return False

        def add_slack_channel_to_config(channel):
            logger.info("Adding slack's channel on processor's config")
            config_dict = dict()
            config_dict["App"] = dict({"SlackChannel": channel})

            success = update_and_restart_config(config_dict)
            return handle_config_response(config_dict, success)

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

        @app.get("/config", response_model=ConfigDTO)
        async def get_config(options: Optional[str] = ""):
            logger.info("get-config requests on api")
            return map_config(extract_config(), options)

        @app.put("/config")
        async def update_config(config: ConfigDTO):
            config_dict = map_to_config_file_format(config)

            success = update_and_restart_config(config_dict)
            return handle_config_response(config_dict, success)

        @app.get("/slack/is-enabled")
        def is_slack_enabled():
            return {
                "enabled": is_slack_configured()
            }

        @app.delete("/slack/revoke")
        def revoke_slack():
            write_user_token("")

        @app.post("/slack/add-channel")
        def add_slack_channel(channel: str):
            add_slack_channel_to_config(channel)

        @app.post("/slack/enable")
        def enable(body: SlackConfig):
            enable_slack(body)

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
