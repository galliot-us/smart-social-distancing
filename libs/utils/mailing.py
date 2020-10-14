import yagmail
import logging
import codecs

# TODO: Move to a constants file
NOTIFICATION_EMAIL_FROM = "noreply@yourdomain.com"


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
        self.email_from = NOTIFICATION_EMAIL_FROM
        self.logger = logging.getLogger(__name__)

    def send_source_notification(self, source_info, subject, content):
        if "Emails" not in source_info or source_info["Emails"].strip() == "":
            self.logger.info("No notification was emailed because no email was added for selected source")
            return
        to = source_info["Emails"].split(',')
        send_email(self.email_from, to, subject, content)
        self.logger.info(f"Sent notification email to {to}")

    def send_violation_notification(self, source_name, num_violations):
        source_info = self.config.get_section_dict(source_name)
        frontend_url = self.config.get_section_dict("App")["DashboardURL"]
        with codecs.open('libs/utils/mail_violations_notification.html', 'r') as f:
            html_string = f.read()
        html_string = html_string.replace('{detections}', str(num_violations))
        html_string = html_string.replace('{camera}', source_info['Name'])
        # TODO: Fix this
        html_string = html_string.replace('{url}', f'{frontend_url}/dashboard?source=email')
        subject = f"[Lanthorn] Violation Report on camera {source_info['Name']}"
        self.send_source_notification(source_info, subject, html_string)

    def send_daily_report(self, source_name, num_violations, hours_sumary):
        source_info = self.config.get_section_dict(source_name)
        frontend_url = self.config.get_section_dict("App")["DashboardURL"]
        with codecs.open('libs/utils/mail_daily_report.html', 'r') as f:
            html_string = f.read()
        html_string = html_string.replace('{detections}', str(num_violations))
        violations_per_hour = ""
        for hour, hour_violation in enumerate(hours_sumary):
            violations_per_hour += f"<tr><td>{hour}:00</td><td>{hour_violation}</td></tr>"
        html_string = html_string.replace('{violations_per_hour}', violations_per_hour)
        html_string = html_string.replace('{camera}', source_info['Name'])
        html_string = html_string.replace('{url}', f'{frontend_url}/dashboard?source=email')
        subject = f"[Lanthorn] Daily Report on camera {source_info['Name']}"
        self.send_source_notification(source_info, subject, html_string)
