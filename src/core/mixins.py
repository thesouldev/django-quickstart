import uuid

from django.db import models


class TimestampMixin(models.Model):

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The current datetime when the object is initially created",
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        help_text="The current datetime whenever the object is saved",
    )

    class Meta:
        abstract = True


class UUIDMixin(models.Model):

    uuid = models.UUIDField(
        editable=False, primary_key=True, default=uuid.uuid4
    )

    class Meta:
        abstract = True
