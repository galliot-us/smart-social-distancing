from fastapi import APIRouter

from api.models.api import ApiDTO
from api.utils import get_config

api_router = APIRouter()


def map_api(config):
    api_section = config.get_section_dict("API")
    return {
        "host": api_section["Host"],
        "port": api_section["Port"],
        "SSLEnabled": api_section["SSLEnabled"],
        "SSLCertificateFile": api_section["SSLCertificateFile"],
        "SSLKeyFile": api_section["SSLKeyFile"],
    }


@api_router.get("", response_model=ApiDTO)
def get_app_config():
    """
    Returns the api configuration of the processor
    """
    return map_api(get_config())
