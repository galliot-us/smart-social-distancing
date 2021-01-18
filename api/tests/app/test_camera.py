import pytest

from api.tests.utils.common_functions import get_section_from_config_file

# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback, app_config


# pytest -v api/tests/app/test_camera.py::TestClassGetAppConfig
class TestClassListCameras:
    """List Cameras, GET /cameras"""

    def test_get_app_config(self, config_rollback):
        client, config_sample_path = config_rollback

        cameras_json = get_section_from_config_file("HERE GOES THE SECTION I WANT", config_sample_path)

        response = client.get('/cameras')

        assert response.status_code == 200
        # assert response.json() == True
