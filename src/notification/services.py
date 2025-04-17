# notifications/services.py

import logging
from urllib.parse import urlencode

from django.conf import settings
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, api_key=settings.SENDGRID_API_KEY):
        self.client = SendGridAPIClient(api_key)

    def send_email(self, to_email: str, subject: str, content: str):
        message = Mail(
            from_email=settings.SENDGRID_SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=content,
        )
        response = self.client.send(message)
        return response

    def send_activation_mail(self, to_email: str, token: str):
        subject = "Activate your account"
        params = {
            "action": "activate",
            "token": token,
        }
        url = f"{settings.FRONTEND_APP_URL}/login?{urlencode(params)}"

        content = render_to_string(
            "emails/activation_email.html", {"activation_url": url}
        )
        logger.debug(params)
        return self.send_email(to_email, subject, content)

    def send_reset_mail(self, to_email: str, uidb64: str, token: str):
        subject = "Reset your password"
        params = {
            "action": "reset",
            "uidb64": uidb64,
            "token": token,
        }
        url = f"{settings.FRONTEND_APP_URL}/login?{urlencode(params)}"
        content = render_to_string(
            "emails/reset_password_email.html", {"reset_url": url}
        )
        logger.debug(params)
        return self.send_email(to_email, subject, content)
