import pytest

from api.tests.utils.common_functions import get_config_file_json, app_config_file_multi_type_json_to_string_json
# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback, app_config


def expected_response_update_report_info(config_sample_path):
    app_config = get_config_file_json(config_sample_path)
    expected_response = app_config_file_multi_type_json_to_string_json(app_config)
    expected_response['app']['has_been_configured'] = 'False'
    return expected_response


# pytest -v api/tests/app/test_config.py::TestClassGetProcessorInfo
class TestClassGetProcessorInfo:
    """Get Config File, GET /config/info"""

    def test_get_processor_info(self, config_rollback):
        """I dont get why has been configured is True"""
        client, config_sample_path = config_rollback

        response = client.get('/config/info')

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
            "has_been_configured": has_been_configured
        }

        assert response.status_code == 200
        assert response.json() == expected_response


# pytest -v api/tests/app/test_config.py::TestClassGetConfigFile
class TestClassGetConfigFile:
    """Get Config File, GET /config"""

    def test_get_config_file(self, config_rollback):
        """INTERNAL SERVER ERROR 500"""
        client, config_sample_path = config_rollback

        response = client.get('/config')

        expected_response = get_config_file_json(config_sample_path)

        assert response.status_code == 200
        assert response.json() == expected_response


# pytest -v api/tests/app/test_config.py::TestClassGetReportInfo
class TestClassGetReportInfo:
    """Get Report Info, GET /config/global_report"""

    def test_get_config_file(self, config_rollback):
        client, config_sample_path = config_rollback

        response = client.get('/config/global_report')

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


# pytest -v api/tests/app/test_config.py::TestClassUpdateConfigFile
class TestClassUpdateConfigFile:
    """Get Report Info, PUT /config"""

    def test_update_config_file_properly(self, config_rollback):
        """Bad Request with the example"""
        client, config_sample_path = config_rollback

        body = {
            "app": {
                "has_been_configured": False,
                "resolution": "string",
                "encoder": "string",
                "max_processes": 0,
                "dashboardurl": "string",
                "screenshots_directory": "/repo/data/processor/static/screenshots",
                "slack_channel": "lanthorn-notifications",
                "occupancy_alerts_min_interval": 180,
                "max_thread_restarts": 0,
                "global_reporting_emails": "email@email,email2@email",
                "global_report_time": "string",
                "daily_global_report": False,
                "weekly_global_report": False,
                "heatmap_resolution": "string"
            },
            "api": {
                "host": "string",
                "port": 0,
                "ssl_enabled": False,
                "ssl_certificate_file": "/repo/certs/0_0_0_0.crt",
                "ssl_key_file": "/repo/certs/0_0_0_0.key"
            },
            "core": {
                "host": "0.0.0.0",
                "queue_port": "8010",
                "queue_auth_key": "shibalba"
            },
            "cameras": [
                {
                    "violation_threshold": 100,
                    "notify_every_minutes": 15,
                    "emails": "john@email.com,doe@email.com",
                    "enable_slack_notifications": False,
                    "daily_report": True,
                    "daily_report_time": "06:00",
                    "id": "0",
                    "name": "Kitchen",
                    "video_path": "/repo/data/softbio_vid.mp4",
                    "tags": "kitchen,living_room",
                    "image": "Base64 image",
                    "dist_method": "CenterPointsDistance"
                }
            ],
            "areas": [
                {
                    "violation_threshold": 100,
                    "notify_every_minutes": 15,
                    "emails": "john@email.com,doe@email.com",
                    "enable_slack_notifications": False,
                    "daily_report": True,
                    "daily_report_time": "06:00",
                    "occupancy_threshold": 300,
                    "id": "0",
                    "name": "Kitchen",
                    "cameras": "cam0,cam1"
                }
            ],
            "detector": {
                "device": "EdgeTPU",
                "name": "posenet",
                "image_size": "641,481,3",
                "model_path": "/repo/data/custom-model",
                "classid": 0,
                "min_score": 0.5
            },
            "classifier": {
                "device": "EdgeTPU",
                "name": "OFMClassifier",
                "image_size": "45,45,3",
                "model_path": "/repo/data/custom-model",
                "min_score": 0.5
            },
            "tracker": {
                "name": "IOUTracker",
                "max_lost": 5,
                "tracker_iou_threshold": 0.5
            },
            "source_post_processors": [
                {
                    "name": "objects_filtering",
                    "enabled": True,
                    "nms_threshold": 0.98,
                    "default_dist_method": "CenterPointsDistance",
                    "dist_threshold": 150
                }
            ],
            "source_loggers": [
                {
                    "name": "objects_filtering",
                    "enabled": True,
                    "screenshot_period": 0,
                    "screenshot_s3bucket": "my-screenshot-bucket",
                    "time_interval": 0.5,
                    "log_directory": "/repo/data/processor/static/data/sources",
                    "endpoint": "https://my-endpoint/"
                }
            ],
            "area_loggers": [
                {
                    "name": "objects_filtering",
                    "enabled": True,
                    "log_directory": "/repo/data/processor/static/data/areas"
                }
            ],
            "periodic_tasks": [
                {
                    "name": "objects_filtering",
                    "enabled": True
                }
            ]
        }
        response = client.put('/config', json=body)

        import pdb
        pdb.set_trace()
        assert response.status_code == 200
        # assert response.json() == expected_response


# pytest -v api/tests/app/test_config.py::TestClassUpdateReportInfo
class TestClassUpdateReportInfo:
    """Update Report Info, PUT /config/global_report"""

    def test_update_report_info_properly(self, config_rollback):
        client, config_sample_path = config_rollback

        body = {
            "emails": "john@email.com,doe@email.com",
            "time": "0:00",
            "daily": True,
            "weekly": True
        }

        response = client.put('/config/global_report', json=body)

        expected_response = expected_response_update_report_info(config_sample_path)

        assert response.status_code == 200
        assert response.json() == expected_response
        assert expected_response['app']['global_reporting_emails'] == "john@email.com,doe@email.com"
        assert expected_response['app']['global_report_time'] == "0:00"
        assert expected_response['app']['daily_global_report'] == "True"
        assert expected_response['app']['weekly_global_report'] == "True"

    def test_try_update_report_info_invalid_keys(self, config_rollback):
        """Here, as no valid key was sent, PUT request was processed with the example values from models/config
        GlobalReportingEmailsInfo """
        client, config_sample_path = config_rollback

        body = {
            "invalid_1": "example_1",
            "invalid_2": "example_2",
            "invalid_3": "example_3"
        }

        response = client.put('/config/global_report', json=body)

        expected_response = expected_response_update_report_info(config_sample_path)

        assert response.status_code == 200
        assert response.json() == expected_response

    def test_try_update_report_info_empty_request_body(self, config_rollback):
        """Here, as no valid key was sended, PUT request was finished with the example values from models/config
        GlobalReportingEmailsInfo """
        client, config_sample_path = config_rollback

        body = {}

        response = client.put('/config/global_report', json=body)

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

        response = client.put('/config/global_report', json=body)

        expected_response = expected_response_update_report_info(config_sample_path)

        assert response.status_code == 400
        assert response.json()['detail'][0]['type'] == 'type_error.bool'

    def test_try_update_report_info_wrong_variable_type_II(self, config_rollback):
        client, config_sample_path = config_rollback

        body = {
            "emails": 40,  # Here, a string should be sent
            "time": True,  # Here, a string should be sent
            "daily": False,
            "weekly": True
        }

        response = client.put('/config/global_report', json=body)

        expected_response = expected_response_update_report_info(config_sample_path)

        assert response.status_code == 200
        assert response.json() == expected_response
        assert expected_response['app']['global_reporting_emails'] == "40"
        assert expected_response['app']['global_report_time'] == "True"
        assert expected_response['app']['daily_global_report'] == "False"
        assert expected_response['app']['weekly_global_report'] == "True"
