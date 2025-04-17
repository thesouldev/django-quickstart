from typing import List, Union

from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from iam import views

router = DefaultRouter()
router.register(r"auth/users", views.UserViewSet, basename="user")
router.register(
    r"auth", views.UserVerificationViewSet, basename="user-verification"
)

"""
JWT Authentication URL Endpoints
"""
urlpatterns: List[Union[URLResolver, URLPattern]] = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/logout/", views.BlacklistRefreshView.as_view(), name="logout"),
    path(
        "",
        include(router.urls),
    ),
]
