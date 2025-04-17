from django.db.models.signals import post_save
from django.dispatch import receiver

from iam.models import UserVerification
from notification.services import EmailService


@receiver(
    post_save, sender=UserVerification, dispatch_uid="send_verification_mail"
)
def send_verification_email(sender, instance, **kwargs):
    if instance.is_verified:
        return
    user, token = instance.user, instance.token
    email_service = EmailService()
    email_service.send_activation_mail(user.email, token)
