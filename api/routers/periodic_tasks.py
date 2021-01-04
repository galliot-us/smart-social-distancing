from fastapi import APIRouter, status
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from typing import Optional

from api.models.periodic_task import PeriodicTaskDTO, PeriodicTaskListDTO, validate_periodic_task
from api.utils import (
    extract_config, handle_response, update_config,
    map_section_from_config, map_to_config_file_format, bad_request_serializer
)
import logging
logger = logging.getLogger(__name__)

periodic_tasks_router = APIRouter()


def get_periodic_tasks():
    config = extract_config(config_type="periodic_tasks")
    return [map_section_from_config(x, config) for x in config.keys()]


@periodic_tasks_router.get("", response_model=PeriodicTaskListDTO,
                           response_model_exclude_none=True)
def list_periodic_tasks():
    """
        Returns the list of periodic tasks configured in the processor.
    """
    return {
        "periodicTasks": get_periodic_tasks()
    }


@periodic_tasks_router.get("/{periodic_task_name}", response_model=PeriodicTaskDTO,
                           response_model_exclude_none=True)
def get_periodic_task(periodic_task_name: str):
    """
    Returns the configuration related to the periodic task <periodic_task_name>.
    """
    periodic_task = next((ps for ps in get_periodic_tasks() if ps["name"] == periodic_task_name), None)
    if not periodic_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The periodic_task: {periodic_task_name} does not exist")
    return periodic_task


@periodic_tasks_router.post("", response_model=PeriodicTaskDTO,
                            status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
async def create_periodic_task(new_periodic_task: PeriodicTaskDTO, reboot_processor: Optional[bool] = True):
    """
    Adds a periodic task.
    """
    config_dict = extract_config()
    periodic_tasks_index = [int(x[-1]) for x in config_dict.keys() if x.startswith("PeriodicTask_")]
    periodic_tasks = get_periodic_tasks()
    try:
        validate_periodic_task(new_periodic_task)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bad_request_serializer(str(e))
        )
    if new_periodic_task.name in [ps["name"] for ps in periodic_tasks]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bad_request_serializer("Periodic task already exists", error_type="config duplicated periodic_task")
        )
    periodic_task_file = map_to_config_file_format(new_periodic_task, True)
    index = 0
    if periodic_tasks_index:
        index = max(periodic_tasks_index) + 1
    config_dict[f"PeriodicTask_{index}"] = periodic_task_file
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(periodic_task_file, success, status.HTTP_201_CREATED)
    return next((ps for ps in get_periodic_tasks() if ps["name"] == periodic_task_file["Name"]), None)


@periodic_tasks_router.put("/{periodic_task_name}", response_model=PeriodicTaskDTO,
                           response_model_exclude_none=True)
async def edit_periodic_task(periodic_task_name: str, edited_periodic_task: PeriodicTaskDTO,
                             reboot_processor: Optional[bool] = True):
    """
    Edits the configuration related to the periodic task <periodic_task_name>.
    """
    edited_periodic_task.name = periodic_task_name
    config_dict = extract_config()
    edited_periodic_task_section = next((
        key for key, value in config_dict.items()
        if key.startswith("PeriodicTask_") and value["Name"] == periodic_task_name
    ), None)
    if not edited_periodic_task_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The periodic_task: {periodic_task_name} does not exist")
    try:
        validate_periodic_task(edited_periodic_task)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bad_request_serializer(str(e))
        )
    periodic_task_file = map_to_config_file_format(edited_periodic_task, True)
    config_dict[edited_periodic_task_section] = periodic_task_file
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(periodic_task_file, success)
    return next((ps for ps in get_periodic_tasks() if ps["name"] == periodic_task_name), None)


@periodic_tasks_router.delete("/{periodic_task_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_periodic_task(periodic_task_name: str, reboot_processor: Optional[bool] = True):
    """
    Deletes the configuration related to the periodic task <periodic_task_name>.
    """
    config_dict = extract_config()
    periodic_task_section = next((
        key for key, value in config_dict.items()
        if key.startswith("PeriodicTask_") and value["Name"] == periodic_task_name
    ), None)
    if not periodic_task_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The periodic task: {periodic_task_name} does not exist")
    config_dict.pop(periodic_task_section)
    success = update_config(config_dict, reboot_processor)
    return handle_response(None, success, status.HTTP_204_NO_CONTENT)
