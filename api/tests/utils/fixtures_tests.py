import pytest
import shutil
import os
import copy

from fastapi.testclient import TestClient

from libs.config_engine import ConfigEngine
from api.settings import Settings
from api.tests.utils.common_functions import create_app_config

example = {
    "violation_threshold": 100,
    "notify_every_minutes": 15,
    "emails": "john@email.com,doe@email.com",
    "enable_slack_notifications": False,
    "daily_report": True,
    "daily_report_time": "06:00",
    "id": "49",
    "name": "Kitchen",
    "video_path": "/repo/data/softbio_vid.mp4",
    "tags": "kitchen,living_room",
    "dist_method": "CenterPointsDistance",
    "live_feed_enabled": False
}


@pytest.fixture
def config_rollback():
    original_path = "/repo/api/tests/data/config-x86-openvino.ini"
    config_sample_path_to_modify = "/repo/api/tests/data/config-x86-openvino_TEMPORARY.ini"
    shutil.copyfile(original_path, config_sample_path_to_modify)

    config = ConfigEngine(config_sample_path_to_modify)
    Settings(config=config)

    # Import ProcessorAPI after Settings has been initialized with a config.
    from api.processor_api import ProcessorAPI

    app_instance = ProcessorAPI()
    api = app_instance.app
    client = TestClient(api)
    yield client, config_sample_path_to_modify

    os.remove(config_sample_path_to_modify)


@pytest.fixture
def app_config():
    app_config = create_app_config()
    return app_config


@pytest.fixture
def camera_sample():
    camera_sample = copy.deepcopy(example)
    return camera_sample


@pytest.fixture
def rollback_screenshot_camera_folder():
    yield None
    # Deletes the camera screenshots directory and all its content.
    camera_screenshot_directory = os.path.join(os.environ.get("ScreenshotsDirectory"), str(example["id"]))
    if os.path.exists(camera_screenshot_directory):
        shutil.rmtree(camera_screenshot_directory)


@pytest.fixture
def rollback_homography_matrix_folder():
    yield None
    # Deletes the homography_matrix directory and all its content.
    raw = f"/repo/data/processor/static/data/sources/"
    path = os.path.join(raw, str(example["id"]))
    if os.path.exists(path):
        shutil.rmtree(path)


@pytest.fixture
def h_inverse_matrix():
    return {"h_inverse.txt": "h_inv: 0.8196721311475405 0.6333830104321896 -302.9061102831591 -1.8201548094104302e-16 "
                             "1.7138599105812207 -531.2965722801783 -2.7856282300542207e-18 0.008047690014903118 "
                             "-1.4947839046199658"}


@pytest.fixture
def pts_destination():
    return {
        "pts_destination": [
            [
                130,
                310
            ],
            [
                45,
                420
            ],
            [
                275,
                420
            ],
            [
                252,
                310
            ]
        ]
    }
