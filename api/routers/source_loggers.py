from fastapi import APIRouter
from pydantic import ValidationError
from starlette import status
from starlette.exceptions import HTTPException
from typing import Optional

from api.models.source_logger import (
    SourceLoggerDTO, SourceLoggerListDTO, VideoLoggerDTO, S3LoggerDTO, FileSystemLoggerDTO, WebHookLogger)
from api.utils import (
    extract_config, handle_response, update_config, pascal_to_camel_case, camel_to_pascal_case)

source_loggers_router = APIRouter()


def map_source_logger(logger_name, config):
    logger_section = config[logger_name]
    logger_mapped = {}
    for key, value in logger_section.items():
        logger_mapped[pascal_to_camel_case(key)] = value
    return logger_mapped


def map_to_source_logger_file_format(logger: SourceLoggerDTO):
    logger_dict = logger.dict(exclude_none=True)
    logger_file_dict = {}
    for key, value in logger_dict.items():
        logger_file_dict[camel_to_pascal_case(key)] = str(value)
    return logger_file_dict


def get_source_logger():
    config = extract_config(config_type="source_loggers")
    return [map_source_logger(x, config) for x in config.keys()]


def get_source_logger_model(logger):
    if logger.name == "video_logger":
        return VideoLoggerDTO
    elif logger.name == "s3_logger":
        return S3LoggerDTO
    elif logger.name == "file_system_logger":
        return FileSystemLoggerDTO
    elif logger.name == "web_hook_logger":
        return WebHookLogger
    else:
        raise ValueError(f"Not supported logger named: {logger.name}")


@source_loggers_router.get("", response_model=SourceLoggerListDTO,
                           response_model_exclude_none=True)
def list_source_loggers():
    """
        Returns the list of source logger configured in the processor.
    """
    return {
        "sourcesLoggers": get_source_logger()
    }


@source_loggers_router.get("/{logger_name}", response_model=SourceLoggerDTO,
                           response_model_exclude_none=True)
def get_source_loggers(logger_name: str):
    """
    Returns the configuration related to the source logger <logger_name>.
    """
    logger = next((ps for ps in get_source_logger() if ps["name"] == logger_name), None)
    if not logger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The logger: {logger_name} does not exist")
    return logger


@source_loggers_router.post("", response_model=SourceLoggerDTO,
                            status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
async def create_logger(new_logger: SourceLoggerDTO, reboot_processor: Optional[bool] = True):
    """
    Adds a logger.
    """
    config_dict = extract_config()
    loggers_index = [int(x[-1]) for x in config_dict.keys() if x.startswith("SourceLogger_")]
    loggers = get_source_logger()
    logger_model = get_source_logger_model(new_logger)
    # Validate that the specific logger's fields are correctly set
    try:
        logger_model(**new_logger.dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if new_logger.name in [ps["name"] for ps in loggers]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logger already exists")
    logger_file = map_to_source_logger_file_format(new_logger)
    index = 0
    if loggers_index:
        index = max(loggers_index) + 1
    config_dict[f"SourceLogger_{index}"] = logger_file
    success = update_config(config_dict, reboot_processor)
    return handle_response(logger_file, success, status.HTTP_201_CREATED)


@source_loggers_router.put("/{logger_name}", response_model=SourceLoggerDTO)
async def edit_logger(logger_name: str, edited_logger: SourceLoggerDTO,
                      reboot_processor: Optional[bool] = True):
    """
    Edits the configuration related to the logger <logger_name>
    """
    edited_logger.name = logger_name
    config_dict = extract_config()
    edited_logger_section = next((
        key for key, value in config_dict.items()
        if key.startswith("SourceLogger_") and value["Name"] == logger_name
    ), None)
    if not edited_logger_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The logger: {logger_name} does not exist")
    logger_model = get_source_logger_model(edited_logger)
    # Validate that the specific logger's fields are correctly set
    try:
        logger_model(**edited_logger.dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    logger_file = map_to_source_logger_file_format(edited_logger)
    config_dict[edited_logger_section] = logger_file
    success = update_config(config_dict, reboot_processor)
    return handle_response(logger_file, success)


@source_loggers_router.delete("/{logger_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(logger_name: str, reboot_processor: Optional[bool] = True):
    """
    Deletes the configuration related to the postprocessor <logger_name>
    """
    config_dict = extract_config()
    logger_section = next((
        key for key, value in config_dict.items()
        if key.startswith("SourceLogger_") and value["Name"] == logger_name
    ), None)
    if not logger_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The logger: {logger_name} does not exist")

    config_dict.pop(logger_section)
    success = update_config(config_dict, reboot_processor)
    return handle_response(None, success, status.HTTP_204_NO_CONTENT)
