import datetime
import pytest
from freezegun import freeze_time
import numpy as np
# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback_create_cameras, heatmap_simulation, config_rollback, \
    reports_simulation


# TODO: Some endpoint need to give a range of dates, try to send only one date.


# pytest -v api/tests/app/test_camera_metrics.py::TestsGetHeatmap
class TestsGetHeatmap:
    """Get Heatmap, GET /metrics/cameras/{camera_id}/heatmap"""

    def test_get_one_heatmap_properly(self, config_rollback_create_cameras, heatmap_simulation):
        # Make the request
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-19")
        # Get the heatmap
        heatmap_path = f"/repo/data/processor/static/data/sources/{camera_id}/heatmaps/violations_heatmap_2020-09-19.npy"
        heatmap = np.load(heatmap_path).tolist()
        # Compare results
        assert response.status_code == 200
        assert response.json()["heatmap"] == heatmap

    def test_try_get_two_heatmaps(self, config_rollback_create_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-20")
        heatmap_path = f"/repo/data/processor/static/data/sources/{camera_id}/heatmaps/violations_heatmap_2020-09-19.npy"
        heatmap = np.load(heatmap_path).tolist()
        assert response.status_code == 200
        assert response.json()["heatmap"] == heatmap
        assert response.json()["not_found_dates"] == ["2020-09-20"]

    def test_get_two_valid_heatmaps(self, config_rollback_create_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-22")
        heatmap_path_1 = f"/repo/data/processor/static/data/sources/{camera_id}/heatmaps/violations_heatmap_2020-09-19.npy"
        heatmap_path_2 = f"/repo/data/processor/static/data/sources/{camera_id}/heatmaps/violations_heatmap_2020-09-22.npy"
        heatmap_1 = np.load(heatmap_path_1)
        heatmap_2 = np.load(heatmap_path_2)
        final_heatmap = np.add(heatmap_1, heatmap_2).tolist()
        assert response.status_code == 200
        assert response.json()["not_found_dates"] == ['2020-09-20', '2020-09-21']
        assert response.json()['heatmap'] == final_heatmap

    def test_get_one_heatmap_properly_detections(self, config_rollback_create_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-19&report_type=detections")
        heatmap_path = f"/repo/data/processor/static/data/sources/{camera_id}/heatmaps/detections_heatmap_2020-09-19.npy"
        heatmap = np.load(heatmap_path).tolist()
        assert response.status_code == 200
        assert response.json()["heatmap"] == heatmap
        # assert response.json()["not_found_dates"] == ["2020-09-20"]

    def test_try_get_one_heatmap_bad_camera_id(self, config_rollback_create_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = "wrong_id"
        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-19")
        assert response.status_code == 404
        assert response.json() == {'detail': "Camera with id 'wrong_id' does not exist"}

    def test_try_get_one_heatmap_bad_report_type(self, config_rollback_create_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-19&report_type=non_existent_report_type")
        assert response.status_code == 400
        assert response.json() == {'detail': [{'loc': [], 'msg': 'Invalid report_type', 'type': 'invalid config'}]}

    def test_try_get_one_heatmap_bad_dates(self, config_rollback_create_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=today&to_date=tomorrow")
        assert response.status_code == 400
        assert response.json() == {'detail': [{'loc': ['query', 'from_date'], 'msg': 'invalid date format',
                                               'type': 'value_error.date'},
                                              {'loc': ['query', 'to_date'], 'msg': 'invalid date format',
                                               'type': 'value_error.date'}], 'body': None}

    def test_try_get_one_heatmap_wrong_dates(self, config_rollback_create_cameras, heatmap_simulation):
        # TODO: Ask if this behaviour is right. In addition, the returned heatmap is an null square matrix.
        """from_date is after to_date"""
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-20&to_date=2020-09-19")
        assert response.status_code == 200
        assert response.json()['not_found_dates'] == []


# pytest -v api/tests/app/test_camera_metrics.py::TestsGetCameraDistancingLive
class TestsGetCameraDistancingLive:
    """Get Camera Distancing Live, GET /metrics/cameras/social-distancing/live"""
    """Returns a report with live information about the social distancing infractions detected in the cameras ."""

    # TODO: What is the trend attribute in the response?

    def test_get_a_report_properly(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(f"/metrics/cameras/social-distancing/live?cameras={camera_id}")
        assert response.json() == {
            'time': '2021-02-19 13:37:58',
            'trend': 0.05,
            'detected_objects': 6,
            'no_infringement': 5,
            'low_infringement': 0,
            'high_infringement': 1,
            'critical_infringement': 0
        }

    def test_get_a_report_two_valid_cameras(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id_1 = camera["id"]
        camera_id_2 = camera_2["id"]
        response = client.get(f"/metrics/cameras/social-distancing/live?cameras={camera_id_1},{camera_id_2}")
        # TODO: Ask if it is good that values are only added.
        assert response.json() == {
            'time': '2021-02-19 13:37:58',
            'trend': 0.11,
            'detected_objects': 12,
            'no_infringement': 10,
            'low_infringement': 0,
            'high_infringement': 2,
            'critical_infringement': 0
        }

    def test_try_get_a_report_bad_id_camera(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras

        response = client.get(f"/metrics/cameras/social-distancing/live?cameras=BAD_ID")

        assert response.json() == {'detail': "Camera with id 'BAD_ID' does not exist"}
        assert response.status_code == 404


# pytest -v api/tests/app/test_camera_metrics.py::TestsGetCameraDistancingHourlyReport
class TestsGetCameraDistancingHourlyReport:
    """ Get Camera Distancing Hourly Report , GET /metrics/cameras/social-distancing/hourly"""
    """
    Returns a hourly report (for the date specified) with information about 
    the social distancing infractions detected in the cameras .
    """

    def test_get_an_hourly_report_properly(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(f"/metrics/cameras/social-distancing/hourly?cameras={camera_id}&date=2021-02-25")

        assert response.status_code == 200
        assert response.json()['detected_objects'] == [54, 30, 19, 37, 27, 39, 44, 25, 51, 31, 47, 39, 16, 26, 67, 29,
                                                       36, 17, 31, 32, 19, 38, 34, 50]
        assert response.json()['no_infringement'] == [13, 5, 2, 18, 5, 11, 10, 6, 14, 6, 17, 18, 4, 8, 17, 11, 3, 6, 7,
                                                      4, 6, 10, 11, 18]

        assert response.json()['low_infringement'] == [10, 14, 4, 19, 11, 15, 7, 7, 11, 2, 1, 3, 10, 10, 19, 7, 15, 5,
                                                       5, 16, 4, 12, 13, 17]
        assert response.json()['high_infringement'] == [16, 2, 3, 0, 8, 1, 16, 11, 12, 6, 15, 0, 0, 1, 14, 7, 10, 2, 1,
                                                        9, 8, 13, 0, 15]
        assert response.json()['critical_infringement'] == [15, 9, 10, 0, 3, 12, 11, 1, 14, 17, 14, 18, 2, 7, 17, 4, 8,
                                                            4, 18, 3, 1, 3, 10, 0]

    def test_get_an_hourly_report_properly_II_less_than_23_hours(self, config_rollback_create_cameras,
                                                                 reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(f"/metrics/cameras/social-distancing/hourly?cameras={camera_id}&date=2021-02-19")

        assert response.status_code == 200
        assert response.json()['detected_objects'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                       0, 0, 0]
        assert response.json()['no_infringement'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                      0, 0]
        assert response.json()['low_infringement'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                       0, 0, 0]
        assert response.json()['high_infringement'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                        0, 0, 0]
        assert response.json()['critical_infringement'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                                            0, 0, 0, 0, 0]

    def test_get_hourly_report_two_dates(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        camera_id_2 = camera["id"]
        response = client.get(f"/metrics/cameras/social-distancing/hourly?cameras={camera_id},{camera_id_2}&date=2021"
                              f"-02-25")

        assert response.status_code == 200
        assert response.json()['detected_objects'] == list(map(lambda x: x * 2, [54, 30, 19, 37, 27, 39, 44, 25, 51,
                                                                                 31, 47, 39, 16, 26, 67, 29, 36, 17,
                                                                                 31, 32, 19, 38, 34, 50]))
        assert response.json()['no_infringement'] == list(map(lambda x: x * 2, [13, 5, 2, 18, 5, 11, 10, 6, 14, 6, 17,
                                                                                18, 4, 8, 17, 11, 3, 6, 7, 4, 6, 10,
                                                                                11, 18]))

        assert response.json()['low_infringement'] == list(map(lambda x: x * 2, [10, 14, 4, 19, 11, 15, 7, 7, 11, 2, 1,
                                                                                 3, 10, 10, 19, 7, 15, 5, 5, 16, 4,
                                                                                 12, 13, 17]))
        assert response.json()['high_infringement'] == list(map(lambda x: x * 2, [16, 2, 3, 0, 8, 1, 16, 11, 12, 6, 15,
                                                                                  0, 0, 1, 14, 7, 10, 2, 1, 9, 8, 13,
                                                                                  0, 15]))
        assert response.json()['critical_infringement'] == list(map(lambda x: x * 2, [15, 9, 10, 0, 3, 12, 11, 1, 14,
                                                                                      17, 14, 18, 2, 7, 17, 4, 8,
                                                                                      4, 18, 3, 1, 3, 10, 0]))

    def test_try_get_hourly_report_non_existent_id(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = 'BAD_ID'
        response = client.get(f"/metrics/cameras/social-distancing/hourly?cameras={camera_id}&date=2021-02-25")

        assert response.status_code == 404
        assert response.json() == {'detail': "Camera with id 'BAD_ID' does not exist"}

    def test_try_get_hourly_report_bad_date_format(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera['id']
        response = client.get(f"/metrics/cameras/social-distancing/hourly?cameras={camera_id}&date=WRONG_DATE")

        assert response.status_code == 400

    def test_try_get_hourly_report_non_existent_date(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera['id']
        response = client.get(f"/metrics/cameras/social-distancing/hourly?cameras={camera_id}&date=2003-05-24")

        assert response.status_code == 200
        # TODO: ASK IF THIS BEHAVIOUR IS RIGHT
        # Since no files with the specified date were found, no objects were added to the report.
        assert response.json() == {
            'detected_objects': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'no_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'low_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'high_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'critical_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
        }

    def test_try_get_hourly_report_two_dates_one_of_them_bad_id(self, config_rollback_create_cameras,
                                                                reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        camera_id_2 = 'BAD_ID'
        response = client.get(f"/metrics/cameras/social-distancing/hourly?cameras={camera_id},{camera_id_2}&date=2021"
                              f"-02-25")

        assert response.status_code == 404
        assert response.json() == {'detail': "Camera with id 'BAD_ID' does not exist"}


# pytest -v api/tests/app/test_camera_metrics.py::TestsGetCameraDistancingDailyReport
class TestsGetCameraDistancingDailyReport:
    """ Get Camera Distancing Daily Report , GET /metrics/cameras/social-distancing/daily"""
    """
    Returns a daily report (for the date range specified) with information about the
    social distancing infractions detected in the cameras.
    """

    def test_get_a_daily_report_properly(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/daily?cameras={camera_id}&from_date=2020-09-20&to_date=2020-09-23")

        assert response.json() == {
            'detected_objects': [0, 0, 148, 179], 'no_infringement': [0, 0, 136, 139],
            'low_infringement': [0, 0, 0, 19], 'high_infringement': [0, 0, 5, 17],
            'critical_infringement': [0, 0, 7, 4], 'dates': ['2020-09-20', '2020-09-21', '2020-09-22', '2020-09-23']
        }
        assert response.status_code == 200

    def test_get_a_daily_report_properly_one_day(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/daily?cameras={camera_id}&from_date=2020-09-20&to_date=2020-09-20")

        assert response.json() == {
            'detected_objects': [0], 'no_infringement': [0], 'low_infringement': [0], 'high_infringement': [0],
            'critical_infringement': [0], 'dates': ['2020-09-20']
        }
        assert response.status_code == 200

    def test_get_a_daily_report_properly_two_cameras(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        camera_id_2 = camera_2["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/daily?cameras={camera_id},{camera_id_2}&from_date=2020-09-20&to_date"
            f"=2020-09-23")

        # In our example, both cameras have the same report.csv file, so the result is the same
        # as one camera, but duplicated
        assert response.json() == {
            'detected_objects': [0, 0, 296, 358], 'no_infringement': [0, 0, 272, 278],
            'low_infringement': [0, 0, 0, 38], 'high_infringement': [0, 0, 10, 34],
            'critical_infringement': [0, 0, 14, 8], 'dates': ['2020-09-20', '2020-09-21', '2020-09-22', '2020-09-23']
        }
        assert response.status_code == 200

    def test_try_get_a_daily_report_bad_id(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = 'BAD_ID'
        response = client.get(
            f"/metrics/cameras/social-distancing/daily?cameras={camera_id}&from_date=2020-09-20&to_date=2020-09-23")
        assert response.json() == {'detail': "Camera with id 'BAD_ID' does not exist"}
        assert response.status_code == 404

    def test_try_get_a_daily_report_bad_dates(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/daily?cameras={camera_id}&from_date=BAD_DATE&to_date=BAD_DATE")

        assert response.status_code == 400

    def test_try_get_a_daily_report_no_reports_for_dates(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/daily?cameras={camera_id}&from_date=2003-05-18&to_date=2003-05-28")

        # TODO: Ask if this behaviour is right
        assert response.status_code == 200
        assert response.json() == {
            'detected_objects': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'low_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'high_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'critical_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'dates': ['2003-05-18', '2003-05-19', '2003-05-20', '2003-05-21', '2003-05-22', '2003-05-23', '2003-05-24',
                      '2003-05-25', '2003-05-26', '2003-05-27', '2003-05-28']
        }

    def test_try_get_a_daily_report_wrong_dates(self, config_rollback_create_cameras, reports_simulation):
        """from_date doesn't come before to_date"""

        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/daily?cameras={camera_id}&from_date=2020-09-20&to_date=2020-09-10")

        assert response.status_code == 400


# pytest -v api/tests/app/test_camera_metrics.py::TestsGetCameraDistancingWeeklyReport
class TestsGetCameraDistancingWeeklyReport:
    """ Get Camera Distancing Weekly Report , GET /metrics/cameras/social-distancing/weekly"""
    """
    Returns a weekly report (for the date range specified) with information about the social distancing infractions
    detected in the cameras.

    If weeks is provided and is a positive number:

    from_date and to_date are ignored.
    Report spans from weeks*7 + 1 days ago to yesterday.
    Taking yesterday as the end of week.

    Else:

    Report spans from from_Date to to_date.
    Taking Sunday as the end of week
    """

    def test_get_a_weekly_report_properly(self, config_rollback_create_cameras, reports_simulation):
        """
        Given date range spans two weeks.
        Week 1: 2020-9-14 2020-9-20
        Week 2: 2020-9-21 2020-9-27
        """
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&from_date=2020-09-20&to_date=2020-09-23")

        assert response.json() == {
            'detected_objects': [0, 327],
            'no_infringement': [0, 275],
            'low_infringement': [0, 19],
            'high_infringement': [0, 22],
            'critical_infringement': [0, 11],
            'weeks': ['2020-09-20 2020-09-20', '2020-09-21 2020-09-23']
        }
        assert response.status_code == 200

    def test_get_a_weekly_report_properly_II(self, config_rollback_create_cameras, reports_simulation):
        """
        Given date range spans only one whole week.
        Week 1: 2020-9-21 2020-9-27
        """
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&from_date=2020-09-21&to_date=2020-09-27")

        assert response.json() == {
            'detected_objects': [714], 'no_infringement': [555], 'low_infringement': [73], 'high_infringement': [55],
            'critical_infringement': [30], 'weeks': ['2020-09-21 2020-09-27']}
        assert response.status_code == 200

    @freeze_time("2020-09-30")
    def test_get_a_weekly_report_properly_weeks_value(self, config_rollback_create_cameras, reports_simulation):
        """
        Here we mock datetime.date.today() to a more convenient date set in @freeze_time("2020-09-30")
        """
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&weeks=4")

        assert response.status_code == 200
        assert response.json() == {
            'detected_objects': [535, 754, 714, 714], 'no_infringement': [416, 622, 555, 555],
            'low_infringement': [54, 59, 73, 73], 'high_infringement': [38, 56, 55, 55],
            'critical_infringement': [26, 19, 30, 30],
            'weeks': ['2020-09-02 2020-09-08', '2020-09-09 2020-09-15', '2020-09-16 2020-09-22',
                      '2020-09-23 2020-09-29']
        }

    def test_get_a_weekly_report_no_dates_or_week_values(self, config_rollback_create_cameras, reports_simulation):
        """
        Here we mock datetime.date.today() to a more convenient date set in @freeze_time("2020-09-30")
        """
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}")

        # TODO: Ask if this behaviour is right.
        assert response.status_code == 200
        assert response.json() == {
            'detected_objects': [], 'no_infringement': [], 'low_infringement': [], 'high_infringement': [],
            'critical_infringement': [], 'weeks': []}

    @freeze_time("2020-09-30")
    def test_try_get_a_weekly_report_properly_weeks_value_wrong(self, config_rollback_create_cameras,
                                                                reports_simulation):
        """
        Here we mock datetime.date.today() to a more convenient date set in @freeze_time("2020-09-30")
        """
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&weeks=WRONG")

        assert response.status_code == 400

    @freeze_time("2020-09-30")
    def test_get_a_weekly_report_properly_weeks_value_and_dates(self, config_rollback_create_cameras,
                                                                reports_simulation):
        """
        Here we mock datetime.date.today() to a more convenient date set in @freeze_time("2012-01-01")
        In addition, query string weeks is given, but also from_date and to_date. So dates should be ignored.
        """
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&weeks=4&from_date=2020-09-21&to_date=2020"
            f"-09-27")

        assert response.status_code == 200
        assert response.json() == {
            'detected_objects': [535, 754, 714, 714], 'no_infringement': [416, 622, 555, 555],
            'low_infringement': [54, 59, 73, 73], 'high_infringement': [38, 56, 55, 55],
            'critical_infringement': [26, 19, 30, 30],
            'weeks': ['2020-09-02 2020-09-08', '2020-09-09 2020-09-15', '2020-09-16 2020-09-22',
                      '2020-09-23 2020-09-29']
        }

    def test_try_get_a_weekly_report_bad_id(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = 'BAD_ID'
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&from_date=2020-09-20&to_date=2020-09-23")

        assert response.status_code == 404
        assert response.json() == {'detail': "Camera with id 'BAD_ID' does not exist"}

    def test_get_a_weekly_report_no_query_string(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly")

        # TODO: IF THIS BEHAVIOUR IS RIGHT
        assert response.status_code == 200
        assert response.json() == {
            'detected_objects': [], 'no_infringement': [], 'low_infringement': [], 'high_infringement': [],
            'critical_infringement': [], 'weeks': []}

    def test_try_get_a_weekly_report_bad_dates_format(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&from_date=BAD_DATE&to_date=BAD_DATE")

        assert response.status_code == 400

    def test_try_get_a_weekly_report_non_existent_dates(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&from_date=2012-04-12&to_date=2012-05-18")

        # TODO: IF THIS BEHAVIOUR IS RIGHT
        assert response.status_code == 200
        assert response.json() == {
            'detected_objects': [0, 0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0, 0],
            'low_infringement': [0, 0, 0, 0, 0, 0], 'high_infringement': [0, 0, 0, 0, 0, 0],
            'critical_infringement': [0, 0, 0, 0, 0, 0],
            'weeks': ['2012-04-12 2012-04-15', '2012-04-16 2012-04-22', '2012-04-23 2012-04-29',
                      '2012-04-30 2012-05-06', '2012-05-07 2012-05-13', '2012-05-14 2012-05-18']
        }

    # pytest -v api/tests/app/test_camera_metrics.py::TestsGetCameraDistancingWeeklyReport::test_try_get_a_weekly_report_invalid_range_of_dates
    def test_try_get_a_weekly_report_invalid_range_of_dates(self, config_rollback_create_cameras, reports_simulation):
        """from_date is after to_date"""
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&from_date=2020-09-25&to_date=2020-09-18")

        assert response.status_code == 400

    # pytest -v api/tests/app/test_camera_metrics.py::TestsGetCameraDistancingWeeklyReport::test_try_get_a_weekly_report_no_id
    def test_try_get_a_weekly_report_no_id(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        response = client.get(
            f"/metrics/cameras/social-distancing/weekly?from_date=2020-09-20&to_date=2020-09-23")

        # Todo: Ask for this behaviour. Apparently first it looks for every ID that has a report.
        #  We can check this putting a breakpoint and checking <entities> in get_weekly_metric().
        #  Finally, the results in response corresponds to the addition of the given weeks
        #  (2020-09-25&to_date=2020-09-18) * 2 (one for each camera, the only cameras that have reports are
        #  the ones that we create in reports_simulation fixture)
        assert response.status_code == 200
        assert response.json() == {'detected_objects': [0, 654], 'no_infringement': [0, 550],
                                   'low_infringement': [0, 38],
                                   'high_infringement': [0, 44], 'critical_infringement': [0, 22],
                                   'weeks': ['2020-09-20 2020-09-20', '2020-09-21 2020-09-23']}

    def test_try_get_a_weekly_report_only_from_date(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        with pytest.raises(TypeError):
            response = client.get(
                f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&from_date=2020-09-20")

        # TODO: Exception raised.
        #  TypeError: '>' not supported between instances of 'str' and 'datetime.date'

    def test_try_get_a_weekly_report_only_to_date(self, config_rollback_create_cameras, reports_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_create_cameras
        camera_id = camera["id"]
        with pytest.raises(TypeError):
            response = client.get(
                f"/metrics/cameras/social-distancing/weekly?cameras={camera_id}&to_date=2020-09-20")

        # TODO: Exception raised.
        #  TypeError: '>' not supported between instances of 'str' and 'datetime.date'
