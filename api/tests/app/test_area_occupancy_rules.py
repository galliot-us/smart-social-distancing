import pytest
from copy import deepcopy

# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback_areas

class TestsOccupancyRules:
    """ LIVE """
    """ Get Area Occupancy Rules, GET /areas/occupancy-rules/:id """
    """ Set Area Occupancy Rules, PUT /areas/occupancy-rules/:id """
    """ Delete Area Occupancy Rules, DELETE /areas/occupancy-rules/:id """

    base_data = [
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
    ]

    def test_set_correct_area_occupancy_rules(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        response = client.put(f"/areas/occupancy-rules/{area_id}", json=self.base_data)

        assert response.status_code == 201
        res = response.json()
        assert len(self.base_data) == len(res)
        for key in self.base_data[0].keys():
            assert key in res[0]
            assert res[0][key] == self.base_data[0][key]

    def test_unitary_set_get_delete(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        set_response = client.put(f"/areas/occupancy-rules/{area_id}", json=self.base_data)
        get_response = client.get(f"/areas/occupancy-rules/{area_id}")
        delete_response = client.delete(f"/areas/occupancy-rules/{area_id}")

        assert set_response.status_code == 201
        assert get_response.status_code == 200
        assert delete_response.status_code == 204

        assert set_response.json() == get_response.json()


    def test_set_invalid_threshold(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data[0]["max_occupancy"] = -1
        response = client.put(f"/areas/occupancy-rules/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_invalid_start_hour(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data[0]["start_hour"] = "24:60"
        response = client.put(f"/areas/occupancy-rules/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_invalid_start_finish_hour(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data[0]["start_hour"] = "23:00"
        data[0]["finish_hour"] = "22:00"
        response = client.put(f"/areas/occupancy-rules/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_overlap_complete(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data[0]["start_hour"] = "12:00"
        data[0]["finish_hour"] = "22:00"
        data[1]["start_hour"] = "14:00"
        data[1]["finish_hour"] = "20:00"
        response = client.put(f"/areas/occupancy-rules/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_overlap_start(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data[0]["start_hour"] = "12:00"
        data[0]["finish_hour"] = "22:00"
        data[1]["start_hour"] = "10:00"
        data[1]["finish_hour"] = "20:00"
        response = client.put(f"/areas/occupancy-rules/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_overlap_end(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data[0]["start_hour"] = "12:00"
        data[0]["finish_hour"] = "22:00"
        data[1]["start_hour"] = "20:00"
        data[1]["finish_hour"] = "23:00"
        response = client.put(f"/areas/occupancy-rules/{area_id}", json=data)

        assert response.status_code == 400

    def test_set_contiguous(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data[0]["start_hour"] = "12:00"
        data[0]["finish_hour"] = "22:00"
        data[1]["start_hour"] = "22:00"
        data[1]["finish_hour"] = "23:00"
        response = client.put(f"/areas/occupancy-rules/{area_id}", json=data)

        assert response.status_code == 201

    def test_set_wrong_days(self, config_rollback_areas):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        data = deepcopy(self.base_data)
        data[0]["days"] = [True, False, True, False, True] # should be 7
        response = client.put(f"/areas/occupancy-rules/{area_id}", json=data)

        assert response.status_code == 400
