import json
import os
import re

from fastapi import APIRouter, status
from starlette.exceptions import HTTPException

from api.models.area import AreaConfigDTO
from api.utils import get_config
from constants import ALL_AREAS
from libs.utils import config as config_utils
from libs.entities.area import Area

area_all_router = APIRouter()


@area_all_router.get("", response_model=AreaConfigDTO)
async def get_area_all():
    """
    Returns the Area "ALL", an area that contains all cameras.
    """
    config = get_config()
    area_all = config.get_area_all()

    if area_all is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The area: 'ALL' does not exist")

    return {
        "violation_threshold": area_all.violation_threshold,
        "notify_every_minutes": area_all.notify_every_minutes,
        "emails": ",".join(area_all.emails),
        "enable_slack_notifications": area_all.enable_slack_notifications,
        "daily_report": area_all.daily_report,
        "daily_report_time": area_all.daily_report_time,
        "occupancy_threshold": area_all.occupancy_threshold,
        "id": area_all.id,
        "name": area_all.name,
        "cameras": ",".join(area_all.cameras)
    }


@area_all_router.put("", response_model=AreaConfigDTO)
async def modify_area_all(area_information: AreaConfigDTO):
    """
    Edits the configuration related to the area "ALL", an area that contains all cameras.
    """
    config = get_config()
    config_directory = config_utils.get_area_config_directory(config)
    config_path = os.path.join(config_directory, ALL_AREAS + ".json")

    json_content = {
        "global_area_all": {
            "ViolationThreshold": area_information.violationThreshold,
            "NotifyEveryMinutes": area_information.notifyEveryMinutes,
            "Emails": area_information.emails,
            "EnableSlackNotifications": str(area_information.enableSlackNotifications),
            "DailyReport": str(area_information.dailyReport),
            "DailyReportTime": area_information.dailyReportTime,
            "OccupancyThreshold": area_information.occupancyThreshold,
            "Id": ALL_AREAS,
            "Name": ALL_AREAS,
        }
    }

    if not os.path.exists(config_path):
        # Create the file with if necessary
        with open(config_path, 'x') as outfile:
            json.dump(json_content, outfile)
    else:
        # If file exists, we have to modify the content in: "global_area_all".
        with open(config_path, "r") as file:
            file_content = json.load(file)

        file_content["global_area_all"] = json_content["global_area_all"]

        with open(config_path, "w") as file:
            json.dump(file_content, file)

    area_all = config.get_area_all()
    json_content["global_area_all"]["Cameras"] = ",".join(area_all.cameras)

    return {re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower(): value for key, value in json_content["global_area_all"].items()}
