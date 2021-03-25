import pytest
from freezegun import freeze_time
# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import config_rollback_areas


# pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsLive
class TestsGetMetricsLive:
    """ LIVE """
    """ Get Area Occupancy Live, GET /metrics/cameras/occupancy/live """
    """ Get Area Distancing Live Report, GET /metrics/cameras/social-distancing/live """
    """ Get Camera Face Mask Detections Live, GET /metrics/cameras/face-mask-detections/live """

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'time': '2020-12-16 20:26:48', 'trend': 8.5, 'average_occupancy': 180, 'max_occupancy': 182,
                'occupancy_threshold': 140, 'violations': 40
            }),
            ("social-distancing", {
                'time': '2021-02-19 13:37:58', 'trend': 0.72, 'detected_objects': 20, 'no_infringement': 9,
                'low_infringement': 7, 'high_infringement': 2, 'critical_infringement': 3
            }),
            ("face-mask-detections", {
                'time': '2021-02-19 13:37:58', 'trend': 0.52, 'no_face': 24, 'face_with_mask': 8, 'face_without_mask': 1
            })
        ]
    )
    def test_get_a_report_properly(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        response = client.get(f"/metrics/areas/{metric}/live?areas={area_id}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'time': '2020-12-16 20:26:48', 'trend': -40.6, 'average_occupancy': 278, 'max_occupancy': 374,
                'occupancy_threshold': 280, 'violations': 120
            }),
            ("social-distancing", {
                'time': '2021-02-19 13:37:58', 'trend': 0.82, 'detected_objects': 32, 'no_infringement': 19,
                'low_infringement': 7, 'high_infringement': 4, 'critical_infringement': 3
            }),
            ("face-mask-detections", {
                'time': '2021-02-19 13:37:58', 'trend': 0.52, 'no_face': 44, 'face_with_mask': 8, 'face_without_mask': 1
            })
        ]
    )
    def test_try_get_a_report_no_areas(self, config_rollback_areas, metric, expected):
        """ If an area is not provided, it will search all reports for every existent area. """
        area, area_2, client, config_sample_path = config_rollback_areas

        response = client.get(f"/metrics/areas/{metric}/live?areas=")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'time': '2020-12-16 20:26:48', 'trend': -40.6, 'average_occupancy': 278, 'max_occupancy': 374,
                'occupancy_threshold': 280, 'violations': 120
            }),
            ("social-distancing", {
                'time': '2021-02-19 13:37:58', 'trend': 0.82, 'detected_objects': 32, 'no_infringement': 19,
                'low_infringement': 7, 'high_infringement': 4, 'critical_infringement': 3
            }),
            ("face-mask-detections", {
                'time': '2021-02-19 13:37:58', 'trend': 0.52, 'no_face': 44, 'face_with_mask': 8, 'face_without_mask': 1
            })
        ]
    )
    def test_try_get_a_report_no_query_string(self, config_rollback_areas, metric,
                                              expected):
        """ If an area is not provided, it will search all reports for every existent area. """
        area, area_2, client, config_sample_path = config_rollback_areas

        response = client.get(f"/metrics/areas/{metric}/live")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("social-distancing", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Area with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_a_report_bad_id(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = 'BAD_ID'

        response = client.get(f"/metrics/areas/{metric}/live?areas={area_id}")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'time': '2020-12-16 20:26:48', 'trend': -40.6, 'average_occupancy': 278, 'max_occupancy': 374,
                'occupancy_threshold': 280, 'violations': 120
            }),
            ("social-distancing", {
                'time': '2021-02-19 13:37:58', 'trend': 0.82, 'detected_objects': 32, 'no_infringement': 19,
                'low_infringement': 7, 'high_infringement': 4, 'critical_infringement': 3
            }),
            ("face-mask-detections", {
                'time': '2021-02-19 13:37:58', 'trend': 0.52, 'no_face': 44, 'face_with_mask': 8, 'face_without_mask': 1
            })
        ]
    )
    def test_get_a_report_properly_two_areas(self, config_rollback_areas, metric,
                                             expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area['id']
        area_id_2 = area_2['id']

        response = client.get(f"/metrics/areas/{metric}/live?areas={area_id_1},{area_id_2}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {'detail': "Area with id 'non_existent_id' does not exist"}),
            ("social-distancing", {'detail': "Area with id 'non_existent_id' does not exist"}),
            ("face-mask-detections", {'detail': "Area with id 'non_existent_id' does not exist"})
        ]
    )
    def test_try_get_a_report_for_two_areas_one_non_existent_id(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area['id']
        area_id_2 = 'non_existent_id'

        response = client.get(f"/metrics/areas/{metric}/live?areas={area_id_1},{area_id_2}")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'time': '2020-12-16 20:26:48', 'trend': -40.6, 'average_occupancy': 278, 'max_occupancy': 374,
                'occupancy_threshold': 280, 'violations': 120
            }),
            ("social-distancing", {
                'time': '2021-02-19 13:37:58', 'trend': 0.82, 'detected_objects': 32, 'no_infringement': 19,
                'low_infringement': 7, 'high_infringement': 4, 'critical_infringement': 3
            }),
            ("face-mask-detections", {
                'time': '2021-02-19 13:37:58', 'trend': 0.52, 'no_face': 44, 'face_with_mask': 8, 'face_without_mask': 1
            })
        ]
    )
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsLive::test_get_a_report_properly_id_all_I
    def test_get_a_report_properly_id_all_I(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = "ALL"

        response = client.get(f"/metrics/areas/{metric}/live?areas={area_id}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'time': '2020-12-16 20:26:48', 'trend': -40.6, 'average_occupancy': 278, 'max_occupancy': 374,
                'occupancy_threshold': 280, 'violations': 120
            }),
            ("social-distancing", {
                'time': '2021-02-19 13:37:58', 'trend': 0.82, 'detected_objects': 32, 'no_infringement': 19,
                'low_infringement': 7, 'high_infringement': 4, 'critical_infringement': 3
            }),
            ("face-mask-detections", {
                'time': '2021-02-19 13:37:58', 'trend': 0.52, 'no_face': 44, 'face_with_mask': 8, 'face_without_mask': 1
            })
        ]
    )
    def test_get_a_report_properly_id_all_II(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = "all"

        response = client.get(f"/metrics/areas/{metric}/live?areas={area_id}")

        assert response.status_code == 200
        assert response.json() == expected


# pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsHourly
class TestsGetMetricsHourly:
    """ HOURLY """
    """ Get Area Occupancy Hourly Report, GET /metrics/cameras/occupancy/hourly """
    """ Get Area Distancing Hourly Report, GET /metrics/cameras/social-distancing/hourly """
    """ Get Camera Face Mask Detections Hourly Report, GET /metrics/cameras/face-mask-detections/hourly """

    @pytest.mark.parametrize(
        "metric,date,expected",
        [
            ("occupancy", "2020-09-25", {
                'occupancy_threshold': [140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140,
                                        140, 140, 140, 140, 140, 140, 140, 140],
                'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 35.0, 60.0, 85.0, 111.0, 80.0, 60.0,
                                      125.0, 40.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 40.0, 60.0, 96.0, 120.0, 90.0, 71.0, 140.0,
                                  58.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("social-distancing", "2021-02-25", {
                'detected_objects': [180, 171, 117, 186, 96, 140, 111, 147, 175, 136, 139, 166, 135, 114, 196, 149, 185,
                                     17, 31, 32, 19, 38, 34, 50],
                'no_infringement': [37, 58, 23, 82, 38, 58, 13, 59, 63, 18, 88, 69, 68, 20, 79, 27, 72, 6, 7, 4, 6, 10,
                                    11, 18],
                'low_infringement': [46, 58, 45, 94, 12, 58, 42, 38, 85, 69, 22, 62, 24, 46, 85, 44, 89, 5, 5, 16, 4,
                                     12, 13, 17],
                'high_infringement': [76, 43, 39, 10, 43, 12, 45, 49, 13, 32, 15, 17, 41, 36, 15, 74, 15, 2, 1, 9, 8,
                                      13, 0, 15],
                'critical_infringement': [21, 12, 10, 0, 3, 12, 11, 1, 14, 17, 14, 18, 2, 12, 17, 4, 9, 4, 18, 3, 1, 3,
                                          10, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("face-mask-detections", "2021-02-25", {
                'no_face': [25, 48, 141, 79, 71, 4, 41, 36, 139, 84, 56, 90, 77, 27, 6, 2, 5, 2, 0, 0, 8, 3, 1, 2],
                'face_with_mask': [23, 38, 30, 58, 76, 84, 123, 90, 113, 32, 52, 66, 81, 125, 4, 2, 0, 1, 4, 1, 9, 5, 1,
                                   4],
                'face_without_mask': [87, 67, 105, 76, 115, 98, 82, 78, 125, 88, 72, 72, 116, 51, 1, 0, 7, 5, 3, 3, 3,
                                      8, 6, 5],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            })
        ]
    )
    def test_get_a_report_properly(self, config_rollback_areas, metric, date,
                                   expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                  0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
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
    def test_try_get_a_report_no_query_string(self, config_rollback_areas, metric, expected):
        """ It is important to highlight that 'config_rollback_areas' provides every report So, when we send
        the request '/metrics/areas/{metric}/hourly' default values will be loaded. As a result, the endpoint
        will look for a report for today. But, there is no report for today among provided reports.
        """

        area, area_2, client, config_sample_path = config_rollback_areas

        response = client.get(f"/metrics/areas/{metric}/hourly")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,date,expected",
        [
            ("occupancy", "2020-09-25", {
                'occupancy_threshold': [140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140,
                                        140, 140, 140, 140, 140, 140, 140, 140],
                'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 35.0, 60.0, 85.0, 111.0, 80.0, 60.0,
                                      125.0, 40.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 40.0, 60.0, 96.0, 120.0, 90.0, 71.0, 140.0,
                                  58.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("social-distancing", "2021-02-25", {
                'detected_objects': [288, 231, 155, 260, 150, 218, 199, 197, 277, 198, 233, 244, 167, 166, 330, 207,
                                     257, 51, 93, 96, 57, 114, 102, 150],
                'no_infringement': [63, 68, 27, 118, 48, 80, 33, 71, 91, 30, 122, 105, 76, 36, 113, 49, 78, 18, 21, 12,
                                    18, 30, 33, 54],
                'low_infringement': [66, 86, 53, 132, 34, 88, 56, 52, 107, 73, 24, 68, 44, 66, 123, 58, 119, 15, 15, 48,
                                     12, 36, 39, 51],
                'high_infringement': [108, 47, 45, 10, 59, 14, 77, 71, 37, 44, 45, 17, 41, 38, 43, 88, 35, 6, 3, 27, 24,
                                      39, 0, 45],
                'critical_infringement': [51, 30, 30, 0, 9, 36, 33, 3, 42, 51, 42, 54, 6, 26, 51, 12, 25, 12, 54, 9, 3,
                                          9, 30, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("face-mask-detections", "2021-02-25", {
                'no_face': [31, 54, 159, 83, 87, 8, 59, 52, 155, 84, 58, 94, 85, 39, 18, 6, 15, 6, 0, 0, 24, 9, 3, 6],
                'face_with_mask': [33, 46, 42, 76, 80, 90, 141, 104, 127, 38, 68, 72, 93, 139, 12, 6, 0, 3, 12, 3, 27,
                                   15, 3, 12],
                'face_without_mask': [91, 79, 105, 92, 129, 112, 100, 80, 143, 104, 84, 80, 126, 65, 3, 0, 21, 15, 9, 9,
                                      9, 24, 18, 15],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            })
        ]
    )
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsHourly::test_try_get_a_report_empty_area
    def test_try_get_a_report_empty_area(self, config_rollback_areas, metric, date,
                                         expected):
        """ If an area is not provided, it will search all reports for every existent area. """

        area, area_2, client, config_sample_path = config_rollback_areas

        response = client.get(f"/metrics/areas/{metric}/hourly?areas=&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_report_several_dates(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']
        date_1 = "2021-03-01"
        date_2 = "2021-03-02"

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}&date={date_1},{date_2}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                  0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
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
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsHourly::test_try_get_a_report_no_date_on_query_string
    def test_try_get_a_report_no_date_on_query_string(self, config_rollback_areas, metric, expected):
        """ It is important to highlight that 'config_rollback_areas' provides every report So, when we send
        the request '/metrics/areas/{metric}/hourly' without date, default date will be loaded. As a result, the
        endpoint will look for a report for today. But, there is no report for today among provided reports.
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_report_empty_date(self, config_rollback_areas, metric):
        """ Invalid date format """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}&date=")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_report_bad_format_date(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']
        date = "BAD_DATE"

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}&date={date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                  0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
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
    def test_try_get_a_report_non_existent_date(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']
        date = "2009-03-01"  # No data for this date

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,date,expected",
        [
            ("occupancy", "2020-09-25", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("social-distancing", "2021-02-25", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", "2021-02-25", {'detail': "Area with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_a_report_bad_id(self, config_rollback_areas, metric, date, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = 'BAD_ID'

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}&date={date}")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,date,expected",
        [
            ("occupancy", "2020-09-04", {
                'occupancy_threshold': [290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290,
                                        290, 140, 140, 140, 140, 140, 140, 140],
                'average_occupancy': [36.0, 69.0, 35.0, 70.0, 41.0, 65.0, 50.0, 70.0, 68.0, 58.0, 143.0, 163.0, 111.0,
                                      160.0, 191.0, 200.0, 124.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [40.0, 76.0, 38.0, 73.0, 45.0, 77.0, 58.0, 73.0, 89.0, 72.0, 158.0, 179.0, 129.0,
                                  169.0, 226.0, 220.0, 145.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("social-distancing", "2021-02-25", {
                'detected_objects': [288, 231, 155, 260, 150, 218, 199, 197, 277, 198, 233, 244, 167, 166, 330, 207,
                                     257, 51, 93, 96, 57, 114, 102, 150],
                'no_infringement': [63, 68, 27, 118, 48, 80, 33, 71, 91, 30, 122, 105, 76, 36, 113, 49, 78, 18, 21, 12,
                                    18, 30, 33, 54],
                'low_infringement': [66, 86, 53, 132, 34, 88, 56, 52, 107, 73, 24, 68, 44, 66, 123, 58, 119, 15, 15, 48,
                                     12, 36, 39, 51],
                'high_infringement': [108, 47, 45, 10, 59, 14, 77, 71, 37, 44, 45, 17, 41, 38, 43, 88, 35, 6, 3, 27, 24,
                                      39, 0, 45],
                'critical_infringement': [51, 30, 30, 0, 9, 36, 33, 3, 42, 51, 42, 54, 6, 26, 51, 12, 25, 12, 54, 9, 3,
                                          9, 30, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("face-mask-detections", "2021-02-25", {
                'no_face': [31, 54, 159, 83, 87, 8, 59, 52, 155, 84, 58, 94, 85, 39, 18, 6, 15, 6, 0, 0, 24, 9, 3, 6],
                'face_with_mask': [33, 46, 42, 76, 80, 90, 141, 104, 127, 38, 68, 72, 93, 139, 12, 6, 0, 3, 12, 3, 27,
                                   15, 3, 12],
                'face_without_mask': [91, 79, 105, 92, 129, 112, 100, 80, 143, 104, 84, 80, 126, 65, 3, 0, 21, 15, 9, 9,
                                      9, 24, 18, 15],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            })
        ]
    )
    def test_get_a_report_several_ids(self, config_rollback_areas, metric, date, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']
        area_id_2 = area_2['id']

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id},{area_id_2}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,date,expected",
        [
            ("occupancy", "2020-09-04", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("social-distancing", "2021-02-25", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", "2021-02-25", {'detail': "Area with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_a_report_several_ids_one_bad_id(self, config_rollback_areas, metric, date, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']
        area_id_2 = "BAD_ID"

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id},{area_id_2}&date={date}")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,date,expected",
        [
            ("occupancy", "2020-09-11", {
                'occupancy_threshold': [140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140, 140,
                                        140, 140, 140, 140, 140, 140, 140, 140],
                'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 40.0, 52.0, 125.0, 150.0, 86.0, 95.0,
                                      130.0, 143.0, 92.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 43.0, 63.0, 135.0, 153.0, 90.0, 101.0, 145.0,
                                  150.0, 97.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("social-distancing", "2021-02-16", {
                'detected_objects': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 180, 42, 0, 0, 0, 0, 0, 0],
                'no_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 120, 27, 0, 0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0],
                'high_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 51, 15, 0, 0, 0, 0, 0, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("face-mask-detections", "2021-02-16", {
                'no_face': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 207, 81, 0, 0, 0, 0, 0, 0],
                'face_with_mask': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'face_without_mask': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            })
        ]
    )
    def test_try_get_a_report_several_ids_one_no_report_for_given_date(self, config_rollback_areas, metric, date,
                                                                       expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area['id']
        area_id_2 = area_2['id']

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id},{area_id_2}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,date,expected",
        [
            ("occupancy", "2020-09-04", {
                'occupancy_threshold': [290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290, 290,
                                        290, 140, 140, 140, 140, 140, 140, 140],
                'average_occupancy': [36.0, 69.0, 35.0, 70.0, 41.0, 65.0, 50.0, 70.0, 68.0, 58.0, 143.0, 163.0, 111.0,
                                      160.0, 191.0, 200.0, 124.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [40.0, 76.0, 38.0, 73.0, 45.0, 77.0, 58.0, 73.0, 89.0, 72.0, 158.0, 179.0, 129.0,
                                  169.0, 226.0, 220.0, 145.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("social-distancing", "2021-02-25", {
                'detected_objects': [288, 231, 155, 260, 150, 218, 199, 197, 277, 198, 233, 244, 167, 166, 330, 207,
                                     257, 51, 93, 96, 57, 114, 102, 150],
                'no_infringement': [63, 68, 27, 118, 48, 80, 33, 71, 91, 30, 122, 105, 76, 36, 113, 49, 78, 18, 21, 12,
                                    18, 30, 33, 54],
                'low_infringement': [66, 86, 53, 132, 34, 88, 56, 52, 107, 73, 24, 68, 44, 66, 123, 58, 119, 15, 15, 48,
                                     12, 36, 39, 51],
                'high_infringement': [108, 47, 45, 10, 59, 14, 77, 71, 37, 44, 45, 17, 41, 38, 43, 88, 35, 6, 3, 27, 24,
                                      39, 0, 45],
                'critical_infringement': [51, 30, 30, 0, 9, 36, 33, 3, 42, 51, 42, 54, 6, 26, 51, 12, 25, 12, 54, 9, 3,
                                          9, 30, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("face-mask-detections", "2021-02-25", {
                'no_face': [31, 54, 159, 83, 87, 8, 59, 52, 155, 84, 58, 94, 85, 39, 18, 6, 15, 6, 0, 0, 24, 9, 3, 6],
                'face_with_mask': [33, 46, 42, 76, 80, 90, 141, 104, 127, 38, 68, 72, 93, 139, 12, 6, 0, 3, 12, 3, 27,
                                   15, 3, 12],
                'face_without_mask': [91, 79, 105, 92, 129, 112, 100, 80, 143, 104, 84, 80, 126, 65, 3, 0, 21, 15, 9, 9,
                                      9, 24, 18, 15],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            })
        ]
    )
    def test_get_a_report_properly_id_all(self, config_rollback_areas, metric, date, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = "ALL"

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected


# pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsDaily
class TestsGetMetricsDaily:
    """ DAILY """
    """ Get Area Occupancy Daily Report, GET /metrics/cameras/occupancy/daily """
    """ Get Area Distancing Daily Report, GET /metrics/cameras/social-distancing/daily """
    """ Get Camera Face Mask Detections Daily Report, GET /metrics/cameras/face-mask-detections/daily """

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [140, 140, 140], 'average_occupancy': [0.0, 83.0, 78.0],
                'max_occupancy': [0.0, 156.0, 163.0], 'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            }),
            ("social-distancing", {
                'detected_objects': [120, 161, 301], 'no_infringement': [35, 143, 183], 'low_infringement': [42, 2, 87],
                'high_infringement': [43, 9, 27], 'critical_infringement': [0, 7, 4],
                'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            }),
            ("face-mask-detections", {
                'no_face': [77, 114, 41], 'face_with_mask': [76, 188, 170], 'face_without_mask': [33, 39, 128],
                'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            })
        ]
    )
    def test_get_a_daily_report_properly(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2020-09-21"
        to_date = "2020-09-23"

        response = client.get(f"/metrics/areas/{metric}/daily?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0], 'average_occupancy': [0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0]
            }),
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0], 'low_infringement': [0, 0, 0, 0],
                'high_infringement': [0, 0, 0, 0], 'critical_infringement': [0, 0, 0, 0]
            }
             ),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0], 'face_without_mask': [0, 0, 0, 0]
            })
        ]
    )
    def test_try_get_a_daily_report_no_querystring(self, config_rollback_areas, metric, expected):
        """
        If no camera is provided, it will search all IDs for each existing camera.

        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=date.today().weekday(),
        weeks=4)" - "date.today()" and this date range (4 weeks ago from today) should never have values for any
        camera in order to pass the test. Moreover, we do not assert response.json()["weeks"] because will change
        depending on the date.
        """

        area, area_2, client, config_sample_path = config_rollback_areas

        response = client.get(f"/metrics/areas/{metric}/daily")

        assert response.status_code == 200
        for key in expected:
            assert response.json()[key] == expected[key]

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0], 'average_occupancy': [0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0]
            }),
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0], 'low_infringement': [0, 0, 0, 0],
                'high_infringement': [0, 0, 0, 0], 'critical_infringement': [0, 0, 0, 0]
            }
             ),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0], 'face_without_mask': [0, 0, 0, 0]
            })
        ]
    )
    def test_get_a_daily_report_only_id(self, config_rollback_areas, metric, expected):
        """
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=3)" - "date.today()"
        and this date range (4 weeks ago from today) should never have values for any camera in order to pass the
        test. Moreover, we do not assert response.json()["weeks"] because will change depending on the date.
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]

        response = client.get(f"/metrics/areas/{metric}/daily?areas={area_id}")

        assert response.status_code == 200
        for key in expected:
            assert response.json()[key] == expected[key]

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_get_a_daily_report_only_from_date(self, config_rollback_areas, metric):
        """
        Note that here as we do not send to_date, default value will take place, and to_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "2021-01-10" - "today".
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        from_date = "2021-01-10"

        response = client.get(f"/metrics/areas/{metric}/daily?from_date={from_date}")

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_get_a_daily_report_only_to_date(self, config_rollback_areas, metric):
        """ Note that here as we do not send from_date, default value will take place, and from_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=3)" - "2020-09-20" and
        this date range is probably wrong because from_date will be later than to_date.
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        to_date = "2021-01-10"

        response = client.get(f"/metrics/areas/{metric}/daily?to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [290, 290, 290], 'average_occupancy': [16.0, 155.0, 79.0],
                'max_occupancy': [21.0, 243.0, 183.0], 'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            }),
            ("social-distancing", {
                'detected_objects': [120, 457, 659], 'no_infringement': [35, 415, 461],
                'low_infringement': [42, 2, 125], 'high_infringement': [43, 19, 61],
                'critical_infringement': [0, 21, 12], 'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            }),
            ("face-mask-detections", {
                'no_face': [77, 150, 77], 'face_with_mask': [76, 400, 440], 'face_without_mask': [33, 91, 188],
                'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            })
        ]
    )
    def test_get_a_daily_report_no_areas_valid_range_of_dates(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        from_date = "2020-09-21"
        to_date = "2020-09-23"

        response = client.get(f"/metrics/areas/{metric}/daily?from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("social-distancing", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Area with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_a_daily_report_bad_id(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = "BAD_ID"
        from_date = "2020-09-21"
        to_date = "2020-09-23"

        response = client.get(f"/metrics/areas/{metric}/daily?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [290, 290, 290], 'average_occupancy': [16.0, 155.0, 79.0],
                'max_occupancy': [21.0, 243.0, 183.0], 'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            }),
            ("social-distancing", {
                'detected_objects': [120, 457, 659], 'no_infringement': [35, 415, 461],
                'low_infringement': [42, 2, 125], 'high_infringement': [43, 19, 61],
                'critical_infringement': [0, 21, 12], 'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            }),
            ("face-mask-detections", {
                'no_face': [77, 150, 77], 'face_with_mask': [76, 400, 440], 'face_without_mask': [33, 91, 188],
                'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            })
        ]
    )
    def test_get_a_daily_report_two_areas(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        area_id_2 = area_2["id"]
        from_date = "2020-09-21"
        to_date = "2020-09-23"

        response = client.get(
            f"/metrics/areas/{metric}/daily?areas={area_id},{area_id_2}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("social-distancing", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Area with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_a_daily_report_two_areas_one_bad_id(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        area_id_2 = "BAD_ID"
        from_date = "2020-09-21"
        to_date = "2020-09-23"

        response = client.get(
            f"/metrics/areas/{metric}/daily?areas={area_id},{area_id_2}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_daily_report_bad_format_both_dates(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "BAD_FORMAT"
        to_date = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/daily?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_daily_report_bad_format_from_date(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "BAD_FORMAT"
        to_date = "2020-09-23"

        response = client.get(f"/metrics/areas/{metric}/daily?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_daily_report_bad_format_to_date(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2020-09-23"
        to_date = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/daily?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_daily_report_from_date_is_after_to_date(self, config_rollback_areas, metric):
        """ Invalid range of dates, from_date doesn't come before to_date """
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2020-09-23"
        to_date = "2020-09-20"

        response = client.get(f"/metrics/areas/{metric}/daily?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0], 'average_occupancy': [0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0], 'dates': ['2008-05-15', '2008-05-16', '2008-05-17']
            }),
            ("social-distancing", {
                'detected_objects': [0, 0, 0], 'no_infringement': [0, 0, 0], 'low_infringement': [0, 0, 0],
                'high_infringement': [0, 0, 0], 'critical_infringement': [0, 0, 0],
                'dates': ['2008-05-15', '2008-05-16', '2008-05-17']
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0], 'face_with_mask': [0, 0, 0], 'face_without_mask': [0, 0, 0],
                'dates': ['2008-05-15', '2008-05-16', '2008-05-17']
            })
        ]
    )
    def test_get_a_daily_report_properly_but_no_data_for_given_dates(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2008-05-15"
        to_date = "2008-05-17"

        response = client.get(f"/metrics/areas/{metric}/daily?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,from_date,to_date,expected",
        [
            ("occupancy", "2020-09-28", "2020-10-01", {
                'occupancy_threshold': [140, 140, 140, 140], 'average_occupancy': [0.0, 83.0, 78.0, 74.0],
                'max_occupancy': [0.0, 156.0, 163.0, 140.0],
                'dates': ['2020-09-28', '2020-09-29', '2020-09-30', '2020-10-01']
            }),
            ("social-distancing", "2020-10-04", "2020-10-06", {
                'detected_objects': [127, 168, 66], 'no_infringement': [44, 65, 9], 'low_infringement': [33, 50, 8],
                'high_infringement': [50, 37, 37], 'critical_infringement': [0, 16, 12],
                'dates': ['2020-10-04', '2020-10-05', '2020-10-06']
            }),
            ("face-mask-detections", "2020-10-05", "2020-10-08", {
                'no_face': [11, 131, 119, 108], 'face_with_mask': [77, 64, 28, 87],
                'face_without_mask': [82, 123, 68, 30],
                'dates': ['2020-10-05', '2020-10-06', '2020-10-07', '2020-10-08']
            })
        ]
    )
    def test_get_a_daily_report_properly_but_data_for_only_one_of_given_areas(self, config_rollback_areas, metric,
                                                                              from_date, to_date, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        area_id_2 = area_2["id"]

        response = client.get(
            f"/metrics/areas/{metric}/daily?areas={area_id},{area_id_2}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_daily_report_bad_format_to_date(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2020-09-21"
        to_date = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/daily?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_daily_report_bad_format_from_date(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "BAD_FORMAT"
        to_date = "2020-09-21"

        response = client.get(f"/metrics/areas/{metric}/daily?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [290, 290, 290], 'average_occupancy': [16.0, 155.0, 79.0],
                'max_occupancy': [21.0, 243.0, 183.0], 'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            }),
            ("social-distancing", {
                'detected_objects': [120, 457, 659], 'no_infringement': [35, 415, 461],
                'low_infringement': [42, 2, 125], 'high_infringement': [43, 19, 61],
                'critical_infringement': [0, 21, 12], 'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            }),
            ("face-mask-detections", {
                'no_face': [77, 150, 77], 'face_with_mask': [76, 400, 440], 'face_without_mask': [33, 91, 188],
                'dates': ['2020-09-21', '2020-09-22', '2020-09-23']
            })
        ]
    )
    def test_get_a_report_properly_id_all(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = "ALL"
        from_date = "2020-09-21"
        to_date = "2020-09-23"

        response = client.get(
            f"/metrics/areas/{metric}/daily?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected


# pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsWeekly
class TestsGetMetricsWeekly:
    """ WEEKLY """
    """ Get Area Occupancy Weekly Report, GET /metrics/cameras/occupancy/weekly """
    """ Get Area Distancing Weekly Report, GET /metrics/cameras/social-distancing/weekly """
    """ Get Camera Face Mask Detections Weekly Report, GET /metrics/cameras/face-mask-detections/weekly """

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [140, 140, 140, 140, 140], 'average_occupancy': [0.0, 49.71, 53.0, 53.0, 0.0],
                'max_occupancy': [0.0, 163.0, 163.0, 163.0, 0.0],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']

            }),
            ("social-distancing", {
                'detected_objects': [20, 1662, 1358, 1426, 94], 'no_infringement': [4, 891, 772, 765, 33],
                'low_infringement': [14, 362, 365, 328, 59], 'high_infringement': [2, 392, 190, 292, 2],
                'critical_infringement': [0, 19, 30, 40, 0],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            }),
            ("face-mask-detections", {
                'no_face': [14, 549, 650, 401, 122], 'face_with_mask': [88, 1023, 920, 855, 91],
                'face_without_mask': [31, 522, 537, 567, 29],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            })
        ]
    )
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsWeekly::test_get_a_weekly_report_properly
    def test_get_a_weekly_report_properly(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0, 0], 'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0]
            }),
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
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsWeekly::test_get_a_weekly_report_no_querystring
    def test_get_a_weekly_report_no_querystring(self, config_rollback_areas, metric, expected):
        """
        If no area is provided, it will look for every existing area..

        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=date.today().weekday(),
        weeks=4)" - "date.today()" and this date range (4 weeks ago from today) should never have values for any
        camera in order to pass the test. Moreover, we do not assert response.json()["weeks"] because will change
        depending on the date.
        """

        area, area_2, client, config_sample_path = config_rollback_areas

        response = client.get(f"/metrics/areas/{metric}/weekly")

        assert response.status_code == 200
        for key in expected:
            assert response.json()[key] == expected[key]

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 140, 140, 140, 140], 'average_occupancy': [0.0, 41.86, 49.71, 53.0, 53.0],
                'max_occupancy': [0.0, 156.0, 163.0, 163.0, 163.0],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("social-distancing", {
                'detected_objects': [121, 1282, 1511, 1390, 1533], 'no_infringement': [38, 679, 848, 769, 825],
                'low_infringement': [22, 329, 315, 372, 393], 'high_infringement': [53, 237, 331, 218, 274],
                'critical_infringement': [8, 36, 19, 30, 40],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("face-mask-detections", {
                'no_face': [0, 472, 456, 728, 455], 'face_with_mask': [0, 753, 1090, 927, 820],
                'face_without_mask': [0, 578, 553, 447, 550],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            })
        ]
    )
    @freeze_time("2020-09-30")
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsWeekly::test_get_a_weekly_report_properly_weeks
    def test_get_a_weekly_report_properly_weeks(self, config_rollback_areas, metric, expected):
        """ Remember that time was mocked to 2020-09-30. """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        weeks = 5

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&weeks={weeks}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 140, 140, 140, 140], 'average_occupancy': [0.0, 41.86, 49.71, 53.0, 53.0],
                'max_occupancy': [0.0, 156.0, 163.0, 163.0, 163.0],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("social-distancing", {
                'detected_objects': [121, 1282, 1511, 1390, 1533], 'no_infringement': [38, 679, 848, 769, 825],
                'low_infringement': [22, 329, 315, 372, 393], 'high_infringement': [53, 237, 331, 218, 274],
                'critical_infringement': [8, 36, 19, 30, 40],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("face-mask-detections", {
                'no_face': [0, 472, 456, 728, 455], 'face_with_mask': [0, 753, 1090, 927, 820],
                'face_without_mask': [0, 578, 553, 447, 550],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            })
        ]
    )
    @freeze_time("2020-09-30")
    def test_get_a_weekly_report_properly_weeks_and_valid_ranges_of_dates(self, config_rollback_areas, metric,
                                                                          expected):
        """
        Remember that time was mocked to 2020-09-30.
        In addition, note that from_date and to_date should be ignored accordingly with the description.
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        weeks = 5
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(
            f"/metrics/areas/{metric}/weekly?areas={area_id}&weeks={weeks}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_bad_format_weeks(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        weeks = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&weeks={weeks}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_bad_format_weeks_and_valid_range_of_dates(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        weeks = "BAD_FORMAT"
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(
            f"/metrics/areas/{metric}/weekly?areas={area_id}&weeks={weeks}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_from_date_after_to_date(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2020-09-17"
        to_date = "2020-09-15"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0, 0], 'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0],
                'weeks': ['2007-03-08 2007-03-14', '2007-03-15 2007-03-21', '2007-03-22 2007-03-28',
                          '2007-03-29 2007-04-04', '2007-04-05 2007-04-11']
            }),
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0], 'high_infringement': [0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-14', '2007-03-15 2007-03-21', '2007-03-22 2007-03-28',
                          '2007-03-29 2007-04-04', '2007-04-05 2007-04-11']
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0, 0], 'face_without_mask': [0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-14', '2007-03-15 2007-03-21', '2007-03-22 2007-03-28',
                          '2007-03-29 2007-04-04', '2007-04-05 2007-04-11']
            })
        ]
    )
    @freeze_time("2007-04-12")
    def test_get_a_weekly_report_no_data_for_input_weeks(self, config_rollback_areas, metric,
                                                         expected):
        """
        Remember that time was mocked to 2007-04-12.
        Note that there is no data for given input.

        Remember that whether <weeks> is used: returned response will separate weeks in range taking a number of
        weeks ago, considering the week ended yesterday. While when we use from_date and to_date: returned response
        will separate weeks in range considering the week starts on Monday
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        weeks = 5

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&weeks={weeks}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0, 0, 0], 'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'weeks': ['2007-03-08 2007-03-11', '2007-03-12 2007-03-18', '2007-03-19 2007-03-25',
                          '2007-03-26 2007-04-01', '2007-04-02 2007-04-08', '2007-04-09 2007-04-11']
            }),
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0, 0], 'high_infringement': [0, 0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-11', '2007-03-12 2007-03-18', '2007-03-19 2007-03-25',
                          '2007-03-26 2007-04-01', '2007-04-02 2007-04-08', '2007-04-09 2007-04-11']
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0, 0, 0],
                'face_without_mask': [0, 0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-11', '2007-03-12 2007-03-18', '2007-03-19 2007-03-25',
                          '2007-03-26 2007-04-01', '2007-04-02 2007-04-08', '2007-04-09 2007-04-11']
            })
        ]
    )
    def test_get_a_weekly_report_no_data_for_input_range_of_dates(self, config_rollback_areas, metric, expected):
        """
        Remember that whether <weeks> is used: Separate weeks in range taking a number of weeks ago, considering the
        week ended yesterday. While when we use from_date and to_date: Separate weeks in range considering the week
        starts on Monday
        """
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2007-03-08"
        to_date = "2007-04-11"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_only_from_date(self, config_rollback_areas, metric):
        """
        Note that here as we do not send to_date, default value will take place, and to_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "2021-01-10" - "today".
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2021-01-10"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&from_date={from_date}")

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_only_to_date(self, config_rollback_areas, metric):
        """
        Note that here as we do not send from_date, default value will take place, and from_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=date.today().weekday(),
        weeks=4)" - "2020-09-20" and this date range is probably wrong because from_date will be later than to_date.
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        to_date = "2020-09-20"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_one_date_bad_format_I(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2007-03-08"
        to_date = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_one_date_bad_format_II(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "BAD_FORMAT"
        to_date = "2007-03-08"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_both_dates_bad_format(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = area["id"]
        from_date = "2007-03-08"
        to_date = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    # NO AREA

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [140, 290, 290, 290, 140], 'average_occupancy': [0.0, 63.43, 95.71, 87.57, 0.0],
                'max_occupancy': [0.0, 192.0, 235.0, 243.0, 0.0],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            }),
            ("social-distancing", {
                'detected_objects': [20, 3170, 2786, 2854, 94], 'no_infringement': [4, 2135, 1882, 1875, 33],
                'low_infringement': [14, 480, 511, 474, 59], 'high_infringement': [2, 504, 300, 402, 2],
                'critical_infringement': [0, 57, 90, 100, 0],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            }),
            ("face-mask-detections", {
                'no_face': [14, 719, 862, 571, 122], 'face_with_mask': [88, 2061, 1810, 1893, 91],
                'face_without_mask': [31, 864, 897, 909, 29],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            })
        ]
    )
    def test_get_a_weekly_report_properly_no_area(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(f"/metrics/areas/{metric}/weekly?from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 140, 290, 290, 290], 'average_occupancy': [0.0, 41.86, 78.86, 92.86, 75.0],
                'max_occupancy': [0.0, 156.0, 235.0, 243.0, 225.0],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("social-distancing", {
                'detected_objects': [121, 2352, 3019, 2818, 2961], 'no_infringement': [38, 1511, 2092, 1879, 1935],
                'low_infringement': [22, 437, 433, 518, 539], 'high_infringement': [53, 313, 443, 328, 384],
                'critical_infringement': [8, 88, 57, 90, 100],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("face-mask-detections", {
                'no_face': [0, 648, 626, 940, 625], 'face_with_mask': [0, 1373, 2128, 1817, 1858],
                'face_without_mask': [0, 878, 895, 807, 892],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            })
        ]
    )
    @freeze_time("2020-09-30")
    def test_get_a_weekly_report_properly_weeks_no_area(self, config_rollback_areas, metric, expected):
        """ Remember that time was mocked to 2020-09-30. """

        area, area_2, client, config_sample_path = config_rollback_areas
        weeks = 5

        response = client.get(f"/metrics/areas/{metric}/weekly?&weeks={weeks}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 140, 290, 290, 290], 'average_occupancy': [0.0, 41.86, 78.86, 92.86, 75.0],
                'max_occupancy': [0.0, 156.0, 235.0, 243.0, 225.0],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("social-distancing", {
                'detected_objects': [121, 2352, 3019, 2818, 2961], 'no_infringement': [38, 1511, 2092, 1879, 1935],
                'low_infringement': [22, 437, 433, 518, 539], 'high_infringement': [53, 313, 443, 328, 384],
                'critical_infringement': [8, 88, 57, 90, 100],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("face-mask-detections", {
                'no_face': [0, 648, 626, 940, 625], 'face_with_mask': [0, 1373, 2128, 1817, 1858],
                'face_without_mask': [0, 878, 895, 807, 892],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            })
        ]
    )
    @freeze_time("2020-09-30")
    def test_get_a_weekly_report_properly_weeks_and_valid_ranges_of_dates_no_area(self, config_rollback_areas, metric,
                                                                                  expected):
        """
        Remember that time was mocked to 2020-09-30.
        In addition, note that from_date and to_date should be ignored accordingly with the description.
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        weeks = 5
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(
            f"/metrics/areas/{metric}/weekly?&weeks={weeks}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_bad_format_weeks_no_area(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        weeks = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/weekly?weeks={weeks}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_bad_format_weeks_and_valid_range_of_dates_no_area(self, config_rollback_areas,
                                                                                       metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        weeks = "BAD_FORMAT"
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(
            f"/metrics/areas/{metric}/weekly?weeks={weeks}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_from_date_after_to_date_no_area(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        from_date = "2020-09-17"
        to_date = "2020-09-15"

        response = client.get(f"/metrics/areas/{metric}/weekly?from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0, 0], 'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0],
                'weeks': ['2007-03-08 2007-03-14', '2007-03-15 2007-03-21', '2007-03-22 2007-03-28',
                          '2007-03-29 2007-04-04', '2007-04-05 2007-04-11']
            }),
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0], 'high_infringement': [0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-14', '2007-03-15 2007-03-21', '2007-03-22 2007-03-28',
                          '2007-03-29 2007-04-04', '2007-04-05 2007-04-11']
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0, 0], 'face_without_mask': [0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-14', '2007-03-15 2007-03-21', '2007-03-22 2007-03-28',
                          '2007-03-29 2007-04-04', '2007-04-05 2007-04-11']
            })
        ]
    )
    @freeze_time("2007-04-12")
    def test_get_a_weekly_report_no_data_for_input_weeks_no_area(self, config_rollback_areas, metric,
                                                                 expected):
        """
        Remember that time was mocked to 2007-04-12.
        Note that there is no data for given input.

        Remember that whether <weeks> is used: returned response will separate weeks in range taking a number of
        weeks ago, considering the week ended yesterday. While when we use from_date and to_date: returned response
        will separate weeks in range considering the week starts on Monday
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        weeks = 5

        response = client.get(f"/metrics/areas/{metric}/weekly?weeks={weeks}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0, 0, 0], 'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'weeks': ['2007-03-08 2007-03-11', '2007-03-12 2007-03-18', '2007-03-19 2007-03-25',
                          '2007-03-26 2007-04-01', '2007-04-02 2007-04-08', '2007-04-09 2007-04-11']
            }),
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0, 0], 'high_infringement': [0, 0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-11', '2007-03-12 2007-03-18', '2007-03-19 2007-03-25',
                          '2007-03-26 2007-04-01', '2007-04-02 2007-04-08', '2007-04-09 2007-04-11']
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0, 0, 0],
                'face_without_mask': [0, 0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-11', '2007-03-12 2007-03-18', '2007-03-19 2007-03-25',
                          '2007-03-26 2007-04-01', '2007-04-02 2007-04-08', '2007-04-09 2007-04-11']
            })
        ]
    )
    def test_get_a_weekly_report_no_data_for_input_range_of_dates_no_area(self, config_rollback_areas, metric,
                                                                          expected):
        """
        Remember that whether <weeks> is used: Separate weeks in range taking a number of weeks ago, considering the
        week ended yesterday. While when we use from_date and to_date: Separate weeks in range considering the week
        starts on Monday
        """
        area, area_2, client, config_sample_path = config_rollback_areas
        from_date = "2007-03-08"
        to_date = "2007-04-11"

        response = client.get(f"/metrics/areas/{metric}/weekly?from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_only_from_date_no_area(self, config_rollback_areas, metric):
        """
        Note that here as we do not send to_date, default value will take place, and to_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "2021-01-10" - "today".
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        from_date = "2021-01-10"

        response = client.get(f"/metrics/areas/{metric}/weekly?from_date={from_date}")

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_only_to_date_no_area(self, config_rollback_areas, metric):
        """
        Note that here as we do not send from_date, default value will take place, and from_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=date.today().weekday(),
        weeks=4)" - "2020-09-20" and this date range is probably wrong because from_date will be later than to_date.
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        to_date = "2020-09-20"

        response = client.get(f"/metrics/areas/{metric}/weekly?to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_one_date_bad_format_I_no_area(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        from_date = "2007-03-08"
        to_date = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/weekly?from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_one_date_bad_format_II_no_area(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        from_date = "BAD_FORMAT"
        to_date = "2007-03-08"

        response = client.get(f"/metrics/areas/{metric}/weekly?from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_both_dates_bad_format_no_area(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        from_date = "2007-03-08"
        to_date = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/weekly?from_date={from_date}&to_date={to_date}")

        assert response.status_code == 400

    # SEVERAL AREAS

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [140, 290, 290, 290, 140],
                'average_occupancy': [0.0, 63.43, 95.71, 87.57, 0.0],
                'max_occupancy': [0.0, 192.0, 235.0, 243.0, 0.0],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            }),
            ("social-distancing", {
                'detected_objects': [20, 3170, 2786, 2854, 94], 'no_infringement': [4, 2135, 1882, 1875, 33],
                'low_infringement': [14, 480, 511, 474, 59], 'high_infringement': [2, 504, 300, 402, 2],
                'critical_infringement': [0, 57, 90, 100, 0],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            }),
            ("face-mask-detections", {
                'no_face': [14, 719, 862, 571, 122], 'face_with_mask': [88, 2061, 1810, 1893, 91],
                'face_without_mask': [31, 864, 897, 909, 29],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            })
        ]
    )
    def test_get_a_weekly_report_properly_two_areas(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&from_date={from_date}"
                              f"&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 140, 290, 290, 290],
                'average_occupancy': [0.0, 41.86, 78.86, 92.86, 75.0],
                'max_occupancy': [0.0, 156.0, 235.0, 243.0, 225.0],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("social-distancing", {
                'detected_objects': [121, 2352, 3019, 2818, 2961], 'no_infringement': [38, 1511, 2092, 1879, 1935],
                'low_infringement': [22, 437, 433, 518, 539], 'high_infringement': [53, 313, 443, 328, 384],
                'critical_infringement': [8, 88, 57, 90, 100],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("face-mask-detections", {
                'no_face': [0, 648, 626, 940, 625], 'face_with_mask': [0, 1373, 2128, 1817, 1858],
                'face_without_mask': [0, 878, 895, 807, 892],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            })
        ]
    )
    @freeze_time("2020-09-30")
    def test_get_a_weekly_report_properly_weeks_two_areas(self, config_rollback_areas, metric, expected):
        """ Remember that time was mocked to 2020-09-30. """
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        weeks = 5

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&weeks={weeks}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 140, 290, 290, 290],
                'average_occupancy': [0.0, 41.86, 78.86, 92.86, 75.0],
                'max_occupancy': [0.0, 156.0, 235.0, 243.0, 225.0],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("social-distancing", {
                'detected_objects': [121, 2352, 3019, 2818, 2961], 'no_infringement': [38, 1511, 2092, 1879, 1935],
                'low_infringement': [22, 437, 433, 518, 539], 'high_infringement': [53, 313, 443, 328, 384],
                'critical_infringement': [8, 88, 57, 90, 100],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("face-mask-detections", {
                'no_face': [0, 648, 626, 940, 625], 'face_with_mask': [0, 1373, 2128, 1817, 1858],
                'face_without_mask': [0, 878, 895, 807, 892],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            })
        ]
    )
    @freeze_time("2020-09-30")
    def test_get_a_weekly_report_properly_weeks_and_valid_ranges_of_dates_two_areas(self, config_rollback_areas,
                                                                                    metric,
                                                                                    expected):
        """
        Remember that time was mocked to 2020-09-30.
        In addition, note that from_date and to_date should be ignored accordingly with the description.
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        weeks = 5
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(
            f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&weeks={weeks}&from_date={from_date}"
            f"&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_bad_format_weeks_two_areas(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        weeks = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&weeks={weeks}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_bad_format_weeks_and_valid_range_of_dates_two_areas(self, config_rollback_areas,
                                                                                         metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        weeks = "BAD_FORMAT"
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(
            f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&weeks={weeks}&from_date={from_date}"
            f"&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_from_date_after_to_date_two_areas(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        from_date = "2020-09-17"
        to_date = "2020-09-15"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&from_date={from_date}"
                              f"&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0, 0], 'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0],
                'weeks': ['2007-03-08 2007-03-14', '2007-03-15 2007-03-21', '2007-03-22 2007-03-28',
                          '2007-03-29 2007-04-04', '2007-04-05 2007-04-11']
            }),
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0], 'high_infringement': [0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-14', '2007-03-15 2007-03-21', '2007-03-22 2007-03-28',
                          '2007-03-29 2007-04-04', '2007-04-05 2007-04-11']
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0, 0], 'face_without_mask': [0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-14', '2007-03-15 2007-03-21', '2007-03-22 2007-03-28',
                          '2007-03-29 2007-04-04', '2007-04-05 2007-04-11']
            })
        ]
    )
    @freeze_time("2007-04-12")
    def test_get_a_weekly_report_no_data_for_input_weeks_two_areas(self, config_rollback_areas, metric,
                                                                   expected):
        """
        Remember that time was mocked to 2007-04-12.
        Note that there is no data for given input.

        Remember that whether <weeks> is used: returned response will separate weeks in range taking a number of
        weeks ago, considering the week ended yesterday. While when we use from_date and to_date: returned response
        will separate weeks in range considering the week starts on Monday
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        weeks = 5

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&weeks={weeks}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 0, 0, 0, 0, 0], 'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'weeks': ['2007-03-08 2007-03-11', '2007-03-12 2007-03-18', '2007-03-19 2007-03-25',
                          '2007-03-26 2007-04-01', '2007-04-02 2007-04-08', '2007-04-09 2007-04-11']
            }),
            ("social-distancing", {
                'detected_objects': [0, 0, 0, 0, 0, 0], 'no_infringement': [0, 0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0, 0], 'high_infringement': [0, 0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-11', '2007-03-12 2007-03-18', '2007-03-19 2007-03-25',
                          '2007-03-26 2007-04-01', '2007-04-02 2007-04-08', '2007-04-09 2007-04-11']
            }),
            ("face-mask-detections", {
                'no_face': [0, 0, 0, 0, 0, 0], 'face_with_mask': [0, 0, 0, 0, 0, 0],
                'face_without_mask': [0, 0, 0, 0, 0, 0],
                'weeks': ['2007-03-08 2007-03-11', '2007-03-12 2007-03-18', '2007-03-19 2007-03-25',
                          '2007-03-26 2007-04-01', '2007-04-02 2007-04-08', '2007-04-09 2007-04-11']
            })
        ]
    )
    def test_get_a_weekly_report_no_data_for_input_range_of_dates_two_areas(self, config_rollback_areas, metric,
                                                                            expected):
        """
        Remember that whether <weeks> is used: Separate weeks in range taking a number of weeks ago, considering the
        week ended yesterday. While when we use from_date and to_date: Separate weeks in range considering the week
        starts on Monday
        """
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        from_date = "2007-03-08"
        to_date = "2007-04-11"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&from_date={from_date}"
                              f"&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_only_from_date_two_areas(self, config_rollback_areas, metric):
        """
        Note that here as we do not send to_date, default value will take place, and to_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "2021-01-10" - "today".
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        from_date = "2021-01-10"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&from_date={from_date}")

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_only_to_date_two_areas(self, config_rollback_areas, metric):
        """
        Note that here as we do not send from_date, default value will take place, and from_date will be
        date.today().
        WARNING: We could not mock the date.today() when the function is called within default query parameters.
        So, we must be careful because the data range will be: "date.today() - timedelta(days=date.today().weekday(),
        weeks=4)" - "2020-09-20" and this date range is probably wrong because from_date will be later than to_date.
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        to_date = "2020-09-20"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_one_date_bad_format_I_two_areas(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        from_date = "2007-03-08"
        to_date = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&from_date={from_date}"
                              f"&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_one_date_bad_format_II_two_areas(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        from_date = "BAD_FORMAT"
        to_date = "2007-03-08"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&from_date={from_date}"
                              f"&to_date={to_date}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    def test_try_get_a_weekly_report_both_dates_bad_format_two_areas(self, config_rollback_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id_1 = area["id"]
        area_id_2 = area_2["id"]
        from_date = "2007-03-08"
        to_date = "BAD_FORMAT"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id_1},{area_id_2}&from_date={from_date}"
                              f"&to_date={to_date}")

        assert response.status_code == 400

    # Non existent area

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("social-distancing", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Area with id 'BAD_ID' does not exist"})
        ]
    )
    def test_try_get_a_weekly_report_bad_area_id(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = "BAD_ID"
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("social-distancing", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Area with id 'BAD_ID' does not exist"})
        ]
    )
    @freeze_time("2020-09-30")
    def test_try_get_a_weekly_report_weeks_bad_area_id(self, config_rollback_areas, metric, expected):
        """ Remember that time was mocked to 2020-09-30. """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = "BAD_ID"
        weeks = 5

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&weeks={weeks}")

        assert response.status_code == 404
        assert response.json() == expected

    # Area = "ALL"

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [0, 140, 290, 290, 290],
                'average_occupancy': [0.0, 41.86, 78.86, 92.86, 75.0],
                'max_occupancy': [0.0, 156.0, 235.0, 243.0, 225.0],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("social-distancing", {
                'detected_objects': [121, 2352, 3019, 2818, 2961], 'no_infringement': [38, 1511, 2092, 1879, 1935],
                'low_infringement': [22, 437, 433, 518, 539], 'high_infringement': [53, 313, 443, 328, 384],
                'critical_infringement': [8, 88, 57, 90, 100],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            }),
            ("face-mask-detections", {
                'no_face': [0, 648, 626, 940, 625], 'face_with_mask': [0, 1373, 2128, 1817, 1858],
                'face_without_mask': [0, 878, 895, 807, 892],
                'weeks': ['2020-08-26 2020-09-01', '2020-09-02 2020-09-08', '2020-09-09 2020-09-15',
                          '2020-09-16 2020-09-22', '2020-09-23 2020-09-29']
            })
        ]
    )
    @freeze_time("2020-09-30")
    def test_get_a_weekly_report_properly_weeks_and_valid_ranges_of_dates_id_all(self, config_rollback_areas,
                                                                                    metric,
                                                                                    expected):
        """
        Remember that time was mocked to 2020-09-30.
        """

        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = "ALL"
        weeks = 5

        response = client.get(
            f"/metrics/areas/{metric}/weekly?areas={area_id}&weeks={weeks}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [140, 290, 290, 290, 140],
                'average_occupancy': [0.0, 63.43, 95.71, 87.57, 0.0],
                'max_occupancy': [0.0, 192.0, 235.0, 243.0, 0.0],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            }),
            ("social-distancing", {
                'detected_objects': [20, 3170, 2786, 2854, 94], 'no_infringement': [4, 2135, 1882, 1875, 33],
                'low_infringement': [14, 480, 511, 474, 59], 'high_infringement': [2, 504, 300, 402, 2],
                'critical_infringement': [0, 57, 90, 100, 0],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            }),
            ("face-mask-detections", {
                'no_face': [14, 719, 862, 571, 122], 'face_with_mask': [88, 2061, 1810, 1893, 91],
                'face_without_mask': [31, 864, 897, 909, 29],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            })
        ]
    )
    def test_get_a_weekly_report_properly_id_all(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = "ALL"
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [140, 290, 290, 290, 140],
                'average_occupancy': [0.0, 63.43, 95.71, 87.57, 0.0],
                'max_occupancy': [0.0, 192.0, 235.0, 243.0, 0.0],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            }),
            ("social-distancing", {
                'detected_objects': [20, 3170, 2786, 2854, 94], 'no_infringement': [4, 2135, 1882, 1875, 33],
                'low_infringement': [14, 480, 511, 474, 59], 'high_infringement': [2, 504, 300, 402, 2],
                'critical_infringement': [0, 57, 90, 100, 0],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            }),
            ("face-mask-detections", {
                'no_face': [14, 719, 862, 571, 122], 'face_with_mask': [88, 2061, 1810, 1893, 91],
                'face_without_mask': [31, 864, 897, 909, 29],
                'weeks': ['2020-09-06 2020-09-06', '2020-09-07 2020-09-13', '2020-09-14 2020-09-20',
                          '2020-09-21 2020-09-27', '2020-09-28 2020-09-28']
            })
        ]
    )
    def test_get_a_weekly_report_properly_ids_all_and_another_valid(self, config_rollback_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_areas
        area_id = "5,aLl"
        from_date = "2020-09-06"
        to_date = "2020-09-28"

        response = client.get(f"/metrics/areas/{metric}/weekly?areas={area_id}&from_date={from_date}&to_date={to_date}")

        assert response.status_code == 200
        assert response.json() == expected
