import pytest

from api.models.app import AppDTO
from api.tests.utils.common_functions import create_app_config, camel_case_to_snake_case_dict, get_app_from_config_file
# The line below is absolutely necessary. Fixtures are passed as arguments to test functions.
# This is why the IDE cannot recognize them.
from api.tests.utils.fixtures_tests import config_rollback, app_config


def expected_response_default():
    """When no valid key is provided to the PUT request, config is updated with default values stored in AppDTO"""
    expected_response = AppDTO().__dict__
    expected_response = camel_case_to_snake_case_dict(expected_response)
    expected_response["has_been_configured"] = True
    return expected_response


# pytest -v api/tests/app/test_app.py::TestsGetAppConfig
class TestsGetAppConfig:
    """Get App Config, GET /app"""

    def test_get_app_config(self, config_rollback):
        client, config_sample_path = config_rollback

        response = client.get("/app")

        expected_response = get_app_from_config_file(config_sample_path)

        assert response.status_code == 200
        assert response.json() == expected_response


# pytest -v api/tests/app/test_app.py::TestsUpdateAppConfig
class TestsUpdateAppConfig:
    """Update App Config, PUT /app"""

    # pytest -v api/tests/app/test_app.py::TestsUpdateAppConfig::test_change_app_config_properly
    def test_change_app_config_properly(self, config_rollback, app_config):
        client, config_sample_path = config_rollback

        body = app_config
        response = client.put("/app", json=body)

        expected_response = get_app_from_config_file(config_sample_path)
        assert response.status_code == 200
        assert response.json() == expected_response

    # pytest -v api/tests/app/test_app.py::TestsUpdateAppConfig::test_try_change_app_config_wrong_type_variable_all
    @pytest.mark.parametrize("key_value_dict, correct_type", [
        ({"has_been_configured": "Here_must_be_a_bool_variable"}, "bool"),
        ({"has_been_configured": 40}, "bool"),
        ({"resolution": False}, "string"),
        ({"resolution": 40}, "string"),
        ({"encoder": False}, "string"),
        ({"encoder": 40}, "string"),
        ({"max_processes": "Here_must_be_an_integer_variable"}, "integer"),
        ({"max_processes": False}, "integer"),
        ({"dashboardurl": 40}, "string"),
        ({"dashboardurl": False}, "string"),
        ({"slack_channel": 40}, "string"),
        ({"slack_channel": False}, "string"),
        ({"occupancy_alerts_min_interval": False}, "integer"),
        ({"occupancy_alerts_min_interval": "Here_must_be_an_integer_variable"}, "integer"),
        ({"max_thread_restarts": False}, "integer"),
        ({"max_thread_restarts": "Here_must_be_an_integer_variable"}, "integer"),
        ({"global_reporting_emails": 40}, "string"),
        ({"global_reporting_emails": False}, "string"),
        ({"global_report_time": 40}, "string"),
        ({"global_report_time": False}, "string"),
        ({"daily_global_report": "Here_must_be_a_bool_variable"}, "bool"),
        ({"daily_global_report": 40}, "bool"),
        ({"weekly_global_report": "Here_must_be_a_bool_variable"}, "bool"),
        ({"weekly_global_report": 40}, "bool"),
        ({"heatmap_resolution": 40}, "string"),
        ({"heatmap_resolution": False}, "string"),
        ({"entity_config_directory": False}, "string"),
        ({"entity_config_directory": 40}, "string"),
        ({"log_performance_metrics_directory": False}, "string"),
        ({"log_performance_metrics_directory": 40}, "string")
    ])
    def test_try_change_app_config_wrong_type_variable_all(self, config_rollback, key_value_dict,
                                                           correct_type):
        """
        It is important to mention, the fact that if pydantic expects a string, it will try to
        cast what was sent, so if we send a bool or an integer to a string field, the field will be valid:
          Example:
              a = bool or integer -> str(a)
          Pydantic will accept it and PUT request will work.

        Same happens when we send bool, and an integer is expected.
            int(False) -> 0
            int(True) -> 1
        """
        client, config_sample_path = config_rollback

        body = create_app_config(key_value_dict)

        response = client.put("/app", json=body)

        if correct_type == "string":
            assert response.status_code == 200

            expected_response = get_app_from_config_file(config_sample_path)
            key = list(key_value_dict.keys())[0]
            value = list(key_value_dict.values())[0]
            expected_response[key] = str(value)
            assert response.json() == expected_response
        elif correct_type == "integer":
            for key, value in key_value_dict.items():
                if isinstance(key_value_dict[key], str):
                    assert response.status_code == 400
                    assert response.json()["detail"][0]["type"] == "type_error." + correct_type
                else:
                    assert response.status_code == 200
                    expected_response = get_app_from_config_file(config_sample_path)
                    assert response.json() == expected_response
        elif correct_type == "bool":
            assert response.status_code == 400
            assert response.json()["detail"][0]["type"] == "type_error." + "bool"
        else:
            assert response.status_code == 400

    # pytest -v api/tests/app/test_app.py::TestsUpdateAppConfig::test_try_change_app_config_non_existence_key
    def test_try_change_app_config_non_existence_key(self, config_rollback):
        client, config_sample_path = config_rollback

        # Extra keys are ignored
        body = {
            "invalid_1": "example_1",
            "invalid_2": "example_2",
            "invalid_3": "example_3"
        }
        response = client.put("/app", json=body)

        expected_response = get_app_from_config_file(config_sample_path)
        default_response = expected_response_default()

        assert response.status_code == 200
        assert response.json() == expected_response
        assert response.json() == default_response

    # pytest -v api/tests/app/test_app.py::TestsUpdateAppConfig::test_try_change_app_config_empty_json
    def test_try_change_app_config_empty_json(self, config_rollback):
        client, config_sample_path = config_rollback

        body = {}
        response = client.put("/app", json=body)

        expected_response = get_app_from_config_file(config_sample_path)
        default_response = expected_response_default()

        assert response.status_code == 200
        assert response.json() == expected_response
        assert response.json() == default_response
