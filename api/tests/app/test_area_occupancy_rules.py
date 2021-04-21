import pytest
import os
from copy import deepcopy

from api.utils import get_config
from libs.utils import config as config_utils

# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback_areas, rollback_area_config_path


def rollback_area_config_file(area_id):
    """area_id must be an string"""
    config_directory = config_utils.get_area_config_directory(get_config())
    config_path = os.path.join(config_directory, area_id + ".json")
    if os.path.exists(config_path):
        os.remove(config_path)


# pytest -v api/tests/app/test_area_occupancy_rules.py::TestsOccupancyRules
class TestsOccupancyRules:
    """ LIVE """
    """ Get Area Occupancy Rules, GET /areas/occupancy-rules/:id """
    """ Set Area Occupancy Rules, PUT /areas/occupancy-rules/:id """
    """ Delete Area Occupancy Rules, DELETE /areas/occupancy-rules/:id """
    
    base_data = {"occupancy_rules":
        [
            {
                "days": [True, True, False, False, False, True, True],
                "start_hour":"12:00",
                "finish_hour":"00:00",
                "max_occupancy":12
            }, {
                "days": [True, True, False, False, False, True, True],
                "start_hour":"00:00",
                "finish_hour":"11:00",
                "max_occupancy":11
            }
        ],
        "id": 5,
        "name": "Kitchen",
        "cameras": "0"
    }

    def test_set_correct_area_occupancy_rules(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data["id"] = area_id
        response = client.put(f"/areas/{area_id}", json=data)

        assert response.status_code == 200

    def test_unitary_set_get_delete(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = 537

        data = deepcopy(self.base_data)
        data["id"] = area_id
        post_response = client.post(f"/areas", json=data)
        get_response1 = client.get(f"/areas/{area_id}")
        data["occupancy_rules"][0]["max_occupancy"] = 100
        put_response = client.put(f"/areas/{area_id}", json=data)
        get_response2 = client.get(f"/areas/{area_id}")
        delete_response = client.delete(f"/areas/{area_id}")
        get_response3 = client.get(f"/areas/{area_id}")

        assert post_response.status_code == 201
        assert put_response.status_code == 200
        assert get_response1.status_code == 200
        assert get_response2.status_code == 200
        assert delete_response.status_code == 204
        assert get_response3.status_code == 404

        res1 = get_response1.json()
        res2 = get_response2.json()
        assert res1 != res2
        assert res1["occupancy_rules"][0]["max_occupancy"] == 12
        assert res2["occupancy_rules"][0]["max_occupancy"] == 100

        rollback_area_config_file(str(area_id))

    def test_get_not_found(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = 404

        get_response = client.get(f"/areas/{area_id}")

        assert get_response.status_code == 404

    def test_get_empty(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = 5

        data = deepcopy(self.base_data)
        data["id"] = area_id
        data["occupancy_rules"] = []
        response = client.put(f"/areas/{area_id}", json=data)
        get_response = client.get(f"/areas/{area_id}")

        assert get_response.status_code == 200
        assert get_response.json()["occupancy_rules"] == []

    def test_set_invalid_threshold(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data["occupancy_rules"][0]["max_occupancy"] = -1
        response = client.put(f"/areas/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_invalid_start_hour(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data["occupancy_rules"][0]["start_hour"] = "24:60"
        response = client.put(f"/areas/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_invalid_start_finish_hour(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data["occupancy_rules"][0]["start_hour"] = "23:00"
        data["occupancy_rules"][0]["finish_hour"] = "22:00"
        response = client.put(f"/areas/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_overlap_complete(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data["occupancy_rules"][0]["start_hour"] = "12:00"
        data["occupancy_rules"][0]["finish_hour"] = "22:00"
        data["occupancy_rules"][1]["start_hour"] = "14:00"
        data["occupancy_rules"][1]["finish_hour"] = "20:00"
        response = client.put(f"/areas/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_overlap_start(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data["occupancy_rules"][0]["start_hour"] = "12:00"
        data["occupancy_rules"][0]["finish_hour"] = "22:00"
        data["occupancy_rules"][1]["start_hour"] = "10:00"
        data["occupancy_rules"][1]["finish_hour"] = "20:00"
        response = client.put(f"/areas/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_overlap_end(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data["occupancy_rules"][0]["start_hour"] = "12:00"
        data["occupancy_rules"][0]["finish_hour"] = "22:00"
        data["occupancy_rules"][1]["start_hour"] = "20:00"
        data["occupancy_rules"][1]["finish_hour"] = "23:00"
        response = client.put(f"/areas/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_overlap_zero(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data["occupancy_rules"][0]["start_hour"] = "00:00"
        data["occupancy_rules"][0]["finish_hour"] = "14:00"
        data["occupancy_rules"][1]["start_hour"] = "13:00"
        data["occupancy_rules"][1]["finish_hour"] = "00:00"
        response = client.put(f"/areas/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_contiguous(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data["occupancy_rules"][0]["start_hour"] = "12:00"
        data["occupancy_rules"][0]["finish_hour"] = "22:00"
        data["occupancy_rules"][1]["start_hour"] = "22:00"
        data["occupancy_rules"][1]["finish_hour"] = "23:00"
        response = client.put(f"/areas/{area_id}", json=data)

        assert response.status_code == 200

    def test_set_wrong_days(self, config_rollback_areas, rollback_area_config_path):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data["occupancy_rules"][0]["days"] = [True, False, True, False, True]  # should be 7
        response = client.put(f"/areas/{area_id}", json=data)

        assert response.status_code == 400
