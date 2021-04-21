import pytest
import re
import os
import json
from copy import deepcopy

from starlette.exceptions import HTTPException
from fastapi import status

from api.models.occupancy_rule import OccupancyRuleListDTO
from api.tests.utils.common_functions import get_config_file_json
from constants import ALL_AREAS
from libs.utils import config as config_utils
from api.utils import get_config
# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback_areas, rollback_area_all_json


def get_area_occupancy_rules(area_id):
    config = get_config()
    areas = config.get_areas()
    area = next((area for area in areas if area.id == area_id), None)
    if not area:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The area: {area_id} does not exist")
    area_config_path = area.get_config_path()

    if not os.path.exists(area_config_path):
        return OccupancyRuleListDTO.parse_obj([]).__root__

    with open(area_config_path, "r") as area_file:
        rules_data = json.load(area_file)
    return OccupancyRuleListDTO.from_store_json(rules_data)


def to_boolean_if_possible(dictionary):
    result = {}
    for key, value in dictionary.items():
        if value in ["false", "true", "False", "True"]:
            if value in ["false", "False"]:
                value = False
            else:
                value = True
        result[key] = value
    return result


def expected_response(config_sample_path):
    config_directory = config_utils.get_area_config_directory(get_config())
    config_path = os.path.join(config_directory, ALL_AREAS + ".json")

    with open(config_path, "r") as file:
        json_content_from_file = json.load(file)["global_area_all"]

    response = {re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower(): value for key, value in json_content_from_file.items()}

    cameras = ",".join(str(value["id"]) for key, value in
                       get_config_file_json(config_sample_path).items() if key.startswith("source__"))

    response["cameras"] = cameras
    response["occupancy_rules"] = get_area_occupancy_rules(ALL_AREAS)

    response = to_boolean_if_possible(response)

    return response


# pytest -v api/tests/app/test_area_all.py::TestsGetAreaAll
class TestsGetAreaAll:
    """ Returns the Area "ALL", an area that contains all cameras.  GET /areas/{ALL_AREAS} """

    def test_get_area_all(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas

        response = client.get(f"/areas/{ALL_AREAS}")

        assert response.status_code == 200
        assert response.json() == expected_response(config_sample_path)


DEFAULT_VALUES_AREA_CONFIG_DTO = {
    'violation_threshold': 0, 'notify_every_minutes': 0, 'emails': '', 'enable_slack_notifications': False,
    'daily_report': False, 'daily_report_time': '06:00', 'occupancy_threshold': 0, 'occupancy_rules': []
}


# pytest -v api/tests/app/test_area_all.py::TestsModifyAreaAll
class TestsModifyAreaAll:
    """Edits the configuration related to the area "ALL", an area that contains all cameras.  PUT /areas/{ALL_AREAS}"""

    def test_edit_area_all_file_properly(self, config_rollback_areas, rollback_area_all_json):
        area, area_2, client, config_sample_path = config_rollback_areas
        body = {
            "violation_threshold": 100,
            "notify_every_minutes": 15,
            "emails": "john@email.com,doe@email.com",
            "enable_slack_notifications": False,
            "daily_report": True,
            "daily_report_time": "06:00",
            "occupancy_threshold": 300,
            "name": "example",  # name is a required field, but will be ignored.
        }
        response = client.put(f"/areas/{ALL_AREAS}", json=body)

        assert response.json()["id"] == ALL_AREAS
        assert response.json()["name"] == ALL_AREAS
        assert response.json()["cameras"] == expected_response(config_sample_path)["cameras"]
        assert response.json() == expected_response(config_sample_path)

    def test_edit_area_all_file_no_body(self, config_rollback_areas, rollback_area_all_json):
        area, area_2, client, config_sample_path = config_rollback_areas
        body = {
            "name": "example"  # name is a required field, but will be ignored.
        }
        response = client.put(f"/areas/{ALL_AREAS}", json=body)

        assert response.status_code == 200
        expected_default_response = deepcopy(DEFAULT_VALUES_AREA_CONFIG_DTO)
        expected_default_response["id"] = ALL_AREAS
        expected_default_response["name"] = ALL_AREAS
        expected_default_response["cameras"] = expected_response(config_sample_path)["cameras"]
        assert response.json() == expected_default_response

    def test_edit_area_all_file_send_extra_parameters(self, config_rollback_areas, rollback_area_all_json):
        """Cameras key must be ignored"""
        area, area_2, client, config_sample_path = config_rollback_areas
        body = {
            "violation_threshold": 100,
            "notify_every_minutes": 15,
            "emails": "john@email.com,doe@email.com",
            "enable_slack_notifications": False,
            "daily_report": True,
            "daily_report_time": "06:00",
            "occupancy_threshold": 300,
            "id": "0",
            "name": "Kitchen", # name is a required field, but will be ignored.
        }
        response = client.put(f"/areas/{ALL_AREAS}", json=body)

        assert response.status_code == 200
        assert response.json()["id"] == ALL_AREAS
        assert response.json()["name"] == ALL_AREAS
        assert response.json() == expected_response(config_sample_path)

    @pytest.mark.parametrize("key_value_dict, status_code", [
        ({"violation_threshold": True}, 200),
        ({"violation_threshold": "True"}, 400),
        ({"violation_threshold": "true"}, 400),
        ({"violation_threshold": 22.5}, 200),
        ({"violation_threshold": "HI"}, 400),
        ({"violation_threshold": "100"}, 200),
        ({"violation_threshold": 40}, 200),
        ({"violation_threshold": -40}, 200),
        ({"notify_every_minutes": True}, 200),
        ({"notify_every_minutes": 22.5}, 200),
        ({"notify_every_minutes": "HI"}, 400),
        ({"notify_every_minutes": "100"}, 200),
        ({"notify_every_minutes": 40}, 200),
        ({"notify_every_minutes": -40}, 200),
        ({"emails": True}, 200),
        ({"emails": 22.5}, 200),
        ({"emails": "HI"}, 200),
        ({"emails": "100"}, 200),
        ({"emails": 40}, 200),
        ({"emails": -40}, 200),
        ({"enable_slack_notifications": True}, 200),
        ({"enable_slack_notifications": 22.5}, 400),
        ({"enable_slack_notifications": "HI"}, 400),
        ({"enable_slack_notifications": "false"}, 200),
        ({"enable_slack_notifications": "False"}, 200),
        ({"enable_slack_notifications": 40}, 400),
        ({"enable_slack_notifications": -40}, 400),
        ({"daily_report": True}, 200),
        ({"daily_report": 22.5}, 400),
        ({"daily_report": "HI"}, 400),
        ({"daily_report": "false"}, 200),
        ({"daily_report": "False"}, 200),
        ({"daily_report": 40}, 400),
        ({"daily_report": -40}, 400),
        ({"daily_report_time": True}, 200),
        ({"daily_report_time": 22.5}, 200),
        ({"daily_report_time": "HI"}, 200),
        ({"daily_report_time": "100"}, 200),
        ({"daily_report_time": 40}, 200),
        ({"daily_report_time": -40}, 200),
        ({"occupancy_threshold": True}, 200),
        ({"occupancy_threshold": 22.5}, 200),
        ({"occupancy_threshold": "HI"}, 400),
        ({"occupancy_threshold": "100"}, 200),
        ({"occupancy_threshold": 40}, 200),
        ({"occupancy_threshold": -40}, 200),
        # We have to add occupancy rules...
    ])
    def test_try_edit_area_all_file_several_formats(self, config_rollback_areas, rollback_area_all_json,
                                                           key_value_dict, status_code):
        area, area_2, client, config_sample_path = config_rollback_areas
        body = {
            "name": "example"  # name is a required field, but will be ignored.
        }
        body.update(key_value_dict)
        response = client.put(f"/areas/{ALL_AREAS}", json=body)

        assert response.status_code == status_code


# pytest -v api/tests/app/test_area_all.py::TestsGetAndModifyAreaAll
class TestsGetAndModifyAreaAll:
    """Integration test:"""
    """
    Edit and Get the configuration related to the area "ALL", an area that contains all cameras.
    Combination of:
        PUT /areas/{ALL_AREAS}
        GET /areas/{ALL_AREAS}
    """
    
    def test_get_and_edit_area_all_file_several_cases(self, config_rollback_areas, rollback_area_all_json):
        area, area_2, client, config_sample_path = config_rollback_areas

        # We first check if /GET response is correct.
        response_1 = client.get(f"/areas/{ALL_AREAS}")
        assert response_1.status_code == 200
        assert response_1.json() == expected_response(config_sample_path)

        # we check if the endpoint is idempotent.
        response_2 = client.get(f"/areas/{ALL_AREAS}")
        assert response_2.status_code == 200
        assert response_2.json() == response_1.json()

        # Let's try the edit endpoint for the first time
        body = {
            "violation_threshold": 100,
            "notify_every_minutes": 15,
            "emails": "john@email.com,doe@email.com",
            "enable_slack_notifications": False,
            "daily_report": True,
            "daily_report_time": "06:00",
            "occupancy_threshold": 300,
            "name": "example"  # name is a required field, but will be ignored.
        }
        response_3 = client.put(f"/areas/{ALL_AREAS}", json=body)
        assert response_3.status_code == 200
        assert response_3.json()["id"] == ALL_AREAS
        assert response_3.json()["name"] == ALL_AREAS
        assert response_3.json()["cameras"] == expected_response(config_sample_path)["cameras"]
        assert response_3.json() == expected_response(config_sample_path)

        # We validate that the endpoint /GET returns the modified values in response_3
        response_4 = client.get(f"/areas/{ALL_AREAS}")
        assert response_4.status_code == 200
        assert response_4.json() == expected_response(config_sample_path)
        assert response_4.json() == response_3.json()

        # Let's modify the file twice
        body = {
            "violation_threshold": 50,
            "notify_every_minutes": 20,
            "emails": "new_email@email.com,new_email_two@email.com",
            "enable_slack_notifications": True,
            "daily_report": False,
            "daily_report_time": "05:40",
            "occupancy_threshold": 250,
            "name": "example"  # name is a required field, but will be ignored.
        }
        client.put(f"/areas/{ALL_AREAS}", json=body)
        response_5 = client.put(f"/areas/{ALL_AREAS}", json=body)
        assert response_5.status_code == 200
        assert response_5.json() == expected_response(config_sample_path)

        # We validate that the endpoint /GET returns the modified values again
        response_6 = client.get(f"/areas/{ALL_AREAS}")
        assert response_6.status_code == 200
        assert response_6.json() == expected_response(config_sample_path)

        # Finally, we will incorrectly call the endpoint /PUT. Nothing should change
        body = {
            "occupancy_threshold": "Unacceptable value",
            "name": "example"  # name is a required field, but will be ignored.
        }
        response_7 = client.put(f"/areas/{ALL_AREAS}", json=body)
        assert response_7.status_code == 400

        # Once again, nothing should change because we do not send required fields "cameras" and "name".
        body = {}
        response_8 = client.put(f"/areas/{ALL_AREAS}", json=body)
        assert response_8.status_code == 400

        # We verify that nothing has changed and the answer is the same as in the previous steps.
        response_9 = client.get(f"/areas/{ALL_AREAS}")
        assert response_9.status_code == 200
        assert response_9.json() == response_6.json()
        assert response_9.json() == response_5.json()
