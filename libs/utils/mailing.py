import os
import yagmail
import logging
import codecs
from dotenv import load_dotenv
load_dotenv()

def send_email(from_email, receiver, subject, contents, attachments=None):
    with yagmail.SMTP(from_email, oauth2_file="oauth2_cred.json") as yag:
        yag.send(
            to=receiver,
            subject=subject,
            contents=contents,
            attachments=attachments,
            newline_to_break=False
        )


class MailService:

    def __init__(self, config):
        self.config = config
        self.email_from = os.getenv("NOTIFICATION_EMAIL_FROM")
        self.logger = logging.getLogger(__name__)

    def send_email_notification(self, entity_info, subject, content):
        if "emails" not in entity_info or not entity_info["emails"]:
            self.logger.info("No notification was emailed because no email was added for selected source")
            return
        to = entity_info["emails"]
        send_email(self.email_from, to, subject, content)
        self.logger.info(f"Sent notification email to {to}")

    def send_violation_notification(self, entity_info, num_violations):
        entity_type = entity_info['type']
        frontend_url = self.config.get_section_dict("App")["DashboardURL"]
        with codecs.open('libs/utils/mail_violations_notification.html', 'r') as f:
            html_string = f.read()
        html_string = html_string.replace('{detections}', str(num_violations))
        html_string = html_string.replace('{entity_type}', entity_type)
        html_string = html_string.replace('{entity_name}', entity_info['name'])
        # TODO: Fix this
        html_string = html_string.replace('{url}', f'{frontend_url}/dashboard?source=email')
        subject = f"[Lanthorn] Violation Report on {entity_info['name']} ({entity_type})"
        self.send_email_notification(entity_info, subject, html_string)

    def send_daily_report(self, entity_info, num_violations, hours_sumary):
        entity_type = entity_info['type']
        frontend_url = self.config.get_section_dict("App")["DashboardURL"]
        with codecs.open('libs/utils/mail_daily_report.html', 'r') as f:
            html_string = f.read()
        html_string = html_string.replace('{detections}', str(num_violations))
        violations_per_hour = ""
        for hour, hour_violation in enumerate(hours_sumary):
            violations_per_hour += f"<tr><td>{hour}:00</td><td>{hour_violation}</td></tr>"
        html_string = html_string.replace('{violations_per_hour}', violations_per_hour)
        html_string = html_string.replace('{entity_type}', entity_type)
        html_string = html_string.replace('{entity_name}', entity_info['name'])
        html_string = html_string.replace('{url}', f'{frontend_url}/dashboard?source=email')
        subject = f"[Lanthorn] Daily Report on {entity_type}: {entity_info['name']}"
        self.send_email_notification(entity_info, subject, html_string)

    def send_occupancy_notification(self, entity_info, num_occupancy):
        entity_id, entity_type = entity_info['id'], entity_info['type']
        entity_name, entity_threshold = entity_info['name'], entity_info['occupancy_threshold']
        frontend_url = self.config.get_section_dict("App")["DashboardURL"]
        with codecs.open('libs/utils/mail_occupancy_notification.html', 'r') as f:
            html_string = f.read()
        html_string = html_string.replace('{num_occupancy}', str(num_occupancy))
        html_string = html_string.replace('{entity_id}', entity_id)
        html_string = html_string.replace('{entity_type}', entity_type)
        html_string = html_string.replace('{entity_name}', entity_name)
        html_string = html_string.replace('{entity_threshold}', str(entity_threshold))
        html_string = html_string.replace('{url}', f'{frontend_url}/dashboard?source=email')
        subject = f"[Lanthorn] Occupancy Alert on {entity_name} ({entity_type})"
        self.send_email_notification(entity_info, subject, html_string)
