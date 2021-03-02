import datetime
import pytest
from freezegun import freeze_time
import numpy as np
# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback_create_cameras, heatmap_simulation, config_rollback, \
    reports_simulation

# TODO: avisar que en: GET /metrics/cameras/social-distancing/live, el texto del costado esta mal

# config_rollback_create_areas = 1, 2, 3, 4


# pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsLive
class TestsGetMetricsLive:
    """ LIVE """
    """ Get Area Occupancy Live, GET /metrics/cameras/occupancy/live """
    """ Get Area Distancing Live Report, GET /metrics/cameras/social-distancing/live """
    """ Get Camera Face Mask Detections Live, GET /metrics/cameras/face-mask-detections/live """

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_get_a_report_properly(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']

        response = client.get(f"/metrics/areas/{metric}/live?area={area_id}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_no_areas(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas

        response = client.get(f"/metrics/areas/{metric}/live?area=")

        assert response.status_code == 400
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_no_query_string(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas

        response = client.get(f"/metrics/areas/{metric}/live")

        assert response.status_code == 400
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_bad_id(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = 'BAD_ID'

        response = client.get(f"/metrics/areas/{metric}/live?area={area_id}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_non_existent_id(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        # Area with ID 4564 does not exist
        area_id = 4564

        response = client.get(f"/metrics/areas/{metric}/live?area={area_id}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_get_a_report_properly_two_areas(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id_1 = area['id']
        area_id_2 = area_2['id']

        response = client.get(f"/metrics/areas/{metric}/live?area={area_id_1},{area_id_2}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_for_two_areas_one_non_existent_id(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id_1 = area['id']
        area_id_2 = 'non_existent_id'

        response = client.get(f"/metrics/areas/{metric}/live?area={area_id_1},{area_id_2}")

        assert response.status_code == 200
        assert response.json() == expected


# pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsLive
class TestsGetMetricsHourly:
    """ HOURLY """
    """ Get Area Occupancy Hourly Report, GET /metrics/cameras/occupancy/hourly """
    """ Get Area Distancing Hourly Report, GET /metrics/cameras/social-distancing/hourly """
    """ Get Camera Face Mask Detections Hourly Report, GET /metrics/cameras/face-mask-detections/hourly """

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_get_a_report_properly(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']
        date = "2021-03-01"

        response = client.get(f"/metrics/areas/{metric}/hourly?area={area_id}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_no_query_string(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas

        response = client.get(f"/metrics/areas/{metric}/hourly")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_empty_area(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        date = "2021-03-01"

        response = client.get(f"/metrics/areas/{metric}/hourly?area=&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_several_dates(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']
        date_1 = "2021-03-01"
        date_2 = "2021-03-02"

        response = client.get(f"/metrics/areas/{metric}/hourly?area={area_id}&date={date_1},{date_2}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_no_date_on_query_string(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']

        response = client.get(f"/metrics/areas/{metric}/hourly?area={area_id}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_empty_date(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']

        response = client.get(f"/metrics/areas/{metric}/hourly?area={area_id}&date=")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_bad_format_date(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']
        date = "BAD_DATE"

        response = client.get(f"/metrics/areas/{metric}/hourly?area={area_id}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_non_existent_date(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']
        date = "2009-03-01"  # No data for this date

        response = client.get(f"/metrics/areas/{metric}/hourly?area={area_id}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_bad_id(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = 'BAD_ID'
        date = "2021-03-01"

        response = client.get(f"/metrics/areas/{metric}/hourly?area={area_id}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_get_a_report_several_ids(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']
        area_id_2 = area_2['id']
        date = "2021-03-01"

        response = client.get(f"/metrics/areas/{metric}/hourly?area={area_id},{area_id_2}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_several_ids_one_bad_id(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']
        area_id_2 = "BAD_ID"
        date = "2021-03-01"

        response = client.get(f"/metrics/areas/{metric}/hourly?area={area_id},{area_id_2}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_several_ids_one_no_report_for_given_date(self, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']
        area_id_2 = 43  # Hay que crear una id valida, pero que no tenga fecha
        date = "2021-03-01"

        response = client.get(f"/metrics/areas/{metric}/hourly?area={area_id},{area_id_2}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected


# pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsDaily
class TestsGetMetricsDaily:
    """ DAILY """
    """ Get Area Occupancy Daily Report, GET /metrics/cameras/occupancy/daily """
    """ Get Area Distancing Daily Report, GET /metrics/cameras/social-distancing/daily """
    """ Get Camera Face Mask Detections Daily Report, GET /metrics/cameras/face-mask-detections/daily """

    def test_create_area(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path_to_modify = config_rollback_create_cameras
        body = {
            "violation_threshold": 100,
            "notify_every_minutes": 15,
            "emails": "john@email.com,doe@email.com",
            "enable_slack_notifications": False,
            "daily_report": True,
            "daily_report_time": "06:00",
            "occupancy_threshold": 300,
            "id": "5",
            "name": "Kitchen",
            "cameras": "49,50"
        }
        created_area = client.post("/areas", json=body).json()
        area_id = created_area['id']
        date = "2021-03-01"

        # La info sale de los distintos reports.csv, de las camaras si la metric es FACEMASK o SOCIALDISTANCING, y de areas si es OCCUPANCY.
        # Un area tiene camaras, si es FACEMASK o SOCIALDISTANCING, se va a buscar a los reportes de las camaras.
        response = client.get(f"/metrics/areas/social-distancing/daily?areas={area_id}&from_date=2020-09-06&to_date=2020-09-09")

        """
        2020-09-06,0,0,0,0,0
        2020-09-07,0,0,0,0,0
        2020-09-08,148,136,0,5,7
        2020-09-09,179,139,19,17,4
        """
