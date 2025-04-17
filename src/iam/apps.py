from django.apps import AppConfig


class IAMConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "iam"
    verbose_name = "Identity and Access Management"

    def ready(self):
        import iam.signals  # noqa: F401
