import json

import pytest
import shutil
import os
import copy
from pathlib import Path

from fastapi.testclient import TestClient

from constants import ALL_AREAS
from libs.config_engine import ConfigEngine
from api.settings import Settings
from api.tests.utils.common_functions import create_app_config
from libs.utils import config as config_utils


from .example_models import camera_template, camera_example, camera_example_2, camera_example_3, camera_example_4,\
    area_example, area_example_2
from ...utils import get_config


def config_rollback_base(option="JUST_CAMERAS"):
    original_path = ""
    if option == "EMPTY":
        """
        Empty template with no camera or area.
        """
        original_path = "/repo/api/tests/data/config-x86-openvino_EMPTY.ini"
    elif option == "JUST_CAMERAS":
        """
        Here there are charged only 2 cameras:
            camera_example (ID: 49)
            camera_example_2 (ID: 50)
        """
        original_path = "/repo/api/tests/data/config-x86-openvino_JUST_CAMERAS.ini"
    elif option == "METRICS":
        """
        Here there are charged 4 cameras and two areas:
            camera_example (ID: 49), Area 5
            camera_example_2 (ID: 50), Area 5
            camera_example_3 (ID: 51), Area 6
            camera_example_4 (ID: 52), Area 6
        """
        original_path = "/repo/api/tests/data/config-x86-openvino_METRICS.ini"
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
def rollback_camera_template():
    yield None
    for id_camera in [str(camera_template["id"]), str(int(camera_template["id"]) + 1)]:
        camera_screenshot_directory = os.path.join(os.environ.get("ScreenshotsDirectory"), id_camera)
        if os.path.exists(camera_screenshot_directory):
            shutil.rmtree(camera_screenshot_directory)
        camera_directory = os.path.join(os.environ.get("SourceLogDirectory"), id_camera)
        if os.path.exists(camera_directory):
            shutil.rmtree(camera_directory)


@pytest.fixture
def rollback_camera_config():
    yield None
    for id_camera in [str(camera_example["id"]), str(camera_example_2["id"])]:
        ml_models_directory = os.path.join(os.environ.get("SourceConfigDirectory"), id_camera, "ml_models")
        if os.path.exists(ml_models_directory):
            shutil.rmtree(ml_models_directory)


@pytest.fixture
def config_rollback():
    client, config_sample_path_to_modify = config_rollback_base(option="EMPTY")
    yield client, config_sample_path_to_modify
    os.remove(config_sample_path_to_modify)


@pytest.fixture
def config_rollback_areas():
    client, config_sample_path_to_modify = config_rollback_base(option="METRICS")
    yield area_example, area_example_2, client, config_sample_path_to_modify
    os.remove(config_sample_path_to_modify)


@pytest.fixture
def config_rollback_cameras():
    client, config_sample_path_to_modify = config_rollback_base(option="JUST_CAMERAS")
    yield camera_example, camera_example_2, client, config_sample_path_to_modify
    os.remove(config_sample_path_to_modify)


@pytest.fixture
def app_config():
    app_config = create_app_config()
    return app_config


@pytest.fixture
def camera_sample():
    camera_sample = copy.deepcopy(camera_template)
    return camera_sample


@pytest.fixture
def rollback_homography_matrix_folder():
    """
    '/repo/api/tests/data/mocked_data/data/processor/config/'
    comes from -->
    config.get_section_dict('App')['EntityConfigDirectory']

    Remember that we use another configuration file to test. So ('App')['EntityConfigDirectory'] is modified
    to point to our mocked data.
    """
    yield None
    # Deletes the homography_matrix directory and all its content.
    raw = "/repo/api/tests/data/mocked_data/data/processor/config"
    path = os.path.join(raw, "sources", str(camera_template["id"]), "homography_matrix")
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
    os.environ["HeatMapPath"] = "/repo/api/tests/data/mocked_data/data/processor/static/data/sources/"
    # Creates heatmaps directory
    heatmap_directory = os.path.join(os.getenv("SourceLogDirectory"), camera_example['id'], "heatmaps")
    Path(heatmap_directory).mkdir(parents=True, exist_ok=True)
    # Copy file to heatmaps to directory
    original_path_violations = "/repo/api/tests/data/violations_heatmap_2020-09-19_EXAMPLE.npy"
    original_path_detections = "/repo/api/tests/data/detections_heatmap_2020-09-19_EXAMPLE.npy"
    heatmap_path_to_modify_violations = os.path.join(heatmap_directory, "violations_heatmap_2020-09-19.npy")
    heatmap_path_to_modify_detections = os.path.join(heatmap_directory, "detections_heatmap_2020-09-19.npy")
    shutil.copyfile(original_path_violations, heatmap_path_to_modify_violations)
    shutil.copyfile(original_path_detections, heatmap_path_to_modify_detections)
    # Generates more data
    new_heatmap_path_to_modify_violations = os.path.join(heatmap_directory, "violations_heatmap_2020-09-22.npy")
    new_heatmap_path_to_modify_detections = os.path.join(heatmap_directory, "detections_heatmap_2020-09-22.npy")
    shutil.copyfile(original_path_detections, new_heatmap_path_to_modify_violations)
    shutil.copyfile(original_path_violations, new_heatmap_path_to_modify_detections)
    yield None
    # Deletes everything
    shutil.rmtree(heatmap_directory)

@pytest.fixture
def rollback_area_all_json():
    config_directory = config_utils.get_area_config_directory(get_config())
    config_path = os.path.join(config_directory, ALL_AREAS + ".json")

    try:
        with open(config_path, "r") as file:
            file_content = json.load(file)
    except Exception:
        yield False
    else:
        yield True
        with open(config_path, "w") as file:
            json.dump(file_content, file)


@pytest.fixture
def rollback_area_config_path():
    yield None
    config_directory = config_utils.get_area_config_directory(get_config())
    for area_id in [area_example["id"], area_example_2["id"]]:
        config_path = os.path.join(config_directory, area_id + ".json")
        if os.path.exists(config_path):
            os.remove(config_path)
