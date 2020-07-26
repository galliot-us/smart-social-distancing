from fastapi.testclient import TestClient
import os
import sys
sys.path.append("..")
from libs.config_engine import ConfigEngine
from api.config_keys import Config 
from api.processor_api import ProcessorAPI
import pytest

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

#@pytest.mark.order1
def test_set_config():
    response = client.post(
    "/set-config",
    json=config_sample_json,
    )
    assert response.status_code == 200
    assert response.json() == config_sample_json


#@pytest.mark.order2
def test_get_config():

    config = ConfigEngine(config_path)
    app_instance = ProcessorAPI(config)
    api = app_instance.app
    client = TestClient(api)

    response_get = client.get("/get-config")

    assert response_get.status_code == 200
    assert response_get.json() == config_sample_json
    
