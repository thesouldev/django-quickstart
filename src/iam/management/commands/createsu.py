from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser"

    def handle(self, *args, **options):
        User = get_user_model()
        username = settings.DJANGO_SUPERUSER_USERNAME
        email = settings.DJANGO_SUPERUSER_EMAIL
        password = settings.DJANGO_SUPERUSER_PASSWORD

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                is_active=True,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created superuser {username}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Superuser {username} already exists")
            )
