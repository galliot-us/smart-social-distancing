import pytest
import os
import base64
import copy
import numpy

from api.tests.utils.common_functions import get_section_from_config_file, get_config_file_json

# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback, camera_sample, rollback_screenshot_camera_folder, h_inverse_matrix, pts_destination, rollback_homography_matrix_folder

# TODO: Test stuffs related with the parameter reboot_processor.


def create_a_camera(client, camera):
    return client.post("/cameras", json=camera)


def create_2_cameras(client, camera_base, enable=False):
    camera_1 = copy.deepcopy(camera_base)
    camera_2 = copy.deepcopy(camera_base)
    camera_1["id"] = "321"
    camera_2["id"] = "123"
    camera_1["live_feed_enabled"] = enable
    camera_2["live_feed_enabled"] = enable
    client.post("/cameras", json=camera_1)
    client.post("/cameras", json=camera_2)
    return camera_1, camera_2


def get_all_cameras(config_sample_path, with_image=False):
    config_file_json = get_config_file_json(config_sample_path, decamelize=True)

    list_of_cameras = {
        "cameras": [config_file_json[camera] for camera in config_file_json if camera.startswith("source__")]}

    for camera in list_of_cameras["cameras"]:
        camera.update({"id": str(camera["id"])})

        if with_image:
            from api.routers.cameras import get_camera_default_image_string
            image_string = get_camera_default_image_string(camera["id"])
            camera["image"] = image_string.decode("utf-8")
        else:
            camera["image"] = None

    return list_of_cameras


def get_camera_from_config_file(camera_id, config_sample_path):
    list_of_cameras = get_all_cameras(config_sample_path)["cameras"]
    for camera in list_of_cameras:
        if camera["id"] == camera_id:
            return camera
    return None


# pytest -v api/tests/app/test_camera.py::TestClassListCameras
class TestClassListCameras:
    """List Cameras, GET /cameras"""

    def test_get_all_cameras_no_image(self, config_rollback):
        client, config_sample_path = config_rollback

        list_of_cameras = get_all_cameras(config_sample_path)

        response = client.get("/cameras")

        assert response.status_code == 200
        assert response.json() == list_of_cameras

    def test_get_all_cameras_with_image(self, config_rollback):
        client, config_sample_path = config_rollback

        list_of_cameras = get_all_cameras(config_sample_path, with_image=True)

        response = client.get("/cameras?options=withImage")

        assert response.status_code == 200
        assert response.json() == list_of_cameras


# pytest -v api/tests/app/test_camera.py::TestClassCreateCamera
class TestClassCreateCamera:
    """Create Camera, POST /cameras"""

    def test_create_one_camera_properly(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback

        response = client.post("/cameras", json=camera_sample)

        assert response.status_code == 201
        for key in camera_sample:
            if key is not "image":
                assert response.json()[key] == camera_sample[key]

    def test_try_create_camera_twice(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback

        response_1 = client.post("/cameras", json=camera_sample)
        response_2 = client.post("/cameras", json=camera_sample)

        assert response_1.status_code == 201
        assert response_2.status_code == 400
        assert response_2.json() == {'detail': [{'loc': [], 'msg': 'Camera already exists', 'type': 'config '
                                                                                                    'duplicated '
                                                                                                    'camera'}]}

    def test_create_same_camera_twice_different_ids(self, config_rollback, camera_sample,
                                                    rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback

        body = camera_sample

        response_1 = client.post("/cameras", json=body)

        body["id"] = 54
        response_2 = client.post("/cameras", json=body)

        assert response_1.status_code == 201
        assert response_2.status_code == 201

    def test_try_create_camera_empty_body(self, config_rollback):
        client, config_sample_path = config_rollback

        body = {}
        response = client.post("/cameras", json=body)

        assert response.status_code == 400

    def test_create_a_camera_function(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback

        response = create_a_camera(client, camera_sample)

        assert response.status_code == 201


# pytest -v api/tests/app/test_camera.py::TestClassGetCamera
class TestClassGetCamera:
    """ Get Camera, GET /cameras/{camera_id} """

    def test_get_one_camera_properly(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback

        create_a_camera(client, camera_sample)

        camera_id = int(camera_sample["id"])
        response = client.get(f"/cameras/{camera_id}")

        assert response.status_code == 200
        for key in camera_sample:
            if key is not "image":
                assert response.json()[key] == camera_sample[key]

    def test_try_get_camera_non_existent_id(self, config_rollback):
        client, config_sample_path = config_rollback

        camera_id = "Non-existent ID"
        response = client.get(f"/cameras/{camera_id}")

        assert response.status_code == 404


# pytest -v api/tests/app/test_camera.py::TestClassEditCamera
class TestClassEditCamera:
    """ Edit Camera, PUT /cameras/{camera_id} """

    def test_edit_a_camera_properly(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]
        body = {
            "violation_threshold": 22,
            "notify_every_minutes": 22,
            "emails": "new_john@email.com,new_doe@email.com",
            "enable_slack_notifications": True,
            "daily_report": False,
            "daily_report_time": "11:22",
            "id": camera_id,
            "name": "new_Kitchen",
            "video_path": "/repo/data/softbio_vid.mp4",
            "tags": "new_kitchen,new_living_room",
            "image": "new_Base64 image",
            "dist_method": "new_CenterPointsDistance",
            "live_feed_enabled": False
        }

        response = client.put(f"cameras/{camera_id}", json=body)

        assert response.status_code == 200
        for key in body:
            if key != "image":
                assert response.json()[key] == body[key]

    def test_try_edit_a_camera_non_existent_id(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = "Non-existent ID"
        body = {
            "violation_threshold": 22,
            "notify_every_minutes": 22,
            "emails": "new_john@email.com,new_doe@email.com",
            "enable_slack_notifications": True,
            "daily_report": False,
            "daily_report_time": "11:22",
            "id": camera_id,
            "name": "new_Kitchen",
            "video_path": "/repo/data/softbio_vid.mp4",
            "tags": "new_kitchen,new_living_room",
            "image": "new_Base64 image",
            "dist_method": "new_CenterPointsDistance",
            "live_feed_enabled": False
        }

        response = client.put(f"cameras/{camera_id}", json=body)

        assert response.status_code == 404
        assert response.json() == {"detail": f"The camera: {camera_id} does not exist"}

    def test_try_edit_camera_wrong_video_path(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]
        body = {
            "violation_threshold": 22,
            "notify_every_minutes": 22,
            "emails": "new_john@email.com,new_doe@email.com",
            "enable_slack_notifications": True,
            "daily_report": False,
            "daily_report_time": "11:22",
            "id": camera_id,
            "name": "new_Kitchen",
            "video_path": "WRONG_PATH",
            "tags": "new_kitchen,new_living_room",
            "image": "new_Base64 image",
            "dist_method": "new_CenterPointsDistance",
            "live_feed_enabled": False
        }

        response = client.put(f"cameras/{camera_id}", json=body)

        assert response.status_code == 400
        assert response.json()["detail"][0]["msg"] == "Failed to load video. The video URI is not valid"

    def test_edit_same_camera_twice(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]
        body_1 = {
            "violation_threshold": 22,
            "notify_every_minutes": 22,
            "emails": "new_john@email.com,new_doe@email.com",
            "enable_slack_notifications": True,
            "daily_report": False,
            "daily_report_time": "11:22",
            "id": camera_id,
            "name": "new_Kitchen",
            "video_path": "/repo/data/softbio_vid.mp4",
            "tags": "new_kitchen,new_living_room",
            "image": "new_Base64 image",
            "dist_method": "new_CenterPointsDistance",
            "live_feed_enabled": False
        }

        body_2 = {
            "violation_threshold": 33,
            "notify_every_minutes": 33,
            "emails": "new_new_john@email.com,new_new_doe@email.com",
            "enable_slack_notifications": False,
            "daily_report": False,
            "daily_report_time": "10:33",
            "id": camera_id,
            "name": "new_new_Kitchen",
            "video_path": "/repo/data/softbio_vid.mp4",
            "tags": "new_new_kitchen,new_new_living_room",
            "image": "new_new_Base64 image",
            "dist_method": "new_new_CenterPointsDistance",
            "live_feed_enabled": False
        }

        client.put(f"cameras/{camera_id}", json=body_1)
        response = client.put(f"cameras/{camera_id}", json=body_2)

        assert response.status_code == 200
        for key in body_2:
            if key != "image":
                assert response.json()[key] == body_2[key]

    def test_try_edit_camera_empty_json(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]
        body = {

        }

        response = client.put(f"cameras/{camera_id}", json=body)

        """
        Fields required: id, name, video_path
        """
        assert response.status_code == 400
        assert response.json() == {"detail": [{"loc": ["body", "id"], "msg": "field required", "type": "value_error"
                                                                                                       ".missing"},
                                              {"loc": ["body", "name"], "msg": "field required",
                                               "type": "value_error.missing"}, {"loc": ["body", "video_path"],
                                                                                "msg": "field required",
                                                                                "type": "value_error.missing"}],
                                   "body": {}}

    def test_edit_camera_empty_string_fields(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]

        # Video path is correctly setted
        body = {
            "violation_threshold": 33,
            "notify_every_minutes": 33,
            "emails": "",
            "enable_slack_notifications": False,
            "daily_report": False,
            "daily_report_time": "",
            "id": camera_id,
            "name": "",
            "video_path": "/repo/data/softbio_vid.mp4",
            "tags": "",
            "image": "",
            "dist_method": "",
            "live_feed_enabled": False
        }

        response = client.put(f"/cameras/{camera_id}", json=body)

        assert response.status_code == 200
        for key in camera_sample:
            if key is not "image":
                assert response.json()[key] == body[key]


# pytest -v api/tests/app/test_camera.py::TestClassDeleteCamera
class TestClassDeleteCamera:
    """ Delete Camera, DELETE /cameras/{camera_id} """

    def test_delete_a_camera_properly(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]

        response = client.delete(f"/cameras/{camera_id}")

        assert response.status_code == 204

    def test_try_delete_a_camera_twice(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]

        response_1 = client.delete(f"/cameras/{camera_id}")
        response_2 = client.delete(f"/cameras/{camera_id}")

        assert response_1.status_code == 204
        assert response_2.status_code == 404

    def test_try_delete_a_camera_non_existent_id(self, config_rollback):
        client, config_sample_path = config_rollback

        camera_id = "Non-existent ID"

        response = client.delete(f"/cameras/{camera_id}")

        assert response.status_code == 404

    def test_try_delete_a_camera_id_none(self, config_rollback):
        client, config_sample_path = config_rollback

        camera_id = None

        response = client.delete(f"/cameras/{camera_id}")

        assert response.status_code == 404

    def test_delete_a_camera_int_id(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = int(camera_sample["id"])

        response = client.delete(f"/cameras/{camera_id}")

        assert response.status_code == 204


def get_string_bytes_from_image(camera_id):
    camera_screenshot_directory = os.path.join(os.environ.get("ScreenshotsDirectory"), str(camera_id))
    image_name = os.listdir(camera_screenshot_directory)[0]
    camera_screenshot_file = os.path.join(camera_screenshot_directory, image_name)
    with open(camera_screenshot_file, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


# pytest -v api/tests/app/test_camera.py::TestClassGetCameraImage
class TestClassGetCameraImage:
    """ Get Camera Image, GET /cameras/{camera_id}/image """

    def test_get_camera_image_properly(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]
        response = client.get(f"/cameras/{camera_id}/image")

        assert response.status_code == 200
        assert response.json()["image"] == get_string_bytes_from_image(camera_id)

    def test_try_get_camera_image_non_existent_id(self, config_rollback):
        client, config_sample_path = config_rollback

        camera_id = "Non-existent ID"
        response = client.get(f"/cameras/{camera_id}/image")

        assert response.status_code == 404
        assert response.json() == {"detail": f"The camera: {camera_id} does not exist"}


def get_h_inverse(camera_id):
    path = f"/repo/data/processor/static/data/sources/{camera_id}/homography_matrix/h_inverse.txt"

    with open(path, "r") as file:
        h_inverse = file.read()

    return h_inverse


# pytest -v api/tests/app/test_camera.py::TestClassConfigCalibratedDistance
class TestClassConfigCalibratedDistance:
    """ Config Calibrated Distance, POST /cameras/{camera_id}/homography_matrix """

    # pytest -v api/tests/app/test_camera.py::TestClassConfigCalibratedDistance::test_set_coordinates_properly
    def test_set_coordinates_properly(self, config_rollback, camera_sample, rollback_screenshot_camera_folder, h_inverse_matrix, pts_destination, rollback_homography_matrix_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        body = pts_destination
        camera_id = camera_sample["id"]
        response = client.post(f"/cameras/{camera_id}/homography_matrix", json=body)

        assert response.status_code == 204
        assert get_h_inverse(camera_id) == h_inverse_matrix["h_inverse.txt"]

    # pytest -v api/tests/app/test_camera.py::TestClassConfigCalibratedDistance::test_try_set_coordinates_0_arrays
    def test_try_set_coordinates_0_arrays(self, config_rollback, camera_sample, rollback_screenshot_camera_folder, rollback_homography_matrix_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        body = {
            "pts_destination": [
                [
                    0,
                    0
                ],
                [
                    0,
                    0
                ],
                [
                    0,
                    0
                ],
                [
                    0,
                    0
                ]
            ]
        }

        camera_id = camera_sample["id"]

        with pytest.raises(numpy.linalg.LinAlgError):
            client.post(f"/cameras/{camera_id}/homography_matrix", json=body)

    def test_try_set_coordinates_non_existent_id(self, config_rollback, pts_destination):
        client, config_sample_path = config_rollback

        camera_id = "Non-existent ID"
        body = pts_destination
        response = client.post(f"/cameras/{camera_id}/homography_matrix", json=body)

        assert response.status_code == 404
        assert response.json() == {"detail": f"The camera: {camera_id} does not exist"}

    def test_try_set_coordinates_empty_request_body(self, config_rollback, camera_sample,
                                                    rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]
        body = {}
        response = client.post(f"/cameras/{camera_id}/homography_matrix", json=body)

        assert response.status_code == 400
        assert response.json() == {"detail": [{"loc": ["body", "pts_destination"], "msg": "field required",
                                               "type": "value_error.missing"}], "body": {}}

    def test_try_set_coordinates_bad_request_body(self, config_rollback, camera_sample,
                                                  rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]
        body = {"pts_destination": [None]}
        response = client.post(f"/cameras/{camera_id}/homography_matrix", json=body)

        assert response.status_code == 400
        assert response.json() == {"detail": [{"loc": ["body", "pts_destination"], "msg": "ensure this value has at "
                                                                                          "least 4 items",
                                               "type": "value_error.list.min_items", "ctx": {"limit_value": 4}}],
                                   "body": {"pts_destination": [None]}}


# pytest -v api/tests/app/test_camera.py::TestClassGetCameraCalibrationImage
class TestClassGetCameraCalibrationImage:
    """ Get Camera Calibration Image, GET /cameras/{camera_id}/calibration_image """

    def test_get_camera_calibration_image_properly(self, config_rollback, camera_sample,
                                                   rollback_screenshot_camera_folder):
        """ TODO: Maybe, here we could go deeper into the response.json() """
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]
        response = client.get(f"/cameras/{camera_id}/calibration_image")

        assert response.status_code == 200

    def test_try_get_camera_image_non_existent_id(self, config_rollback):
        client, config_sample_path = config_rollback

        camera_id = "Non-existent ID"
        response = client.get(f"/cameras/{camera_id}/calibration_image")

        assert response.status_code == 404
        assert response.json() == {"detail": f"The camera: {camera_id} does not exist"}


# pytest -v api/tests/app/test_camera.py::TestClassGetVideoLiveFeedEnabled
class TestClassGetVideoLiveFeedEnabled:
    """ Get Camera Calibration Image, GET /cameras/{camera_id}/video_live_feed_enabled """

    def test_get_camera_calibration_image_properly(self, config_rollback, camera_sample,
                                                   rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]
        response = client.get(f"/cameras/{camera_id}/video_live_feed_enabled")

        expected_response = {
            "enabled": camera_sample["live_feed_enabled"]
        }
        assert response.status_code == 200
        assert response.json() == expected_response

    def test_try_get_camera_image_non_existent_id(self, config_rollback):
        client, config_sample_path = config_rollback

        camera_id = "Non-existent ID"
        response = client.get(f"/cameras/{camera_id}/video_live_feed_enabled")

        assert response.status_code == 404
        assert response.json() == {"detail": f"The camera: {camera_id} does not exist"}


# pytest -v api/tests/app/test_camera.py::TestClassEnableVideoLiveFeed
class TestClassEnableVideoLiveFeed:
    """ Enable Video Live Feed, PUT /cameras/{camera_id}/enable_video_live_feed """

    def test_enable_video_live_feed_properly(self, config_rollback, camera_sample, rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        camera_sample["live_feed_enabled"] = False
        create_a_camera(client, camera_sample)

        camera_id = camera_sample["id"]
        response = client.put(f"/cameras/{camera_id}/enable_video_live_feed")

        camera_from_config_file = get_camera_from_config_file(camera_id, config_sample_path)

        assert response.status_code == 204
        assert camera_from_config_file["live_feed_enabled"] is True

    def test_try_enable_video_live_feed_non_existent_id(self, config_rollback):
        client, config_sample_path = config_rollback

        camera_id = "Non-existent ID"
        response = client.put(f"/cameras/{camera_id}/enable_video_live_feed")

        assert response.status_code == 404
        assert response.json() == {"detail": f"The camera: {camera_id} does not exist"}

    def test_enable_one_video_live_feed_disable_the_rest(self, config_rollback, camera_sample,
                                                         rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)
        camera_1, camera_2 = create_2_cameras(client, camera_sample)

        camera_id = camera_sample["id"]
        response = client.put(f"/cameras/{camera_id}/enable_video_live_feed?disable_other_cameras=true")

        camera_from_config_file_0 = get_camera_from_config_file(camera_id, config_sample_path)
        camera_from_config_file_1 = get_camera_from_config_file(camera_1["id"], config_sample_path)
        camera_from_config_file_2 = get_camera_from_config_file(camera_2["id"], config_sample_path)

        assert response.status_code == 204
        assert camera_from_config_file_0["live_feed_enabled"] is True
        assert camera_from_config_file_1["live_feed_enabled"] is False
        assert camera_from_config_file_2["live_feed_enabled"] is False

    def test_enable_video_feed_disable_other_cameras_false(self, config_rollback, camera_sample,
                                                      rollback_screenshot_camera_folder):
        client, config_sample_path = config_rollback
        create_a_camera(client, camera_sample)
        camera_1, camera_2 = create_2_cameras(client, camera_sample, True)

        camera_id = camera_sample["id"]
        response = client.put(f"/cameras/{camera_id}/enable_video_live_feed?disable_other_cameras=false")

        camera_from_config_file_0 = get_camera_from_config_file(camera_id, config_sample_path)
        camera_from_config_file_1 = get_camera_from_config_file(camera_1["id"], config_sample_path)
        camera_from_config_file_2 = get_camera_from_config_file(camera_2["id"], config_sample_path)

        assert response.status_code == 204
        assert camera_from_config_file_0["live_feed_enabled"] is True
        assert camera_from_config_file_1["live_feed_enabled"] is True
        assert camera_from_config_file_2["live_feed_enabled"] is True
