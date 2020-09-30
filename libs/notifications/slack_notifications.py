import configparser
import os
import logging
from slack import WebClient


class SlackService:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        with open("slack_token.txt", "r") as slack_token:
            self.slack_token = slack_token.read()
        self.slack_client = WebClient(token=self.slack_token)
        self.channel = config.get_section_dict("App")["SlackChannel"]
        self.username = "lanthorn"
        self.icon_emoji = ":robot_face:"

    def post_message(self, msg, recipient):
        return self.slack_client.chat_postMessage(
            channel=recipient,
            text=msg
        )

    def post_message_to_channel(self, msg, channel):
        self.logger.info(f"Posting to {channel}")
        return self.slack_client.chat_postMessage(
            channel=channel,
            text=msg,
            username=self.username,
            parse='full'
        )

    def file_upload(self, file_content, file_name, file_type, title=None):
        return self.slack_client.files_upload(
            channels=self.channel,
            content=file_content,
            filename=file_name,
            filetype=file_type,
            initial_comment='{} Log File'.format(file_name),
            title=title
        )

    def user_info(self, uid):
        return self.slack_client.users_info(
            user=uid,
            token=self.slack_token
        )

    def violation_report(self, cam_id, cam_name, number):
        msg = f"We found {number} violations in {cam_id}: {cam_name} camera"
        self.post_message_to_channel(msg, self.channel)
