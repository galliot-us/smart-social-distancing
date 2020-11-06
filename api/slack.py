import logging
import os

from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Optional


from .utils import handle_response, update_and_restart_config

logger = logging.getLogger(__name__)

slack_router = APIRouter()


class SlackConfig(BaseModel):
    user_token: str
    channel: Optional[str]

    class Config:
        schema_extra = {
            'example': {
                'user_token': 'xxxx-ffff...'
            }
        }


class SlackIsEnabled(BaseModel):
    enabled: bool


def add_slack_channel_to_config(channel):
    logger.info("Adding slack's channel on processor's config")
    config_dict = dict()
    config_dict["App"] = dict({"SlackChannel": channel})

    success = update_and_restart_config(config_dict)
    return handle_response(config_dict, success)


def is_slack_configured():
    if not os.path.exists('slack_token.txt'):
        return False
    with open("slack_token.txt", "r") as user_token:
        value = user_token.read()
        return bool(value)


def write_user_token(token):
    logger.info("Writing user access token")
    with open("slack_token.txt", "w+") as slack_token:
        slack_token.write(token)


def enable_slack(token_config):
    write_user_token(token_config.user_token)
    logger.info("Enabling slack notification on processor's config")
    config_dict = dict()
    config_dict["App"] = dict({"EnableSlackNotifications": "yes", "SlackChannel": token_config.channel})
    success = update_and_restart_config(config_dict)

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
def add_slack_channel(channel: str):
    """
    Changes the slack's channel used by the processor to send notifications
    """
    add_slack_channel_to_config(channel)


@slack_router.post("/enable", status_code=status.HTTP_204_NO_CONTENT)
def enable(body: SlackConfig):
    """
    Changes the slack workspace configured in the processor
    """
    enable_slack(body)
