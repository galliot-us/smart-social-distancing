import threading
import time
import cv2 as cv
import numpy as np
from datetime import date
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
import uvicorn
import os

from libs import pubsub


class WebGUI:
    """
    The Webgui object implements a fastapi application and acts as an interface for users.
    Once it is created it will act as a central application for viewing outputs.

    :param config: Is a ConfigEngine instance which provides necessary parameters.
    :param engine_instance:  A ConfigEngine object which store all of the config parameters. Access to any parameter
        is possible by calling get_section_dict method.
    """

    def __init__(self, config, engine_instance):
        self.config = config
        self.__ENGINE_INSTANCE = engine_instance
        self._output_frame = None
        self._birds_view = None
        self._lock = threading.Lock()
        self._host = self.config.get_section_dict("App")["Host"]
        self._port = int(self.config.get_section_dict("App")["Port"])
        self.app = self.create_fastapi_app()
        self._displayed_items = {}  # all items here will be used at ui webpage
        self._public_url = self.config.get_section_dict("App")["PublicUrl"]


    def create_fastapi_app(self):
        # Create and return a fastapi instance
        app = FastAPI()

        if os.environ.get('DEV_ALLOW_ALL_ORIGINS', False):
            from fastapi.middleware.cors import CORSMiddleware
            app.add_middleware(CORSMiddleware, allow_origins='*', allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

        app.mount("/panel/static", StaticFiles(directory="/srv/frontend/static"), name="panel")
        app.mount("/static", StaticFiles(directory="/repo/data/web_gui/static"), name="static")

        @app.get("/panel/")
        async def panel():
            return FileResponse("/srv/frontend/index.html")

        @app.get("/")
        async def index():
            return RedirectResponse("/panel/")

        @app.get("/api/cameras/")
        async def api_cameras():
            return [{
                'id': 'default',
                'streams': [
                    {'src': 'http://qthttp.apple.com.edgesuite.net/1010qwoeiuryfg/sl.m3u8'},
                ],
            }]

        @app.get("/live_feed/{feed_name}")
        def live_feed(feed_name):
            # TODO hossein: check if feed_name is valid. Otherwise, many requests will loop on time.sleep(1)
            while True:
                receive = pubsub.init_subscriber(feed_name)
                if receive is None:
                    time.sleep(1)
                else:
                    break

            def generate_frames():
                while True:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + receive() + b"\r\n"
                    )

            return StreamingResponse(
                generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
            )

        return app


    def _run(self):
        # Get video file path from the config
        video_path = self.config.get_section_dict("App")["VideoPath"]
        self.__ENGINE_INSTANCE.process_video(video_path)

    def start(self):
        """
        Start the thread's activity.
        It must be called at most once. It runes self._run method on a separate thread and starts
        process_video method at engine instance
        """
        process_thread = threading.Thread(target=self._run)
        process_thread.start()
        uvicorn.run(self.app, host=self._host, port=self._port, log_level='error')
        self.__ENGINE_INSTANCE.running_video = False
