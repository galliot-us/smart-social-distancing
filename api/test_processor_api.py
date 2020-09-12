from fastapi.testclient import TestClient
from libs.config_engine import ConfigEngine
from api.models.config_keys import Config
from api.processor_api import ProcessorAPI
import pytest
import humps
import copy

config_path='/repo/config-coral.ini'
config = ConfigEngine(config_path)
app_instance = ProcessorAPI(config)
api = app_instance.app
client = TestClient(api)


sample_config_path='/repo/api/config-sample.ini'
config_backup_path='/repo/config-coral-backup.ini'

# make a copy for config file

# read sample config file
config_sample = ConfigEngine(sample_config_path)
sections = config_sample.get_sections()
config_sample_json = {}

for section in sections:
    config_sample_json[section] = config_sample.get_section_dict(section)

config_sample_json = humps.decamelize(config_sample_json)

#@pytest.mark.order1
def test_set_config():
    response = client.post(
        "/set-config",
        json=config_sample_json,
    )
    assert response.status_code == 200
    assert response.json() == config_sample_json

#@pytest.mark.order2
def test_set_invalid_video_path():
    wrong_json = copy.deepcopy(config_sample_json)
    wrong_json['app']['video_path'] = 'wrong_path'
    expected_response = {'detail': [{'loc': ['body', 'app', 'video_path'], 'msg': 'Failed to load video. The video URI is not valid', 'type': 'value_error'}]}
    expected_response['body'] = wrong_json
    response = client.post(
        "/set-config",
        json=wrong_json,
    )
    assert response.status_code == 400
    assert response.json() == expected_response

#@pytest.mark.order3
def test_get_config():
    config = ConfigEngine(config_path)
    app_instance = ProcessorAPI(config)
    api = app_instance.app
    client = TestClient(api)

    response_get = client.get("/get-config")

    assert response_get.status_code == 200
    assert response_get.json() == config_sample_json
