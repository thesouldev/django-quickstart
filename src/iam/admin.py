from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission

from .models import User, UserVerification


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("get_username",)

    def get_username(self, obj):
        return obj.username


admin.site.register(User, CustomUserAdmin)
admin.site.register(UserVerification)
admin.site.register(Permission)
