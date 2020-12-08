from fastapi import APIRouter

from api.models.api import ApiDTO
from api.utils import extract_config, map_section_from_config

api_router = APIRouter()


@api_router.get("", response_model=ApiDTO)
def get_api_config():
    """
    Returns the api configuration of the processor
    """
    return map_section_from_config("API", extract_config())
