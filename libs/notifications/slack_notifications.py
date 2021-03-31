import logging
import os
from slack import WebClient

def is_slack_configured():
    if not os.path.exists("slack_token.txt"):
        return False
    with open("slack_token.txt", "r") as user_token:
        value = user_token.read()
        return bool(value)

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

    def violation_report(self, entity_info, number):
        entity_id, entity_type, entity_name = entity_info['id'], entity_info['type'], entity_info['name']
        msg = f"We found {number} violations in {entity_id}: {entity_name} ({entity_type})"
        self.post_message_to_channel(msg, self.channel)

    def daily_report(self, entity_info, number):
        entity_id, entity_type, entity_name = entity_info['id'], entity_info['type'], entity_info['name']
        msg = f"Yesterday we found {number} violations in {entity_id}: {entity_name} ({entity_type})."
        self.post_message_to_channel(msg, self.channel)

    def occupancy_alert(self, entity_info, number, threshold):
        entity_id, entity_type = entity_info['id'], entity_info['type']
        entity_name = entity_info['name']
        msg = f"Occupancy threshold was exceeded in {entity_type} {entity_id}: {entity_name}." \
              f"We found {number} people out of a capacity of {threshold}."
        self.post_message_to_channel(msg, self.channel)

    def send_global_report(self, report_type, sources, areas, sources_violations_per_hour, areas_violations_per_hour):
        msg = f"*{report_type.capitalize()} Report:* \n\n"
        msg += "*Areas:*\n"
        for index, area in enumerate(areas):
            entity_id, entity_name = area['id'], area['name']
            msg += f"*{entity_id}:* {entity_name} - {sum(areas_violations_per_hour[index])} Violations\n"
        msg += "\n*Cameras:*\n"
        for index, source in enumerate(sources):
            entity_id, entity_name = source['id'], source['name']
            msg += f"*{entity_id}:* {entity_name} - {sum(sources_violations_per_hour[index])} Violations\n"
        self.post_message_to_channel(msg, self.channel)
