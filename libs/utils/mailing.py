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

    def send_violation_notification(self, source_name, num_violations):
        source_info = self.config.get_section_dict(source_name)
        if "Emails" not in source_info or source_info["Emails"].strip() == "":
            self.logger.info("No notification sent because no email was added for selected source")
            return
        to = source_info["Emails"].split(',')
        cam_name = source_info["Name"]
        frontend_url = self.config.get_section_dict("App")["DashboardURL"]
        with codecs.open('libs/utils/mail_violations_notification.html', 'r') as f:
            html_string = f.read()
        html_string = html_string.replace('{detections}', str(num_violations))
        html_string = html_string.replace('{camera}', cam_name)
        # TODO: Fix this
        html_string = html_string.replace('{url}', f'{frontend_url}/dashboard?source=email')
        send_email(self.email_from, to, f"[Lanthorn] Violation Report on camera {cam_name}", html_string)
        self.logger.info(f"Sent notification email to {to}")
