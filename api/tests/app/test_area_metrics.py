import datetime
import pytest
from freezegun import freeze_time
import numpy as np
# The line below is absolutely necessary. Fixtures are passed as arguments to test functions. That is why IDE could
# not recognized them.
from api.tests.utils.fixtures_tests import reports_simulation_areas, config_rollback_create_areas


# TODO: avisar que en: GET /metrics/cameras/social-distancing/live, el texto del costado esta mal.

# TODO: El trend ni puta idea que es.


# pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsLive
class TestsGetMetricsLive:
    """ LIVE """
    """ Get Area Occupancy Live, GET /metrics/cameras/occupancy/live """
    """ Get Area Distancing Live Report, GET /metrics/cameras/social-distancing/live """
    """ Get Camera Face Mask Detections Live, GET /metrics/cameras/face-mask-detections/live """

    # TODO: Ask if this behaviour is right. This one, probably yes, it sums every report from the cameras in the area.
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
    # TODO: Aca lo de las areas de distintas fechas de las camaras tambien vale.
    #  Ademas, si vamos al .csv de live en social-distancing, vamos a ver que hay disitntas fechas y sin embargo se toma la ulitma linea. Lo mismo con face-mask.
    def test_get_a_report_properly(self, config_rollback_create_areas, reports_simulation_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']

        response = client.get(f"/metrics/areas/{metric}/live?areas={area_id}")

        assert response.status_code == 200
        assert response.json() == expected

    # TODO: Ask if this behaviour is right. As no area was given, it took all areas. And sums every report.
    #  we have to mock this, in order to have the same result in every computer.
    #  I believe we should mock get_entities(), but do not waste effort if the behaviour is wrong.
    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'time': '2020-12-16 20:26:48', 'trend': -44.13, 'average_occupancy': 360, 'max_occupancy': 364,
                'occupancy_threshold': 580, 'violations': 380
            }),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsLive::test_try_get_a_report_no_areas
    def test_try_get_a_report_no_areas(self, config_rollback_create_areas, reports_simulation_areas, metric, expected):
        """
        area, area_2, client, config_sample_path = config_rollback_create_areas

        response = client.get(f"/metrics/areas/{metric}/live?areas=")

        import pdb
        pdb.set_trace()
        assert response.status_code == 400
        assert response.json() == expected
        """
        pass

    # TODO: Ask if this behaviour is right. As no area was given, it took all areas. And sums every report.
    #  we have to mock this, in order to have the same result in every computer.
    #  I believe we should mock get_entities(), but do not waste effort if the behaviour is wrong.
    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsLive::test_try_get_a_report_no_query_string
    def test_try_get_a_report_no_query_string(self, config_rollback_create_areas, reports_simulation_areas, metric,
                                              expected):
        """
        area, area_2, client, config_sample_path = config_rollback_create_areas

        response = client.get(f"/metrics/areas/{metric}/live")
        import pdb
        pdb.set_trace()
        assert response.status_code == 400
        assert response.json() == expected
        """

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("social-distancing", {'detail': "Area with id 'BAD_ID' does not exist"}),
            ("face-mask-detections", {'detail': "Area with id 'BAD_ID' does not exist"})
        ]
    )
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsLive::test_try_get_a_report_bad_id
    def test_try_get_a_report_bad_id(self, config_rollback_create_areas, reports_simulation_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
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
    # TODO: Aca lo de las areas de distintas fechas tambien vale.
    #  Sucede tambine lo de que los live no coinciden las fechas, y se toma el ultimo renglon igual.
    def test_get_a_report_properly_two_areas(self, config_rollback_create_areas, reports_simulation_areas, metric,
                                             expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
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
    def test_try_get_a_report_for_two_areas_one_non_existent_id(self, config_rollback_create_areas,
                                                                reports_simulation_areas, metric, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id_1 = area['id']
        area_id_2 = 'non_existent_id'

        response = client.get(f"/metrics/areas/{metric}/live?areas={area_id_1},{area_id_2}")

        assert response.status_code == 404
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
    def test_get_a_report_properly(self, config_rollback_create_areas, reports_simulation_areas, metric, date,
                                   expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {
                'occupancy_threshold': [300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 0, 0,
                                        0, 0, 0, 0, 0, 0, 0],
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
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsHourly::test_try_get_a_report_no_query_string
    @freeze_time("2008-10-30")
    def test_try_get_a_report_no_query_string(self, config_rollback_create_areas, reports_simulation_areas, metric,
                                              expected):
        """ Here we mock date.today() because when we do not send date as a query
        string, date.today() is used instead. We have to make sure that the mocked date does not have reports for the
        used areas."""

        area, area_2, client, config_sample_path = config_rollback_create_areas

        response = client.get(f"/metrics/areas/{metric}/hourly")
        # TODO: AYUDA, date.today() se mockea, pero no se guarda en date.
        #  Cambiar date a date_now o algo asi, y mostrar.

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,date,expected",
        [
            ("occupancy", "2020-09-25", {
                'occupancy_threshold': [300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 0, 0,
                                        0, 0, 0, 0, 0, 0, 0],
                'average_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'max_occupancy': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                  0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("social-distancing", "2021-02-25", {
                'detected_objects': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'no_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'low_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'high_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'critical_infringement': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            }),
            ("face-mask-detections", "2021-02-25", {
                'no_face': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'face_with_mask': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'face_without_mask': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'hours': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
            })
        ]
    )
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsHourly::test_try_get_a_report_empty_area
    # TODO: Ask if this behaviour is right. As no area was given, it took all areas. And sums every report.
    #  we have to mock this, in order to have the same result in every computer.
    #  I believe we should mock get_entities(), but do not waste effort if the behaviour is wrong.
    def test_try_get_a_report_empty_area(self, config_rollback_create_areas, reports_simulation_areas, metric, date,
                                         expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        response = client.get(f"/metrics/areas/{metric}/hourly?areas=&date={date}")

        assert response.status_code == 200
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric",
        ["occupancy", "social-distancing", "face-mask-detections"]
    )
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsHourly::test_try_get_a_report_several_dates
    def test_try_get_a_report_several_dates(self, config_rollback_create_areas, reports_simulation_areas, metric):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']
        date_1 = "2021-03-01"
        date_2 = "2021-03-02"

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}&date={date_1},{date_2}")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    def test_try_get_a_report_no_date_on_query_string(self, config_rollback_create_areas, reports_simulation_areas,
                                                      metric, expected):
        """ areas will be every area, and we will hace same problem as above (any quuery string).

        # TODO: AYUDA, date.today() se mockea, pero no se guarda en date.
        #  Cambiar date a date_now o algo asi, y mostrar.
        """
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id}")

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
    def test_try_get_a_report_empty_date(self, config_rollback_create_areas, reports_simulation_areas, metric,
                                         expected):
        """ areas will be every area, and we will hace same problem as above (any quuery string).

        # TODO: AYUDA, date.today() se mockea, pero no se guarda en date.
        #  Cambiar date a date_now o algo asi, y mostrar.
        """
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
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsHourly::test_try_get_a_report_bad_format_date
    def test_try_get_a_report_bad_format_date(self, config_rollback_create_areas, reports_simulation_areas, metric,
                                              expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
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
    def test_try_get_a_report_non_existent_date(self, config_rollback_create_areas, reports_simulation_areas, metric,
                                                expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
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
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsHourly::test_try_get_a_report_bad_id
    def test_try_get_a_report_bad_id(self, config_rollback_create_areas, reports_simulation_areas, metric, date,
                                     expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
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
    def test_get_a_report_several_ids(self, config_rollback_create_areas, reports_simulation_areas, metric, date,
                                      expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
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
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsHourly::test_try_get_a_report_several_ids_one_bad_id
    def test_try_get_a_report_several_ids_one_bad_id(self, config_rollback_create_areas, reports_simulation_areas,
                                                     metric, date, expected):
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']
        area_id_2 = "BAD_ID"

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id},{area_id_2}&date={date}")

        assert response.status_code == 404
        assert response.json() == expected

    @pytest.mark.parametrize(
        "metric,expected",
        [
            ("occupancy", {}),
            ("social-distancing", {}),
            ("face-mask-detections", {})
        ]
    )
    # pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsHourly::test_try_get_a_report_several_ids_one_no_report_for_given_date
    def test_try_get_a_report_several_ids_one_no_report_for_given_date(self, metric, expected):
        # Ver que pasa cuando normalmente una sola no tiene fecha
        area, area_2, client, config_sample_path = config_rollback_create_areas
        area_id = area['id']
        area_id_2 = 43  # Hay que crear una id valida, pero que no tenga fecha
        date = "2021-03-01"

        response = client.get(f"/metrics/areas/{metric}/hourly?areas={area_id},{area_id_2}&date={date}")

        assert response.status_code == 200
        assert response.json() == expected


# pytest -v api/tests/app/test_area_metrics.py::TestsGetMetricsDaily
class TestsGetMetricsDaily:
    """ DAILY """
    """ Get Area Occupancy Daily Report, GET /metrics/cameras/occupancy/daily """
    """ Get Area Distancing Daily Report, GET /metrics/cameras/social-distancing/daily """
    """ Get Camera Face Mask Detections Daily Report, GET /metrics/cameras/face-mask-detections/daily """

    def test_create_area(self, config_rollback_create_areas, reports_simulation):
        area, area_2, client, config_sample_path_to_modify = config_rollback_create_areas

        # La info sale de los distintos reports.csv, de las camaras si la metric es FACEMASK o SOCIALDISTANCING, y de areas si es OCCUPANCY.
        # Un area tiene camaras, si es FACEMASK o SOCIALDISTANCING, se va a buscar a los reportes de las camaras.
        # response = client.get(f"/metrics/areas/social-distancing/daily?areas={area_id}&from_date=2020-09-06&to_date=2020-09-09")
