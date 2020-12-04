from fastapi import APIRouter
from pydantic import ValidationError
from starlette import status
from starlette.exceptions import HTTPException
from typing import Optional

from api.models.area_logger import AreaLoggerDTO, AreaLoggerListDTO, FileSystemLoggerDTO
from api.utils import (
    extract_config, handle_response, update_config, map_section_from_config, map_to_config_file_format)

area_loggers_router = APIRouter()


def get_area_loggers():
    config = extract_config(config_type="area_loggers")
    return [map_section_from_config(x, config) for x in config.keys()]


def get_area_loggers_model(logger):
    if logger.name == "file_system_logger":
        return FileSystemLoggerDTO
    else:
        raise ValueError(f"Not supported logger named: {logger.name}")


@area_loggers_router.get("", response_model=AreaLoggerListDTO,
                         response_model_exclude_none=True)
def list_area_loggers():
    """
        Returns the list of area logger configured in the processor.
    """
    return {
        "areasLoggers": get_area_loggers()
    }


@area_loggers_router.get("/{logger_name}", response_model=AreaLoggerDTO,
                         response_model_exclude_none=True)
def get_area_loggerss(logger_name: str):
    """
    Returns the configuration related to the area logger <logger_name>.
    """
    logger = next((ps for ps in get_area_loggers() if ps["name"] == logger_name), None)
    if not logger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The logger: {logger_name} does not exist")
    return logger


@area_loggers_router.post("", response_model=AreaLoggerDTO,
                          status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
async def create_logger(new_logger: AreaLoggerDTO, reboot_processor: Optional[bool] = True):
    """
    Adds a logger.
    """
    config_dict = extract_config()
    loggers_index = [int(x[-1]) for x in config_dict.keys() if x.startswith("AreaLogger_")]
    loggers = get_area_loggers()
    logger_model = get_area_loggers_model(new_logger)
    # Validate that the specific logger's fields are correctly set
    try:
        logger_model(**new_logger.dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if new_logger.name in [ps["name"] for ps in loggers]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logger already exists")
    logger_file = map_to_config_file_format(new_logger, True)
    index = 0
    if loggers_index:
        index = max(loggers_index) + 1
    config_dict[f"AreaLogger_{index}"] = logger_file
    success = update_config(config_dict, reboot_processor)
    return handle_response(logger_file, success, status.HTTP_201_CREATED)


@area_loggers_router.put("/{logger_name}", response_model=AreaLoggerDTO)
async def edit_logger(logger_name: str, edited_logger: AreaLoggerDTO,
                      reboot_processor: Optional[bool] = True):
    """
    Edits the configuration related to the logger <logger_name>
    """
    edited_logger.name = logger_name
    config_dict = extract_config()
    edited_logger_section = next((
        key for key, value in config_dict.items()
        if key.startswith("AreaLogger_") and value["Name"] == logger_name
    ), None)
    if not edited_logger_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The logger: {logger_name} does not exist")
    logger_model = get_area_loggers_model(edited_logger)
    # Validate that the specific logger's fields are correctly set
    try:
        logger_model(**edited_logger.dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    logger_file = map_to_config_file_format(edited_logger, True)
    config_dict[edited_logger_section] = logger_file
    success = update_config(config_dict, reboot_processor)
    return handle_response(logger_file, success)


@area_loggers_router.delete("/{logger_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_logger(logger_name: str, reboot_processor: Optional[bool] = True):
    """
    Deletes the configuration related to the postprocessor <logger_name>
    """
    config_dict = extract_config()
    logger_section = next((
        key for key, value in config_dict.items()
        if key.startswith("AreaLogger_") and value["Name"] == logger_name
    ), None)
    if not logger_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The logger: {logger_name} does not exist")

    config_dict.pop(logger_section)
    success = update_config(config_dict, reboot_processor)
    return handle_response(None, success, status.HTTP_204_NO_CONTENT)
