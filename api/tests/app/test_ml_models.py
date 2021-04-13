import pytest
import os
import json

# The line below is absolutely necessary. Fixtures are passed as arguments to test functions.
# This is why the IDE cannot recognize them.
from api.tests.utils.fixtures_tests import config_rollback_cameras, rollback_camera_config


def pascal_case_to_snake_case(parameters):
    result = {}

    for key, value in parameters.items():
        result[''.join(word.title() for word in key.split('_'))] = value

    if "ClassId" in result.keys():
        result["ClassID"] = result["ClassId"]
        del result["ClassId"]

    return result


def expected_response(body_parameters):
    parameters = pascal_case_to_snake_case(body_parameters)

    result = {}

    result["model_name"] = parameters["Name"]

    del parameters["Name"]
    del parameters["Device"]
    result["variables"] = parameters

    return result


def saved_file(camera_id, body):
    model_path = os.path.join(os.environ.get("SourceConfigDirectory"), camera_id, "ml_models",
                              f"model_{body['device']}.json")

    with open(model_path, "r") as file:
        json_file_content = json.load(file)

    return json_file_content


# pytest -v api/tests/app/test_ml_models.py::TestsModifyMLModel
class TestsModifyMLModel:
    """Change the ML model to process a camera, POST /ml_model/{camera_id}"""

    def test_change_ml_model_properly(self, config_rollback_cameras, rollback_camera_config):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        body = {
            "device": "Jetson",
            "name": "openpifpaf_tensorrt",
            "image_size": "641,369,3",
            "model_path": "string",
            "class_id": 0,
            "min_score": 0.3,
            "tensorrt_precision": 32
        }
        response = client.post(f"/ml_model/{camera_id}", json=body)

        assert response.status_code == 200
        assert response.json() == expected_response(body)
        assert response.json() == saved_file(camera_id, body)

    def test_try_change_ml_model_wrong_camera_id(self, config_rollback_cameras, rollback_camera_config):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = "Wrong ID"

        body = {
            "device": "Jetson",
            "name": "openpifpaf_tensorrt",
            "image_size": "641,369,3",
            "model_path": "string",
            "class_id": 0,
            "min_score": 0.3,
            "tensorrt_precision": 32
        }
        response = client.post(f"/ml_model/{camera_id}", json=body)

        assert response.status_code == 404
        assert response.json() == {'detail': 'The camera: Wrong ID does not exist'}

    @pytest.mark.parametrize("key_value_dict, status_code_expected", [
        ({"device": "Non-existent Device"}, 400),
        ({"device": ""}, 400),
        ({"device": "None"}, 400),
        ({"device": "jetson"}, 400),  # "jetson" does not have a capital letter.
        ({"device": 20}, 400),
        ({"device": 20.1}, 400),
        ({"device": {}}, 400),
        ({"device": None}, 400),
        ({"tensorrt_precision": 40}, 400),
        ({"tensorrt_precision": None}, 200),
        ({"tensorrt_precision": "None"}, 400),
        ({"tensorrt_precision": ""}, 400),
        ({"tensorrt_precision": "string"}, 400),
        ({"tensorrt_precision": "16"}, 200),  # Success
        ({"tensorrt_precision": "32"}, 200),  # Success
        ({"tensorrt_precision": "32.2"}, 400),
        ({"tensorrt_precision": "32.0"}, 400),
        ({"tensorrt_precision": -32}, 400),
        ({"tensorrt_precision": -16}, 400),
        ({"tensorrt_precision": {}}, 400),
        ({"tensorrt_precision": 16.0}, 200),  # Success
        ({"tensorrt_precision": 16.2}, 200),  # Success
        ({"tensorrt_precision": 95.2}, 400),
        ({"name": "Non-existent Model"}, 400),
        ({"name": "Openvino"}, 400),  # "Openvino" has a capital letter.
        ({"name": 20}, 400),
        ({"name": 20.1}, 400),
        ({"name": {}}, 400),
        ({"name": None}, 400),
        ({"image_size": None}, 400),
        ({"image_size": ",,"}, 400),
        ({"image_size": " , , "}, 400),
        ({"image_size": "-1,-1,-2"}, 200),  # Success
        ({"image_size": "2,2,-2"}, 200),  # Success
        ({"image_size": "2, 2, 2"}, 200),  # Success
        ({"image_size": "2,2,2,2"}, 400),
        ({"image_size": "2,2"}, 400),
        ({"image_size": "2,2,"}, 400),
        ({"image_size": (2, 2, 2)}, 400),
        ({"image_size": 40}, 400),
        ({"image_size": 40.5}, 400),
        ({"image_size": "string"}, 400),
        ({"image_size": "None"}, 400),
        ({"image_size": "30.30.5"}, 400),
        ({"image_size": ""}, 400),
        ({"image_size": {}}, 400),
        ({"model_path": "Non-existent path"}, 200),  # Success
        ({"model_path": ""}, 200),
        ({"model_path": 20}, 200),  # Success
        ({"model_path": 20.1}, 200),  # Success
        ({"model_path": {}}, 400),
        ({"model_path": None}, 400),
        ({"class_id": "Non-existent ID"}, 400),
        ({"class_id": ""}, 400),
        ({"class_id": "20"}, 200),  # Success
        ({"class_id": "-20"}, 200),  # Success
        ({"class_id": 20}, 200),  # Success
        ({"class_id": -20}, 200),  # Success
        ({"class_id": (20, 30)}, 400),
        ({"class_id": 20.1}, 200),  # Success
        ({"class_id": -20.1}, 200),  # Success
        ({"class_id": 20.0}, 200),  # Success
        ({"class_id": -20.0}, 200),  # Success
        ({"class_id": {}}, 400),
        ({"class_id": None}, 400),
        ({"min_score": "Wrong score"}, 400),
        ({"min_score": ""}, 400),
        ({"min_score": "5"}, 200),  # Success
        ({"min_score": "20.4"}, 200),  # Success
        ({"min_score": "20.0"}, 200),  # Success
        ({"min_score": "-20.3"}, 200),  # Success
        ({"min_score": "-20.0"}, 200),  # Success
        ({"min_score": 20}, 200),  # Success
        ({"min_score": -20}, 200),  # Success
        ({"min_score": (20.5, 30.4)}, 400),
        ({"min_score": -20.1}, 200),  # Success
        ({"min_score": 20.0}, 200),  # Success
        ({"min_score": -20.0}, 200),  # Success
        ({"min_score": {}}, 400),
        ({"min_score": None}, 400)
    ])
    def test_try_change_ml_model_only_one_parameter_wrong(self, config_rollback_cameras, rollback_camera_config,
                                                          key_value_dict, status_code_expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        body = {
            "device": "EdgeTPU",
            "name": "mobilenet_ssd_v2",
            "image_size": "641,369,3",
            "model_path": "string",
            "class_id": 0,
            "min_score": 0.3,
            "tensorrt_precision": 32
        }
        body.update(key_value_dict)

        response = client.post(f"/ml_model/{camera_id}", json=body)

        assert response.status_code == status_code_expected

    @pytest.mark.parametrize("parameter, status_code_expected", [
        ("device", 400),
        ("name", 400),
        ("image_size", 400),
        ("model_path", 200),
        ("class_id", 200),
        ("min_score", 200),
        ("tensorrt_precision", 200),
    ])
    def test_try_change_ml_model_one_missing_parameter(self, config_rollback_cameras, rollback_camera_config, parameter,
                                                       status_code_expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        body = {
            "device": "x86",
            "name": "openvino",
            "image_size": "300,300,3",
            "model_path": "string",
            "class_id": 0,
            "min_score": 0.3,
            "tensorrt_precision": 32
        }
        del body[parameter]

        response = client.post(f"/ml_model/{camera_id}", json=body)

        assert response.status_code == status_code_expected

        if response.status_code == 200:
            for key in expected_response(body)["variables"].keys():
                # We check the response this way, because if some parameters are omitted, default values set in
                # MLModelDTO will be carried out.
                assert response.json()["variables"][key] == expected_response(body)["variables"][key]

    @pytest.mark.parametrize("model_name, status_code_expected", [
        ("ssd_mobilenet_v2_coco", 200),
        ("ssd_mobilenet_v2_pedestrian_softbio", 200),
        ("openpifpaf_tensorrt", 400),
        ("mobilenet_ssd_v2", 200),
        ("pedestrian_ssd_mobilenet_v2", 200),
        ("pedestrian_ssdlite_mobilenet_v2", 200),
        ("posenet", 200),
        ("mobilenet_ssd_v2", 200),
        ("openvino", 200),
        ("openpifpaf", 200),
        ("yolov3", 200)
    ])
    def test_try_change_ml_model_no_tensorrt_precision_parameter(self, config_rollback_cameras, rollback_camera_config,
                                                                 model_name, status_code_expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        body = {
            "name": model_name,
            "device": "Dummy",
            "image_size": "1281,721,3",
            "model_path": "string",
            "class_id": 0,
            "min_score": 0.3
        }

        if model_name == "yolov3":
            body["image_size"] = "416,416,3"

        response = client.post(f"/ml_model/{camera_id}", json=body)

        assert response.status_code == status_code_expected

    @pytest.mark.parametrize("model_name, status_code_expected", [
        ("ssd_mobilenet_v2_coco", 200),
        ("ssd_mobilenet_v2_pedestrian_softbio", 200),
        ("openpifpaf_tensorrt", 400),
        ("mobilenet_ssd_v2", 200),
        ("pedestrian_ssd_mobilenet_v2", 200),
        ("pedestrian_ssdlite_mobilenet_v2", 200),
        ("posenet", 400),  # Fails
        ("mobilenet_ssd_v2", 200),
        ("openvino", 200),
        ("openpifpaf", 400),  # Fails
        ("yolov3", 400)  # Fails
    ])
    def test_try_change_ml_model_random_image_size(self, config_rollback_cameras, rollback_camera_config,
                                                                 model_name, status_code_expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        image_size = "300,300,3"

        body = {
            "name": model_name,
            "device": "Dummy",
            "image_size": image_size,
            "model_path": "string",
            "class_id": 0,
            "min_score": 0.3
        }

        response = client.post(f"/ml_model/{camera_id}", json=body)

        assert response.status_code == status_code_expected

    def test_try_change_ml_model_bad_model_for_given_device(self, config_rollback_cameras, rollback_camera_config):
        """There are several cases where this test fails, we only test one to check if it is working."""
        """
        The device "Jetson" only supports the following models: "ssd_mobilenet_v2_coco",
        "ssd_mobilenet_v2_pedestrian_softbio" and "openpifpaf_tensorrt".
        """

        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        body = {
            "device": "Jetson",
            "name": "openvino",
            "image_size": "300,300,3",
            "model_path": "string",
            "class_id": 0,
            "min_score": 0.3,
            "tensorrt_precision": 32
        }
        response = client.post(f"/ml_model/{camera_id}", json=body)

        assert response.status_code == 400

    def test_change_ml_model_properly_three_times(self, config_rollback_cameras, rollback_camera_config):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        # First time, no .json file is detected, so it has to be created.
        body = {
            "device": "Jetson",
            "name": "openpifpaf_tensorrt",
            "image_size": "641,369,3",
            "model_path": "string",
            "class_id": 0,
            "min_score": 0.3,
            "tensorrt_precision": 32
        }
        response_1 = client.post(f"/ml_model/{camera_id}", json=body)
        
        assert response_1.status_code == 200
        assert response_1.json() == expected_response(body)
        assert response_1.json() == saved_file(camera_id, body)

        # Second time, a .json file is detected, so it has to be overwritten with the same data.
        response_2 = client.post(f"/ml_model/{camera_id}", json=body)

        assert response_2.status_code == 200
        assert response_2.json() == expected_response(body)
        assert response_2.json() == saved_file(camera_id, body)

        # Third time, a .json file is detected, and we check if new values were successfully changed.
        body["name"] = "ssd_mobilenet_v2_pedestrian_softbio"
        body["min_score"] = 0.5

        response_3 = client.post(f"/ml_model/{camera_id}", json=body)

        assert response_3.status_code == 200
        assert response_3.json() == expected_response(body)
        assert response_3.json() == saved_file(camera_id, body)

    def test_try_change_ml_model_create_a_camera_recently(self, config_rollback_cameras, rollback_camera_config):
        camera, camera_2, client, config_sample_path = config_rollback_cameras

        # Create the camera

        camera_template = {
            "violation_threshold": 100,
            "notify_every_minutes": 15,
            "emails": "john@email.com,doe@email.com",
            "enable_slack_notifications": False,
            "daily_report": True,
            "daily_report_time": "06:00",
            "id": "200",
            "name": "Kitchen",
            "video_path": "/repo/api/tests/data/mocked_data/data/softbio_vid.mp4",
            "tags": "kitchen,living_room",
            "dist_method": "CenterPointsDistance",
            "live_feed_enabled": False
        }

        camera_id = camera_template["id"]

        client.post("/cameras", json=camera_template)

        # Set the ML Model

        body_ml_model = {
            "device": "Jetson",
            "name": "openpifpaf_tensorrt",
            "image_size": "641,369,3",
            "model_path": "string",
            "class_id": 0,
            "min_score": 0.3,
            "tensorrt_precision": 32
        }
        response = client.post(f"/ml_model/{camera_id}", json=body_ml_model)

        assert response.status_code == 200
        assert response.json() == expected_response(body_ml_model)
        assert response.json() == saved_file(camera_id, body_ml_model)

        # Rollback the camera

        client.delete(f"/cameras/{camera_id}")
