import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone

from core.mixins import TimestampMixin, UUIDMixin


class User(AbstractUser, UUIDMixin):
    is_active = models.BooleanField(
        default=False, help_text="User is active", null=False
    )
    groups = models.ManyToManyField(
        Group, related_name="customuser_set", blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission, related_name="customuser_set", blank=True
    )

    def __str__(self) -> str:
        return self.email


class UserVerification(TimestampMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    token = models.CharField(max_length=64, null=True)
    verified_at = models.DateTimeField(null=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self) -> bool:
        expiry = self.modified_at + datetime.timedelta(
            hours=settings.USERTOKEN_EXPIRY_HOURS
        )
        return timezone.now() > expiry  # pyre-ignore[58]

    def __str__(self) -> str:
        return self.user.email
