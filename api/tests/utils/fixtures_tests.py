import pytest
import shutil

from fastapi.testclient import TestClient

# from api.tests.utils.common_variables import default
from libs.config_engine import ConfigEngine
from api.settings import Settings
from api.tests.utils.common_functions import create_app_config


@pytest.fixture
def config_rollback():
    config_sample_path = '/repo/api/tests/data/config-x86-openvino_TEMPLATE.ini'
    config = ConfigEngine(config_sample_path)
    Settings(config=config)

    # Here, to import ProcessorAPI successfully, "Settings" must be previously initialized with a config, that is why
    # import order matters
    from api.processor_api import ProcessorAPI

    app_instance = ProcessorAPI()
    api = app_instance.app
    client = TestClient(api)
    yield client, config_sample_path

    original = '/repo/api/tests/data/config-x86-openvino.ini'
    target = '/repo/api/tests/data/config-x86-openvino_TEMPLATE.ini'

    shutil.copyfile(original, target)


@pytest.fixture
def app_config():
    app_config = create_app_config()
    return app_config
