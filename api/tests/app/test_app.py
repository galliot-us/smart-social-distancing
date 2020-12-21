import pytest

from api.models.app import AppDTO
from api.tests.utils.common_functions import get_app_from_ini_config_file_json, json_multi_type_to_json_string, \
    create_app_config, camel_case_to_snake_case_dict
# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback, app_config


def expected_response_function(config_sample_path):
    expected_response = get_app_from_ini_config_file_json(config_sample_path)
    expected_response = json_multi_type_to_json_string(expected_response)

    # It is weird that this change does not appear in response.json()
    # Because if request was successfully, the PUT request will change the flag "has_been_configured"
    expected_response["has_been_configured"] = "False"

    return expected_response


def expected_response_default():
    """When no valid key is provided to the PUT request, config is updated with default values stored in AppDTO"""
    expected_response = AppDTO().__dict__
    expected_response = camel_case_to_snake_case_dict(expected_response)
    expected_response = json_multi_type_to_json_string(expected_response)
    expected_response["dashboard_url"] = expected_response["dashboard_u_r_l"]
    del expected_response["dashboard_u_r_l"]
    return expected_response


# pytest -v api/tests/app/test_app.py::TestClassGetAppConfig
class TestClassGetAppConfig:
    """Get App Config, GET /app"""

    def test_get_app_config(self, config_rollback):
        client, config_sample_path = config_rollback

        response = client.get('/app')

        expected_response = get_app_from_ini_config_file_json(config_sample_path)
        expected_response["dashboardurl"] = expected_response["dashboard_url"]
        del expected_response["dashboard_url"]

        assert response.status_code == 200
        assert response.json() == expected_response


# pytest -v api/tests/app/test_app.py::TestClassUpdateAppConfig
class TestClassUpdateAppConfig:
    """Update App Config, PUT /app"""

    # pytest -v api/tests/app/test_app.py::TestClassUpdateAppConfig::test_change_app_config_properly
    def test_change_app_config_properly(self, config_rollback, app_config):
        client, config_sample_path = config_rollback

        body = app_config
        response = client.put('/app', json=body)

        expected_response = expected_response_function(config_sample_path)
        assert response.status_code == 200
        assert response.json() == expected_response

    # pytest -v api/tests/app/test_app.py::TestClassUpdateAppConfig::test_try_change_app_config_wrong_type_variable_all
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
        ({"screenshots_directory": 40}, "string"),
        ({"screenshots_directory": False}, "string"),
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
    ])
    def test_try_change_app_config_wrong_type_variable_all(self, config_rollback, key_value_dict,
                                                           correct_type):
        """
        It is important to mention, the fact that if pydantic expects a string, it will try to
        cast what was sent, so if we send a bool or an integer to a string field, pydantic will work:
          Example:
              a = bool or integer
              str(a)
          Pydantic will accept it and PUT request will work.

        Idem when we send a bool, and an integer is expected.
            int(False) = 0
            int(True) = 1
        """
        client, config_sample_path = config_rollback

        body = create_app_config(key_value_dict)

        response = client.put('/app', json=body)

        if correct_type == "string":
            assert response.status_code == 200
            expected_response = expected_response_function(config_sample_path)
            assert response.json() == expected_response
        elif correct_type == "integer":
            for key, value in key_value_dict.items():
                if isinstance(key_value_dict[key], str):
                    assert response.status_code == 400
                    assert response.json()['detail'][0]['type'] == 'type_error.' + correct_type
                else:
                    assert response.status_code == 200
                    expected_response = expected_response_function(config_sample_path)
                    assert response.json() == expected_response
        else:
            assert response.status_code == 400
            assert response.json()['detail'][0]['type'] == 'type_error.' + correct_type

    # pytest -v api/tests/app/test_app.py::TestClassUpdateAppConfig::test_try_change_app_config_non_existence_key
    def test_try_change_app_config_non_existence_key(self, config_rollback):
        client, config_sample_path = config_rollback

        body = {
            "invalid_1": "example_1",
            "invalid_2": "example_2",
            "invalid_3": "example_3"
        }
        response = client.put('/app', json=body)

        expected_response = expected_response_function(config_sample_path)
        expected_response_2 = expected_response_default()

        assert response.status_code == 200
        assert response.json() == expected_response
        assert response.json() == expected_response_2

    # pytest -v api/tests/app/test_app.py::TestClassUpdateAppConfig::test_try_change_app_config_empty_json
    def test_try_change_app_config_empty_json(self, config_rollback):
        client, config_sample_path = config_rollback

        body = {}
        response = client.put('/app', json=body)

        expected_response = expected_response_function(config_sample_path)
        expected_response_2 = expected_response_default()

        assert response.status_code == 200
        assert response.json() == expected_response
        assert response.json() == expected_response_2
