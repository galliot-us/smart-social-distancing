import logging

from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Optional


from api.utils import handle_response, update_config
from libs.notifications.slack_notifications import is_slack_configured

logger = logging.getLogger(__name__)

slack_router = APIRouter()


class SlackConfig(BaseModel):
    user_token: str
    channel: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "user_token": "xxxx-ffff..."
            }
        }


class SlackIsEnabled(BaseModel):
    enabled: bool


def add_slack_channel_to_config(channel, reboot_processor):
    logger.info("Adding slack's channel on processor's config")
    config_dict = dict()
    config_dict["App"] = dict({"SlackChannel": channel})

    success = update_config(config_dict, reboot_processor)
    return handle_response(config_dict, success)


def write_user_token(token):
    logger.info("Writing user access token")
    with open("slack_token.txt", "w+") as slack_token:
        slack_token.write(token)


def enable_slack(token_config, reboot_processor):
    write_user_token(token_config.user_token)
    logger.info("Enabling slack notification on processor's config")
    config_dict = dict()
    config_dict["App"] = dict({"SlackChannel": token_config.channel})
    success = update_config(config_dict, reboot_processor)

    return handle_response(config_dict, success)


@slack_router.get("/is-enabled", response_model=SlackIsEnabled)
def is_slack_enabled():
    """
    Returns if slack is already enabled in the processor
    """
    return {
        "enabled": is_slack_configured()
    }


@slack_router.delete("/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_slack():
    """
    Remove the current slack configuration in the processor
    """
    write_user_token("")


@slack_router.post("/add-channel", status_code=status.HTTP_204_NO_CONTENT)
def add_slack_channel(channel: str, reboot_processor: Optional[bool] = True):
    """
    Changes the slack's channel used by the processor to send notifications
    """
    add_slack_channel_to_config(channel, reboot_processor)


@slack_router.post("/enable", status_code=status.HTTP_204_NO_CONTENT)
def enable(body: SlackConfig, reboot_processor: Optional[bool] = True):
    """
    Changes the slack workspace configured in the processor
    """
    enable_slack(body, reboot_processor)
