from fastapi import APIRouter
from pydantic import ValidationError
from starlette import status
from starlette.exceptions import HTTPException
from typing import Optional

from api.models.source_post_processor import (
    SourcePostProcessorDTO, SourcePostProcessorListDTO, ObjectFilteringDTO, SocialDistanceDTO, AnonymizerDTO)
from api.utils import (
    extract_config, handle_response, update_config, map_section_from_config, map_to_config_file_format)

source_post_processors_router = APIRouter()


def get_source_post_processors():
    config = extract_config(config_type="source_post_processors")
    return [map_section_from_config(x, config) for x in config.keys()]


def get_source_post_processors_model(post_processor):
    if post_processor.name == "objects_filtering":
        return ObjectFilteringDTO
    elif post_processor.name == "social_distance":
        return SocialDistanceDTO
    elif post_processor.name == "anonymizer":
        return AnonymizerDTO
    else:
        raise ValueError(f"Not supported post processor named: {post_processor.name}")


@source_post_processors_router.get("", response_model=SourcePostProcessorListDTO,
                                   response_model_exclude_none=True)
def list_source_post_processors():
    """
        Returns the list of post processors configured in the processor.
    """
    return {
        "sourcesPostProcessors": get_source_post_processors()
    }


@source_post_processors_router.get("/{post_processor_name}", response_model=SourcePostProcessorDTO,
                                   response_model_exclude_none=True)
def get_source_post_processorss(post_processor_name: str):
    """
    Returns the configuration related to the post processor <post_processor_name>.
    """
    post_processor = next((ps for ps in get_source_post_processors() if ps["name"] == post_processor_name), None)
    if not post_processor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The post_processor: {post_processor_name} does not exist")
    return post_processor


@source_post_processors_router.post("", response_model=SourcePostProcessorDTO,
                                    status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
async def create_post_processor(new_post_processor: SourcePostProcessorDTO, reboot_processor: Optional[bool] = True):
    """
    Adds a post processor.
    """
    config_dict = extract_config()
    post_processors_index = [int(x[-1]) for x in config_dict.keys() if x.startswith("SourcePostProcessor_")]
    post_processors = get_source_post_processors()
    post_processor_model = get_source_post_processors_model(new_post_processor)
    # Validate that the specific post processor's fields are correctly set
    try:
        post_processor_model(**new_post_processor.dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if new_post_processor.name in [ps["name"] for ps in post_processors]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PostProcessor already exists")
    post_processor_file = map_to_config_file_format(new_post_processor, True)
    index = 0
    if post_processors_index:
        index = max(post_processors_index) + 1
    config_dict[f"SourcePostProcessor_{index}"] = post_processor_file
    success = update_config(config_dict, reboot_processor)
    return handle_response(post_processor_file, success, status.HTTP_201_CREATED)


@source_post_processors_router.put("/{post_processor_name}", response_model=SourcePostProcessorDTO)
async def edit_post_processor(post_processor_name: str, edited_post_processor: SourcePostProcessorDTO,
                              reboot_processor: Optional[bool] = True):
    """
    Edits the configuration related to the post processor <post_processor_name>
    """
    edited_post_processor.name = post_processor_name
    config_dict = extract_config()
    edited_post_processor_section = next((
        key for key, value in config_dict.items()
        if key.startswith("SourcePostProcessor_") and value["Name"] == post_processor_name
    ), None)
    if not edited_post_processor_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The post processor: {post_processor_name} does not exist")
    post_processor_model = get_source_post_processors_model(edited_post_processor)
    # Validate that the specific post processor's fields are correctly set
    try:
        post_processor_model(**edited_post_processor.dict())
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    post_processor_file = map_to_config_file_format(edited_post_processor, True)
    config_dict[edited_post_processor_section] = post_processor_file
    success = update_config(config_dict, reboot_processor)
    return handle_response(post_processor_file, success)


@source_post_processors_router.delete("/{post_processor_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post_processor(post_processor_name: str, reboot_processor: Optional[bool] = True):
    """
    Deletes the configuration related to the post processor <post_processor_name>
    """
    config_dict = extract_config()
    post_processor_section = next((
        key for key, value in config_dict.items()
        if key.startswith("SourcePostProcessor_") and value["Name"] == post_processor_name
    ), None)
    if not post_processor_section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The post processor: {post_processor_name} does not exist")

    config_dict.pop(post_processor_section)
    success = update_config(config_dict, reboot_processor)
    return handle_response(None, success, status.HTTP_204_NO_CONTENT)
