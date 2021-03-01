import pytest
import shutil
import os
import copy
from pathlib import Path

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

example_2 = {
    "violation_threshold": 90,
    "notify_every_minutes": 14,
    "emails": "nicolas@email.com,cage@email.com",
    "enable_slack_notifications": False,
    "daily_report": True,
    "daily_report_time": "05:40",
    "id": "50",
    "name": "Kitchen",
    "video_path": "/repo/data/softbio_vid.mp4",
    "tags": "kitchen,living_room",
    "dist_method": "CenterPointsDistance",
    "live_feed_enabled": False
}


def config_rollback_base():
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
    return client, config_sample_path_to_modify


@pytest.fixture
def config_rollback():
    client, config_sample_path_to_modify = config_rollback_base()
    yield client, config_sample_path_to_modify
    os.remove(config_sample_path_to_modify)


def create_camera(client, example_camera):
    camera_sample = copy.deepcopy(example_camera)
    return client.post("/cameras", json=camera_sample)


def delete_camera(client, camera_id):
    client.delete(f'/cameras/{camera_id}')


@pytest.fixture
def config_rollback_create_cameras():
    client, config_sample_path_to_modify = config_rollback_base()

    response_camera_1 = create_camera(client, copy.deepcopy(example))
    response_camera_2 = create_camera(client, copy.deepcopy(example_2))

    yield response_camera_1.json(), response_camera_2.json(), client, config_sample_path_to_modify

    # Delete cameras
    delete_camera(client, example['id'])
    delete_camera(client, example_2['id'])

    # We have to remove .ini file after every endpoint call
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


@pytest.fixture
def heatmap_simulation():
    # Creates heatmaps directory
    heatmap_directory = os.path.join(os.getenv("SourceLogDirectory"), example['id'], "heatmaps")
    Path(heatmap_directory).mkdir(parents=True, exist_ok=True)
    # Copy file to heatmaps to directory
    original_path_violations = "/repo/api/tests/data/violations_heatmap_2020-09-19_EXAMPLE.npy"
    original_path_detections = "/repo/api/tests/data/detections_heatmap_2020-09-19_EXAMPLE.npy"
    heatmap_path_to_modify_violations = f"/repo/data/processor/static/data/sources/{example['id']}/heatmaps/violations_heatmap_2020-09-19.npy"
    heatmap_path_to_modify_detections = f"/repo/data/processor/static/data/sources/{example['id']}/heatmaps/detections_heatmap_2020-09-19.npy"
    shutil.copyfile(original_path_violations, heatmap_path_to_modify_violations)
    shutil.copyfile(original_path_detections, heatmap_path_to_modify_detections)
    # Generates more data
    new_heatmap_path_to_modify_violations = f"/repo/data/processor/static/data/sources/{example['id']}/heatmaps/violations_heatmap_2020-09-22.npy"
    new_heatmap_path_to_modify_detections = f"/repo/data/processor/static/data/sources/{example['id']}/heatmaps/detections_heatmap_2020-09-22.npy"
    shutil.copyfile(original_path_detections, new_heatmap_path_to_modify_violations)
    shutil.copyfile(original_path_violations, new_heatmap_path_to_modify_detections)
    yield None
    # Deletes everything
    shutil.rmtree(heatmap_directory)


"""
def create_reports(id_camera):
    # Creates reports directory
    reports_directory = os.path.join(os.getenv("SourceLogDirectory"), id_camera, "reports")
    Path(reports_directory).mkdir(parents=True, exist_ok=True)
    # Creates metric directories
    face_mask_usage_directory = os.path.join(reports_directory, "face-mask-usage")
    Path(face_mask_usage_directory).mkdir(parents=True, exist_ok=True)
    social_distancing_directory = os.path.join(reports_directory, "social-distancing")
    Path(social_distancing_directory).mkdir(parents=True, exist_ok=True)
    # Copy live.csv files to corresponding to directories
    face_mask_usage_original_path_live_file = "/repo/api/tests/data/reports_EXAMPLE/face-mask-usage/live.csv"
    social_distancing_original_path_live_file = "/repo/api/tests/data/reports_EXAMPLE/social-distancing/live.csv"
    destination_face_mask_usage = os.path.join(face_mask_usage_directory, "live.csv")
    destination_social_distancing = os.path.join(social_distancing_directory, "live.csv")
    shutil.copyfile(face_mask_usage_original_path_live_file, destination_face_mask_usage)
    shutil.copyfile(social_distancing_original_path_live_file, destination_social_distancing)
"""


def copy_tree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def create_reports(id_camera):
    fromDirectory = "/repo/api/tests/data/reports_EXAMPLE/"
    reports_directory = os.path.join(os.getenv("SourceLogDirectory"), id_camera, "reports")
    copy_tree(fromDirectory, reports_directory)


def delete_reports(id_camera):
    # Deletes everything
    reports_directory = os.path.join(os.getenv("SourceLogDirectory"), id_camera, "reports")
    shutil.rmtree(reports_directory)


@pytest.fixture
def reports_simulation():
    create_reports(example['id'])
    create_reports(example_2['id'])
    yield None
    delete_reports(example['id'])
    delete_reports(example_2['id'])

