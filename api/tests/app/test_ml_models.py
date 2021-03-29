import pytest

# The line below is absolutely necessary. Fixtures are passed as arguments to test functions.
# This is why the IDE cannot recognize them.
from api.tests.utils.fixtures_tests import config_rollback_cameras, rollback_camera_config


# pytest -v api/tests/app/test_ml_models.py::TestsModifyMLModel
class TestsModifyMLModel:
    """Change the ML model to process a camera, POST /ml_model/{camera_id}"""

    def test_change_ml_model_correctly(self, config_rollback_cameras, rollback_camera_config):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        body = {
            "device": "Jetson",
            "name": "openpifpaf_tensorrt",
            "image_size": "300,300,3",
            "model_path": "string",
            "class_id": 0,
            "tensorrt_precision": 32
        }
        response = client.post(f"/ml_model/{camera_id}", json=body)

        import pdb
        pdb.set_trace()

        assert response.status_code == 200
