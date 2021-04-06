import pytest

from api.tests.utils.common_functions import get_config_file_json, app_config_file_multi_type_json_to_string_json
# The line below is absolutely necessary. Fixtures are passed as arguments to test functions.
# This is why the IDE cannot recognize them.
from api.tests.utils.fixtures_tests import config_rollback


def expected_response_update_report_info(config_sample_path):
    app_config = get_config_file_json(config_sample_path)
    expected_response = app_config_file_multi_type_json_to_string_json(app_config)

    expected_response["app"]["has_been_configured"] = "False"
    return expected_response


def body_without_app_field(client):
    response_get_config = client.get("/config")
    body = response_get_config.json()
    del body["app"]
    return body


# pytest -v api/tests/app/test_config.py::TestsGetProcessorInfo
class TestsGetProcessorInfo:
    """Get Config File, GET /config/info"""

    def test_get_processor_info(self, config_rollback):
        """I dont get why has been configured is True"""
        client, config_sample_path = config_rollback

        response = client.get("/config/info")

        # Expected response
        config = get_config_file_json(config_sample_path)

        has_been_configured = bool(config["app"]["has_been_configured"])

        device = config["detector"]["device"]
        if config["detector"]["name"] == "openvino":
            device += "-openvino"

        from constants import PROCESSOR_VERSION

        expected_response = {
            "version": PROCESSOR_VERSION,
            "device": device,
            "has_been_configured": has_been_configured,
            "metrics": {
                "social_distancing": True,
                "facemask": False,
                "occupancy": True,
                "in_out": True,
            }
        }

        assert response.status_code == 200
        assert response.json() == expected_response


# pytest -v api/tests/app/test_config.py::TestsGetConfigFile
class TestsGetConfigFile:
    """Get Config File, GET /config"""

    def test_get_config_file(self, config_rollback):
        client, config_sample_path = config_rollback

        response = client.get("/config")

        assert response.status_code == 200


# pytest -v api/tests/app/test_config.py::TestsGetReportInfo
class TestsGetReportInfo:
    """Get Report Info, GET /config/global_report"""

    def test_get_global_report(self, config_rollback):
        client, config_sample_path = config_rollback

        response = client.get("/config/global_report")

        config = get_config_file_json(config_sample_path)
        app_config = config["app"]
        expected_response = {
            "emails": app_config["global_reporting_emails"],
            "time": app_config["global_report_time"],
            "daily": app_config["daily_global_report"],
            "weekly": app_config["weekly_global_report"]
        }

        assert response.status_code == 200
        assert response.json() == expected_response


# pytest -v api/tests/app/test_config.py::TestsUpdateConfigFile
class TestsUpdateConfigFile:
    """Get Report Info, PUT /config"""

    def test_update_config_file_properly(self, config_rollback):
        client, config_sample_path = config_rollback

        response_get_config = client.get("/config")

        response = client.put("/config", json=response_get_config.json())

        assert response.status_code == 200

    def test_try_update_config_file_bad_request_I(self, config_rollback):
        """Empty request body"""
        client, config_sample_path = config_rollback

        body = body_without_app_field(client)

        response = client.put("/config", json=body)

        assert response.status_code == 400
        assert response.json()["detail"][0]["type"] == "value_error.missing"

    def test_try_update_config_file_bad_request_II(self, config_rollback):
        """App filed with a string instead of a dict"""
        client, config_sample_path = config_rollback

        body = body_without_app_field(client)
        body["app"] = "Here should be a dict instead of string"

        response = client.put("/config", json=body)

        assert response.status_code == 400
        assert response.json()["detail"][0]["type"] == "type_error.dict"


# pytest -v api/tests/app/test_config.py::TestsUpdateReportInfo
class TestsUpdateReportInfo:
    """Update Report Info, PUT /config/global_report"""

    def test_update_report_info_properly(self, config_rollback):
        client, config_sample_path = config_rollback

        body = {
            "emails": "john@email.com,doe@email.com",
            "time": "0:00",
            "daily": True,
            "weekly": True
        }

        response = client.put("/config/global_report", json=body)

        expected_response = expected_response_update_report_info(config_sample_path)

        assert response.status_code == 200
        assert response.json() == expected_response
        assert expected_response["app"]["global_reporting_emails"] == "john@email.com,doe@email.com"
        assert expected_response["app"]["global_report_time"] == "0:00"
        assert expected_response["app"]["daily_global_report"] == "True"
        assert expected_response["app"]["weekly_global_report"] == "True"

    def test_try_update_report_info_invalid_keys(self, config_rollback):
        """Here, as no valid key was sent, PUT request was processed with the example values from models/config
        GlobalReportingEmailsInfo """
        client, config_sample_path = config_rollback

        body = {
            "invalid_1": "example_1",
            "invalid_2": "example_2",
            "invalid_3": "example_3"
        }

        response = client.put("/config/global_report", json=body)

        expected_response = expected_response_update_report_info(config_sample_path)

        assert response.status_code == 200
        assert response.json() == expected_response

    def test_try_update_report_info_empty_request_body(self, config_rollback):
        """Here, as no valid key was sended, PUT request was finished with the example values from models/config
        GlobalReportingEmailsInfo """
        client, config_sample_path = config_rollback

        body = {}

        response = client.put("/config/global_report", json=body)

        expected_response = expected_response_update_report_info(config_sample_path)

        assert response.status_code == 200
        assert response.json() == expected_response

    def test_try_update_report_info_wrong_variable_type_I(self, config_rollback):
        client, config_sample_path = config_rollback

        body = {
            "emails": "string",
            "time": "string",
            "daily": 40,
            "weekly": 40
        }

        response = client.put("/config/global_report", json=body)

        assert response.status_code == 400
        assert response.json()["detail"][0]["type"] == "type_error.bool"

    def test_try_update_report_info_wrong_variable_type_II(self, config_rollback):
        client, config_sample_path = config_rollback

        body = {
            "emails": 40,  # Here, a string should be sent
            "time": True,  # Here, a string should be sent
            "daily": False,
            "weekly": True
        }

        response = client.put("/config/global_report", json=body)

        expected_response = expected_response_update_report_info(config_sample_path)

        assert response.status_code == 200
        assert response.json() == expected_response
        assert expected_response["app"]["global_reporting_emails"] == "40"
        assert expected_response["app"]["global_report_time"] == "True"
        assert expected_response["app"]["daily_global_report"] == "False"
        assert expected_response["app"]["weekly_global_report"] == "True"
