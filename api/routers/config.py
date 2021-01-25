import logging

from fastapi import APIRouter
from typing import Optional

from api.models.config import ConfigDTO, ConfigInfo, GlobalReportingEmailsInfo
from api.utils import (
    get_config, extract_config, handle_response, update_config, map_section_from_config, map_to_config_file_format
)
from constants import PROCESSOR_VERSION

from .cameras import map_camera, map_to_camera_file_format

logger = logging.getLogger(__name__)

config_router = APIRouter()


def map_to_file_format(config_dto: ConfigDTO):
    config_dict = dict()
    config_dict["App"] = map_to_config_file_format(config_dto.app)
    config_dict["CORE"] = map_to_config_file_format(config_dto.core)
    for count, area in enumerate(config_dto.areas):
        config_dict["Area_" + str(count)] = map_to_config_file_format(area)
    for count, camera in enumerate(config_dto.cameras):
        config_dict["Source_" + str(count)] = map_to_camera_file_format(camera)
    config_dict["Detector"] = map_to_config_file_format(config_dto.detector)
    if config_dto.classifier:
        config_dict["Classifier"] = map_to_camera_file_format(config_dto.classifier)
    config_dict["Tracker"] = map_to_config_file_format(config_dto.tracker)
    for count, source_post_processor in enumerate(config_dto.sourcePostProcessors):
        config_dict["SourcePostProcessor_" + str(count)] = map_to_config_file_format(
            source_post_processor, True)
    for count, source_logger in enumerate(config_dto.sourceLoggers):
        config_dict["SourceLogger_" + str(count)] = map_to_config_file_format(source_logger, True)
    for count, area_logger in enumerate(config_dto.areaLoggers):
        config_dict["AreaLogger_" + str(count)] = map_to_config_file_format(area_logger, True)
    for count, periodic_task in enumerate(config_dto.periodicTasks):
        config_dict["PeriodicTask_" + str(count)] = map_to_config_file_format(periodic_task, True)
    return config_dict


def map_config(config, options):
    cameras_name = [x for x in config.keys() if x.startswith("Source_")]
    areas_name = [x for x in config.keys() if x.startswith("Area_")]
    source_post_processor = [x for x in config.keys() if x.startswith("SourcePostProcessor_")]
    source_loggers = [x for x in config.keys() if x.startswith("SourceLogger_")]
    area_loggers = [x for x in config.keys() if x.startswith("AreaLogger_")]
    periodic_tasks = [x for x in config.keys() if x.startswith("PeriodicTask_")]
    return {
        "app": map_section_from_config("App", config),
        "api": map_section_from_config("API", config),
        "core": map_section_from_config("CORE", config),
        "cameras": [map_camera(x, config, options) for x in cameras_name],
        "areas": [map_section_from_config(x, config) for x in areas_name],
        "detector": map_section_from_config("Detector", config),
        "classifier": map_section_from_config("Classifier", config),
        "tracker": map_section_from_config("Tracker", config),
        "sourcePostProcessors": [map_section_from_config(x, config) for x in source_post_processor],
        "sourceLoggers": [map_section_from_config(x, config) for x in source_loggers],
        "areaLoggers": [map_section_from_config(x, config) for x in area_loggers],
        "periodicTasks": [map_section_from_config(x, config) for x in periodic_tasks],
    }


def processor_info(config):
    has_been_configured = config.get_boolean("App", "HasBeenConfigured")
    device = config.get_section_dict("Detector")["Device"]
    if config.get_section_dict("Detector")["Name"] == "openvino":
        device += "-openvino"
    return {
        "version": PROCESSOR_VERSION,
        "device": device,
        "has_been_configured": has_been_configured
    }


@config_router.get("", response_model=ConfigDTO, response_model_exclude_none=True)
async def get_config_file(options: Optional[str] = ""):
    """
    Returns the configuration used by the processor
    """
    logger.info("get-config requests on api")
    return map_config(extract_config(), options)


@config_router.put("", response_model=ConfigDTO)
async def update_config_file(config: ConfigDTO, reboot_processor: Optional[bool] = True):
    """
    Overwrites the configuration used by the processor.
    """
    config_dict = map_to_file_format(config)
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(config_dict, success)
    return map_config(extract_config(), "")


@config_router.get("/info", response_model=ConfigInfo)
async def get_processor_info():
    """
    Returns basic info regarding this processor
    """
    return processor_info(get_config())


@config_router.get("/global_report", response_model=GlobalReportingEmailsInfo)
async def get_report_info():
    app_config = extract_config()["App"]
    return {
        "emails": app_config["GlobalReportingEmails"],
        "time": app_config["GlobalReportTime"],
        "daily": get_config().get_boolean("App", "DailyGlobalReport"),
        "weekly": get_config().get_boolean("App", "WeeklyGlobalReport")
    }


@config_router.put("/global_report")
async def update_report_info(global_report_info: GlobalReportingEmailsInfo, reboot_processor: Optional[bool] = True):
    global_report_info = global_report_info.dict(exclude_unset=True, exclude_none=True)
    config_dict = extract_config()
    key_mapping = {"GlobalReportingEmails": "emails", "GlobalReportTime": "time",
                   "DailyGlobalReport": "daily", "WeeklyGlobalReport": "weekly"}
    for key, value in key_mapping.items():
        if value in global_report_info:
            config_dict["App"][key] = str(global_report_info[value])
    success = update_config(config_dict, reboot_processor)
    return handle_response(config_dict, success)
