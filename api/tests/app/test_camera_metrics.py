import os
import pytest
from freezegun import freeze_time
import numpy as np
# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback_cameras, heatmap_simulation, config_rollback

HEATMAP_PATH_PREFIX = "/repo/api/tests/data/mocked_data/data/processor/static/data/sources/"


# pytest -v api/tests/app/test_camera_metrics.py::TestsGetHeatmap
class TestsGetHeatmap:
    """ Get Heatmap, GET /metrics/cameras/{camera_id}/heatmap """
    """
    Returns a heatmap image displaying the violations/detections detected by the camera <camera_id>.
    """

    def test_get_one_heatmap_properly(self, config_rollback_cameras, heatmap_simulation):
        # Make the request
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-19")

        # Get the heatmap
        heatmap_path = os.path.join(HEATMAP_PATH_PREFIX, camera_id, "heatmaps", "violations_heatmap_2020-09-19.npy")
        heatmap = np.load(heatmap_path).tolist()

        # Compare results
        assert response.status_code == 200
        assert response.json()["heatmap"] == heatmap

    def test_try_get_two_heatmaps(self, config_rollback_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-20")

        heatmap_path = os.path.join(HEATMAP_PATH_PREFIX, camera_id, "heatmaps", "violations_heatmap_2020-09-19.npy")
        heatmap = np.load(heatmap_path).tolist()

        assert response.status_code == 200
        assert response.json()["heatmap"] == heatmap
        assert response.json()["not_found_dates"] == ["2020-09-20"]

    def test_get_two_valid_heatmaps(self, config_rollback_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-22")

        heatmap_path_1 = os.path.join(HEATMAP_PATH_PREFIX, camera_id, "heatmaps", "violations_heatmap_2020-09-19.npy")
        heatmap_path_2 = os.path.join(HEATMAP_PATH_PREFIX, camera_id, "heatmaps", "violations_heatmap_2020-09-22.npy")
        heatmap_1 = np.load(heatmap_path_1)
        heatmap_2 = np.load(heatmap_path_2)
        final_heatmap = np.add(heatmap_1, heatmap_2).tolist()

        assert response.status_code == 200
        assert response.json()["not_found_dates"] == ['2020-09-20', '2020-09-21']
        assert response.json()['heatmap'] == final_heatmap

    def test_get_one_heatmap_properly_detections(self, config_rollback_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        response = client.get(
            f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-19&report_type=detections")

        heatmap_path = os.path.join(HEATMAP_PATH_PREFIX, camera_id, "heatmaps", "detections_heatmap_2020-09-19.npy")
        heatmap = np.load(heatmap_path).tolist()

        assert response.status_code == 200
        assert response.json()["heatmap"] == heatmap

    def test_try_get_one_heatmap_bad_camera_id(self, config_rollback_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = "wrong_id"

        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-19")

        assert response.status_code == 404
        assert response.json() == {'detail': "Camera with id 'wrong_id' does not exist"}

    def test_try_get_one_heatmap_bad_report_type(self, config_rollback_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        response = client.get(
            f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-19&to_date=2020-09-19&report_type"
            f"=non_existent_report_type")

        assert response.status_code == 400
        assert response.json() == {'detail': [{'loc': [], 'msg': 'Invalid report_type', 'type': 'invalid config'}]}

    def test_try_get_one_heatmap_bad_dates(self, config_rollback_cameras, heatmap_simulation):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=today&to_date=tomorrow")

        assert response.status_code == 400
        assert response.json() == {'detail': [{'loc': ['query', 'from_date'], 'msg': ''
                                                                                     'invalid date format',
                                               'type': 'value_error.date'},
                                              {'loc': ['query', 'to_date'], 'msg': 'invalid date format',
                                               'type': 'value_error.date'}], 'body': None}

    def test_try_get_one_heatmap_wrong_dates(self, config_rollback_cameras, heatmap_simulation):
        """from_date is after to_date"""
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date=2020-09-20&to_date=2020-09-19")

        assert response.status_code == 400

    def test_try_get_one_heatmap_only_from_date(self, config_rollback_cameras, heatmap_simulation):
        """ Note that here as we do not send to_date, default value will take place, and to_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "2021-01-10" - "today".
        """
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "2021-01-10"

        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?from_date={from_date}")

        assert response.status_code == 200

    def test_try_get_one_heatmap_only_to_date(self, config_rollback_cameras, heatmap_simulation):
        """ Note that here as we do not send from_date, default value will take place, and from_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=date.today().weekday(),
        weeks=4)" - "2020-09-20" and this date range is probably wrong because from_date will be later than to_date.
        """

        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        to_date = "2020-09-20"

        response = client.get(f"/metrics/cameras/{camera_id}/heatmap?to_date={to_date}")

        assert response.status_code == 400


# pytest -v api/tests/app/test_camera_metrics.py::TestsGetCameraDistancingLive
class TestsGetCameraDistancingLive:
    """ Get Camera Distancing Live, GET /metrics/cameras/social-distancing/live """
    """
    Returns a report with live information about the social distancing infractions detected in the cameras.
    """

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'time': '2021-02-19 13:37:58',
                'trend': 0.05,
                'detected_objects': 6,
                'no_infringement': 5,
                'low_infringement': 0,
                'high_infringement': 1,
                'critical_infringement': 0
            }),
            ("face-mask-detections", {
                'time': '2021-02-19 13:37:58',
                'trend': 0.0,
                'no_face': 10,
                'face_with_mask': 0,
                'face_without_mask': 0
            })
        ]
    )
    def test_get_a_report_properly(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        response = client.get(f"/metrics/cameras/{metric}/live?cameras={camera_id}")

        assert response.json() == expected
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'time': '2021-02-19 13:37:58', 'trend': 0.72, 'detected_objects': 20, 'no_infringement': 9,
                'low_infringement': 7, 'high_infringement': 2, 'critical_infringement': 3
            }),
            ("face-mask-detections", {
                'time': '2021-02-19 13:37:58', 'trend': 0.52, 'no_face': 24, 'face_with_mask': 8, 'face_without_mask': 1
            })
        ]
    )
    def test_get_a_report_two_valid_cameras(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id_1 = camera["id"]
        camera_id_2 = camera_2["id"]

        response = client.get(f"/metrics/cameras/{metric}/live?cameras={camera_id_1},{camera_id_2}")

        assert response.json() == expected
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {'detail': "Camera with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Camera with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_a_report_bad_id_camera(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras

        response = client.get(f"/metrics/cameras/{metric}/live?cameras=BAD_ID")

        assert response.json() == expected
        assert response.status_code == 404


# pytest -v api/tests/app/test_camera_metrics.py::TestsGetCameraDistancingHourlyReport
class TestsGetCameraDistancingHourlyReport:
    """ Get Camera Distancing Hourly Report , GET /metrics/cameras/social-distancing/hourly """
    """
    Returns a hourly report (for the date specified) with information about 
    the social distancing infractions detected in the cameras .
    """

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [54, 30, 19, 37, 27, 39, 44, 25, 51, 31, 47, 39, 16, 26, 67, 29, 36, 17, 31, 32, 19,
                                     38,
                                     34, 50],
                'no_infringement': [13, 5, 2, 18, 5, 11, 10, 6, 14, 6, 17, 18, 4, 8, 17, 11, 3, 6, 7, 4, 6, 10, 11, 18],
                'low_infringement': [10, 14, 4, 19, 11, 15, 7, 7, 11, 2, 1, 3, 10, 10, 19, 7, 15, 5, 5, 16, 4, 12, 13,
                                     17],
                'high_infringement': [16, 2, 3, 0, 8, 1, 16, 11, 12, 6, 15, 0, 0, 1, 14, 7, 10, 2, 1, 9, 8, 13, 0, 15],
                'critical_infringement': [15, 9, 10, 0, 3, 12, 11, 1, 14, 17, 14, 18, 2, 7, 17, 4, 8, 4, 18, 3, 1, 3,
                                          10,
                                          0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("face-mask-detections", {
                'no_face': [3, 3, 9, 2, 8, 2, 9, 8, 8, 0, 1, 2, 4, 6, 6, 2, 5, 2, 0, 0, 8, 3, 1, 2],
                'face_with_mask': [5, 4, 6, 9, 2, 3, 9, 7, 7, 3, 8, 3, 6, 7, 4, 2, 0, 1, 4, 1, 9, 5, 1, 4],
                'face_without_mask': [2, 6, 0, 8, 7, 7, 9, 1, 9, 8, 6, 4, 5, 7, 1, 0, 7, 5, 3, 3, 3, 8, 6, 5],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            })
        ]
    )
    def test_get_an_hourly_report_properly(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        date = "2021-02-25"

        response = client.get(f"/metrics/cameras/{metric}/hourly?cameras={camera_id}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'no_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'high_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'face_with_mask': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'face_without_mask': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            })
        ]
    )
    def test_get_an_hourly_report_properly_II_less_than_23_hours(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        date = "2021-02-19"

        response = client.get(f"/metrics/cameras/{metric}/hourly?cameras={camera_id}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [108, 60, 38, 74, 54, 78, 88, 50, 102, 62, 94, 78, 32, 52, 134, 58, 72, 34, 62, 64,
                                     38,
                                     76, 68, 100],
                'no_infringement': [26, 10, 4, 36, 10, 22, 20, 12, 28, 12, 34, 36, 8, 16, 34, 22, 6, 12, 14, 8, 12, 20,
                                    22,
                                    36],
                'low_infringement': [20, 28, 8, 38, 22, 30, 14, 14, 22, 4, 2, 6, 20, 20, 38, 14, 30, 10, 10, 32, 8, 24,
                                     26,
                                     34],
                'high_infringement': [32, 4, 6, 0, 16, 2, 32, 22, 24, 12, 30, 0, 0, 2, 28, 14, 20, 4, 2, 18, 16, 26, 0,
                                      30],
                'critical_infringement': [30, 18, 20, 0, 6, 24, 22, 2, 28, 34, 28, 36, 4, 14, 34, 8, 16, 8, 36, 6, 2, 6,
                                          20,
                                          0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]}
             ),
            ("face-mask-detections", {
                'no_face': [6, 6, 18, 4, 16, 4, 18, 16, 16, 0, 2, 4, 8, 12, 12, 4, 10, 4, 0, 0, 16, 6, 2, 4],
                'face_with_mask': [10, 8, 12, 18, 4, 6, 18, 14, 14, 6, 16, 6, 12, 14, 8, 4, 0, 2, 8, 2, 18, 10, 2, 8],
                'face_without_mask': [4, 12, 0, 16, 14, 14, 18, 2, 18, 16, 12, 8, 10, 14, 2, 0, 14, 10, 6, 6, 6, 16, 12,
                                      10],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            })
        ]
    )
    def test_get_hourly_report_two_dates(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        camera_id_2 = camera["id"]
        date = "2021-02-25"

        response = client.get(f"/metrics/cameras/{metric}/hourly?cameras={camera_id},{camera_id_2}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {'detail': "Camera with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Camera with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_hourly_report_non_existent_id(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = 'BAD_ID'
        date = "2021-02-25"

        response = client.get(f"/metrics/cameras/{metric}/hourly?cameras={camera_id}&date={date}")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["social-distancing", "face-mask-detections"]
    )
    def test_try_get_hourly_report_bad_date_format(self, config_rollback_cameras, metric):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera['id']
        date = "WRONG_DATE"

        response = client.get(f"/metrics/cameras/{metric}/hourly?cameras={camera_id}&date={date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'no_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'high_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'face_with_mask': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'face_without_mask': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            })
        ]
    )
    def test_try_get_hourly_report_non_existent_date(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera['id']
        date = "2003-05-24"

        response = client.get(f"/metrics/cameras/{metric}/hourly?cameras={camera_id}&date={date}")

        assert response.status_code == 200
        # Since no files with the specified date were found, no objects were added to the report.
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {'detail': "Camera with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Camera with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_hourly_report_two_dates_one_of_them_bad_id(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        camera_id_2 = 'BAD_ID'
        date = "2021-02-25"

        response = client.get(f"/metrics/cameras/{metric}/hourly?cameras={camera_id},{camera_id_2}&date={date}")

        assert response.status_code == 404
        assert response.json() == expected


# pytest -v api/tests/app/test_camera_metrics.py::TestsGetCameraDistancingDailyReport
class TestsGetCameraDistancingDailyReport:
    """ Get Camera Distancing Daily Report , GET /metrics/cameras/social-distancing/daily"""
    """
    Returns a daily report (for the date range specified) with information about the
    social distancing infractions detected in the cameras.
    """

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [0, 0, 148, 179], 'no_infringement': [0, 0, 136, 139],
                'low_infringement': [0, 0, 0, 19], 'high_infringement': [0, 0, 5, 17],
                'critical_infringement': [0, 0, 7, 4], 'dates': ['2020-09-20', '2020-09-21', '2020-09-22', '2020-09-23']
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 18, 18], 'face_with_mask': [0, 0, 106, 135], 'face_without_mask': [0, 0, 26, 30],
                'dates': ['2020-09-20', '2020-09-21', '2020-09-22', '2020-09-23']})
        ]
    )
    def test_get_a_daily_report_properly(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        to_date = "2020-09-23"
        from_date = "2020-09-20"

        response = client.get(
            f"/metrics/cameras/{metric}/daily?cameras={camera_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [0], 'no_infringement': [0], 'low_infringement': [0], 'high_infringement': [0],
                'critical_infringement': [0], 'dates': ['2020-09-20']
            }),
            ("face-mask-detections", {
                'no_face': [0], 'face_with_mask': [0], 'face_without_mask': [0], 'dates': ['2020-09-20']})
        ]
    )
    def test_get_a_daily_report_properly_one_day(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        date = "2020-09-20"

        response = client.get(
            f"/metrics/cameras/{metric}/daily?cameras={camera_id}&from_date={date}&to_date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [104, 120, 161, 301], 'no_infringement': [5, 35, 143, 183],
                'low_infringement': [57, 42, 2, 87], 'high_infringement': [42, 43, 9, 27],
                'critical_infringement': [0, 0, 7, 4], 'dates': ['2020-09-20', '2020-09-21', '2020-09-22', '2020-09-23']
            }),
            ("face-mask-detections", {
                'no_face': [85, 77, 114, 41], 'face_with_mask': [36, 76, 188, 170],
                'face_without_mask': [23, 33, 39, 128],
                'dates': ['2020-09-20', '2020-09-21', '2020-09-22', '2020-09-23']
            })
        ]
    )
    def test_get_a_daily_report_properly_two_cameras(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        camera_id_2 = camera_2["id"]
        to_date = "2020-09-23"
        from_date = "2020-09-20"

        response = client.get(
            f"/metrics/cameras/{metric}/daily?cameras={camera_id},{camera_id_2}&from_date={from_date}&to_date={to_date}"
        )

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {'detail': "Camera with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Camera with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_a_daily_report_bad_id(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = 'BAD_ID'

        response = client.get(
            f"/metrics/cameras/{metric}/daily?cameras={camera_id}&from_date=2020-09-20&to_date=2020-09-23")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_daily_report_bad_dates(self, config_rollback_cameras, metric):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "BAD_DATE"
        to_date = "BAD_DATE"

        response = client.get(
            f"/metrics/cameras/{metric}/daily?cameras={camera_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'no_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'high_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'dates': ['2003-05-18', '2003-05-19', '2003-05-20', '2003-05-21', '2003-05-22', '2003-05-23',
                          '2003-05-24', '2003-05-25', '2003-05-26', '2003-05-27', '2003-05-28']
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'face_without_mask': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'dates': ['2003-05-18', '2003-05-19', '2003-05-20', '2003-05-21', '2003-05-22', '2003-05-23',
                          '2003-05-24', '2003-05-25', '2003-05-26', '2003-05-27', '2003-05-28']
            })
        ]
    )
    def test_try_get_a_daily_report_no_reports_for_dates(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "2003-05-18"
        to_date = "2003-05-28"

        response = client.get(
            f"/metrics/cameras/{metric}/daily?cameras={camera_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_daily_report_wrong_dates(self, config_rollback_cameras, metric):
        """from_date doesn't come before to_date"""

        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "2020-09-20"
        to_date = "2020-09-10"

        response = client.get(
            f"/metrics/cameras/{metric}/daily?cameras={camera_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_daily_report_only_from_date(self, config_rollback_cameras, metric):
        """ Note that here as we do not send to_date, default value will take place, and to_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "2021-01-10" - "today".
        """

        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "2021-01-10"

        response = client.get(f"/metrics/cameras/{metric}/daily?cameras={camera_id}&from_date={from_date}")

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "metric",
        ["social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_daily_report_only_to_date(self, config_rollback_cameras, metric):
        """ Note that here as we do not send from_date, default value will take place, and from_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=3)" - "2020-09-20" and
        this date range is probably wrong because from_date will be later than to_date.
        """

        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        to_date = "2020-09-20"

        response = client.get(f"/metrics/cameras/{metric}/daily?cameras={camera_id}&to_date={to_date}")

        assert response.status_code == 400


# pytest -v api/tests/app/test_camera_metrics.py::TestsGetCameraDistancingWeeklyReport
class TestsGetCameraDistancingWeeklyReport:
    """ Get Camera Distancing Weekly Report , GET /metrics/cameras/social-distancing/weekly """
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

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [0, 327],
                'no_infringement': [0, 275],
                'low_infringement': [0, 19],
                'high_infringement': [0, 22],
                'critical_infringement': [0, 11],
                'weeks': ['2020-09-20 2020-09-20', '2020-09-21 2020-09-23']
            }),
            ("face-mask-detections", {
                'no_face': [0, 36], 'face_with_mask': [0, 241], 'face_without_mask': [0, 56],
                'weeks': ['2020-09-20 2020-09-20', '2020-09-21 2020-09-23']
            })
        ]
    )
    def test_get_a_weekly_report_properly(self, config_rollback_cameras, metric, expected):
        """
        Given date range spans two weeks.
        Week 1: 2020-9-14 2020-9-20
        Week 2: 2020-9-21 2020-9-27
        """
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "2020-09-20"
        to_date = "2020-09-23"

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [714], 'no_infringement': [555], 'low_infringement': [73],
                'high_infringement': [55],
                'critical_infringement': [30], 'weeks': ['2020-09-21 2020-09-27']
            }),
            ("face-mask-detections", {
                'no_face': [85], 'face_with_mask': [519], 'face_without_mask': [171],
                'weeks': ['2020-09-21 2020-09-27']
            })
        ]
    )
    def test_get_a_weekly_report_properly_II(self, config_rollback_cameras, metric,
                                             expected):
        """
        Given date range spans only one whole week.
        Week 1: 2020-9-21 2020-9-27
        """
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "2020-09-21"
        to_date = "2020-09-27"

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [535, 754, 714, 714], 'no_infringement': [416, 622, 555, 555],
                'low_infringement': [54, 59, 73, 73], 'high_infringement': [38, 56, 55, 55],
                'critical_infringement': [26, 19, 30, 30],
                'weeks': ['2020-09-02 2020-09-08', '2020-09-09 2020-09-15', '2020-09-16 2020-09-22',
                          '2020-09-23 2020-09-29']
            }),
            ("face-mask-detections", {
                'no_face': [88, 85, 106, 85], 'face_with_mask': [310, 519, 445, 519],
                'face_without_mask': [150, 171, 180, 171],
                'weeks': ['2020-09-02 2020-09-08', '2020-09-09 2020-09-15', '2020-09-16 2020-09-22',
                          '2020-09-23 2020-09-29']
            })
        ]
    )
    @freeze_time("2020-09-30")
    def test_get_a_weekly_report_properly_weeks_value(self, config_rollback_cameras,
                                                      metric, expected):
        """
        Here we mock datetime.date.today() to a more convenient date set in @freeze_time("2020-09-30")
        """
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        weeks = 4

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&weeks={weeks}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0], 'high_infringement': [0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0]
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0, 0], 'face_without_mask': [0, 0, 0, 0, 0]
            })
        ]
    )
    def test_get_a_weekly_report_no_dates_or_week_values(self, config_rollback_cameras, metric, expected):
        """
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=date.today().weekday(),
        weeks=4)" - "date.today()" and this date range (4 weeks ago from today) should never have values for any
        camera in order to pass the test. Moreover, we do not assert response.json()["weeks"] because will change
        depending on the date.
        """

        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?cameras={camera_id}")

        assert response.status_code == 200
        for key in expected:
            assert response.json()[key] == expected[key]

    @pytest.mark.parametrize(
        "metric",
        ["social-distancing", "face-mask-detections"]
    )
    @freeze_time("2020-09-30")
    def test_try_get_a_weekly_report_properly_weeks_value_wrong(self, config_rollback_cameras, metric):
        """
        Here we mock datetime.date.today() to a more convenient date set in @freeze_time("2020-09-30")
        """
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        weeks = "WRONG"

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&weeks={weeks}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [535, 754, 714, 714], 'no_infringement': [416, 622, 555, 555],
                'low_infringement': [54, 59, 73, 73], 'high_infringement': [38, 56, 55, 55],
                'critical_infringement': [26, 19, 30, 30],
                'weeks': ['2020-09-02 2020-09-08', '2020-09-09 2020-09-15', '2020-09-16 2020-09-22',
                          '2020-09-23 2020-09-29']
            }),
            ("face-mask-detections", {
                'no_face': [88, 85, 106, 85], 'face_with_mask': [310, 519, 445, 519],
                'face_without_mask': [150, 171, 180, 171],
                'weeks': ['2020-09-02 2020-09-08', '2020-09-09 2020-09-15', '2020-09-16 2020-09-22',
                          '2020-09-23 2020-09-29']
            })
        ]
    )
    @freeze_time("2020-09-30")
    def test_get_a_weekly_report_properly_weeks_value_and_dates(self, config_rollback_cameras, metric, expected):
        """
        Here we mock datetime.date.today() to a more convenient date set in @freeze_time("2012-01-01")
        In addition, query string weeks is given, but also from_date and to_date. So dates should be ignored.
        """
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        weeks = 4
        from_date = "2020-09-21"
        to_date = "2020-09-27"

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&weeks={weeks}&from_date={from_date}&"
            f"to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {'detail': "Camera with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Camera with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_a_weekly_report_bad_id(self, config_rollback_cameras, metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = 'BAD_ID'
        from_date = "2020-09-20"
        to_date = "2020-09-23"

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0], 'high_infringement': [0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0]
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0, 0], 'face_without_mask': [0, 0, 0, 0, 0]
            })
        ]
    )
    def test_get_a_weekly_report_no_query_string(self, config_rollback_cameras,
                                                 metric, expected):
        """
        If no camera is provided, it will search all IDs for each existing camera.

        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=date.today().weekday(),
        weeks=4)" - "date.today()" and this date range (4 weeks ago from today) should never have values for any
        camera in order to pass the test. Moreover, we do not assert response.json()["weeks"] because will change
        depending on the date.
        """

        camera, camera_2, client, config_sample_path = config_rollback_cameras

        response = client.get(
            f"/metrics/cameras/{metric}/weekly")

        assert response.status_code == 200
        for key in expected:
            assert response.json()[key] == expected[key]

    @pytest.mark.parametrize(
        "metric",
        ["social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_bad_dates_format(self, config_rollback_cameras, metric):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "BAD_DATE"
        to_date = "BAD_DATE"

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0, 0], 'high_infringement': [0, 0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0, 0],
                'weeks': ['2012-04-12 2012-04-15', '2012-04-16 2012-04-22', '2012-04-23 2012-04-29',
                          '2012-04-30 2012-05-06', '2012-05-07 2012-05-13', '2012-05-14 2012-05-18']
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0, 0, 0],
                'face_without_mask': [0, 0, 0, 0, 0, 0],
                'weeks': ['2012-04-12 2012-04-15', '2012-04-16 2012-04-22', '2012-04-23 2012-04-29',
                          '2012-04-30 2012-05-06', '2012-05-07 2012-05-13', '2012-05-14 2012-05-18']
            })
        ]
    )
    def test_try_get_a_weekly_report_non_existent_dates(self, config_rollback_cameras,
                                                        metric, expected):
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "2012-04-12"
        to_date = "2012-05-18"

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_invalid_range_of_dates(self, config_rollback_cameras,
                                                            metric):
        """from_date is after to_date"""
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "2020-09-25"
        to_date = "2020-09-18"

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("social-distancing", {
                'detected_objects': [104, 582], 'no_infringement': [5, 361], 'low_infringement': [57, 131],
                'high_infringement': [42, 79], 'critical_infringement': [0, 11],
                'weeks': ['2020-09-20 2020-09-20', '2020-09-21 2020-09-23']
            }),
            ("face-mask-detections", {
                'no_face': [85, 232], 'face_with_mask': [36, 434], 'face_without_mask': [23, 200],
                'weeks': ['2020-09-20 2020-09-20', '2020-09-21 2020-09-23']
            })
        ]
    )
    def test_try_get_a_weekly_report_no_id(self, config_rollback_cameras, metric, expected):
        """
        If no camera is provided, it will search all IDs for each existing camera.
        No problem because we are mocking the date and we have the control over every existent camera. Unit is not
        broke.
        Our existing cameras are the ones that appeared in the config file of 'config_rollback_cameras' -> the ones
        from 'config-x86-openvino_MAIN' -> the ones with ids 49, 50 (cameras with ids 51 and 52 appear in another
        config file, so will not play here)
        """
        camera, camera_2, client, config_sample_path = config_rollback_cameras
        from_date = "2020-09-20"
        to_date = "2020-09-23"

        response = client.get(
            f"/metrics/cameras/{metric}/weekly?from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_only_from_date(self, config_rollback_cameras, metric):
        """
        Note that here as we do not send to_date, default value will take place, and to_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "2021-01-10" - "today".
        """

        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        from_date = "2021-01-10"

        response = client.get(f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&from_date={from_date}")

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "metric",
        ["social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_only_to_date(self, config_rollback_cameras, metric):
        """
        Note that here as we do not send from_date, default value will take place, and from_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=date.today().weekday(),
        weeks=4)" - "2020-09-20" and this date range is probably wrong because from_date will be later than to_date.
        """

        camera, camera_2, client, config_sample_path = config_rollback_cameras
        camera_id = camera["id"]
        to_date = "2020-09-20"

        response = client.get(f"/metrics/cameras/{metric}/weekly?cameras={camera_id}&to_date={to_date}")

        assert response.status_code == 400
