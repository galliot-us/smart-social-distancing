import logging
import os

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional


from .utils import handle_config_response, update_and_restart_config

logger = logging.getLogger(__name__)

slack_api = FastAPI()


class SlackConfig(BaseModel):
    user_token: str
    channel: Optional[str]

    class Config:
        schema_extra = {
            'example': {
                'user_token': 'xxxx-ffff...'
            }
        }


def add_slack_channel_to_config(channel):
    logger.info("Adding slack's channel on processor's config")
    config_dict = dict()
    config_dict["App"] = dict({"SlackChannel": channel})

    success = update_and_restart_config(config_dict)
    return handle_config_response(config_dict, success)


def is_slack_configured():
    if not os.path.exists('slack_token.txt'):
        return False
    with open("slack_token.txt", "r") as user_token:
        value = user_token.read()
        if value:
            return True
        return False


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

    return handle_config_response(config_dict, success)


@slack_api.get("/is-enabled")
def is_slack_enabled():
    return {
        "enabled": is_slack_configured()
    }


@slack_api.delete("/revoke")
def revoke_slack():
    write_user_token("")


@slack_api.post("/add-channel")
def add_slack_channel(channel: str):
    add_slack_channel_to_config(channel)


@slack_api.post("/enable")
def enable(body: SlackConfig):
    enable_slack(body)
