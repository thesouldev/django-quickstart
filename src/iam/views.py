from typing import Type

from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import decorators, permissions, status, viewsets
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from iam import models
from iam.models import UserVerification
from iam.serializers import (
    AccountActivationSerializer,
    RefreshTokenSerializer,
    RequestAccountActivationSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    UserVerificationSerializer,
)
from notification.services import EmailService


class BlacklistRefreshView(GenericAPIView):
    """
    View for blacklisting the refresh token (logout).

    This view invalidates the provided refresh token, preventing
    future access token generation.

    POST:
    'refresh': (str) - The refresh token to be blacklisted.

    Returns:
        - 200 - Refresh token successfully blacklisted.
        - 400 - Invalid or missing refresh token.
    """

    serializer_class = RefreshTokenSerializer

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh = RefreshToken(serializer.validated_data["refresh"])
            refresh.blacklist()  # pyre-ignore[16]
        except (InvalidToken, TokenError):
            return Response(
                {"message": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"message": "Refresh token successfully blacklisted."},
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    Manage users (create, retrieve, update).

    Permissions:
    - Admin only (IsAdminUser)
    """

    serializer_class = UserSerializer
    queryset = models.User.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def create(self, request: Request, *args, **kwargs) -> Response:
        return super().create(request, *args, **kwargs)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return super().retrieve(request, *args, **kwargs)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        return super().partial_update(request, *args, **kwargs)

    def update(self, request: Request, *args, **kwargs) -> Response:
        return super().update(request, *args, **kwargs)

    @decorators.action(
        methods=["post"],
        detail=False,
        url_path="register",
        url_name="register",
        permission_classes=[permissions.AllowAny],
    )
    def register(self, request: Request) -> Response:
        """
        Register a new user account.

        HTTP Method: POST

        Request Body:
        - email (str): Required, unique.
        - password (str): Required, validated.
        - first_name (str): Optional.
        - last_name (str): Optional.

        Permissions:
        - Public (AllowAny)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)

        # generate the user activation token
        token = default_token_generator.make_token(user)
        UserVerification.objects.create(user=user, token=token)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class UserVerificationViewSet(viewsets.ModelViewSet):
    queryset = UserVerification.objects.all()
    serializer_class = UserVerificationSerializer
    permission_classes = [permissions.IsAdminUser]

    serializers_per_action = {
        "initiate_account_activation": RequestAccountActivationSerializer,
        "verify_account": AccountActivationSerializer,
        "initiate_account_reset": RequestPasswordResetSerializer,
        "reset_account_password": ResetPasswordSerializer,
    }

    action: str = ""

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action in self.serializers_per_action:
            return self.serializers_per_action[self.action]
        return super().get_serializer_class()

    @decorators.action(
        detail=False,
        methods=["post"],
        url_path="request-account-activation",
        url_name="request-account-activation",
        permission_classes=[permissions.AllowAny],
    )
    def initiate_account_activation(self, request: Request) -> Response:
        """
        Request account activation.

        HTTP Method: POST

        Request Body:
        - email (str): Required.

        Permissions:
        - Public (AllowAny)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        user_verification_record = serializer.validated_data[
            "user_verification_record"
        ]

        activation_token = default_token_generator.make_token(user)
        try:
            user_verification_record.token = activation_token
            user_verification_record.save()
        except Exception as e:
            print(e)
            return Response(
                {"error": "Error sending account activation email"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Account activation email sent"},
            status=status.HTTP_200_OK,
        )

    @decorators.action(
        detail=False,
        methods=["post"],
        url_path="account-verify",
        url_name="account-verify",
        permission_classes=[permissions.AllowAny],
    )
    def verify_account(self, request: Request) -> Response:
        """
        Verify the account using the token.

        HTTP Method: POST

        Request Body:
        - token (str): Required, activation token.

        Permissions:
        - Public (AllowAny)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_verification_record = serializer.validated_data[
            "user_verification_record"
        ]
        if user_verification_record.is_verified:
            return Response(
                {"message": "Account already verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_verification_record.is_verified = True
        user_verification_record.verified_at = timezone.now()
        user_verification_record.save()

        user = user_verification_record.user
        user.is_active = True
        user.save()
        return Response(
            {"message": "Account verified successfully"},
            status=status.HTTP_200_OK,
        )

    @decorators.action(
        detail=False,
        methods=["post"],
        url_path="request-account-reset",
        url_name="request-account-reset",
        permission_classes=[permissions.AllowAny],
    )
    def initiate_account_reset(self, request: Request) -> Response:
        """
        Request password reset.

        HTTP Method: POST

        Request Body:
        - username (str): Required, user's email.

        Permissions:
        - Public (AllowAny)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        user_verification_record = serializer.validated_data[
            "user_verification_record"
        ]

        reset_password_token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.uuid))

        email_service = EmailService()
        try:
            email_service.send_reset_mail(
                user.email, uidb64, reset_password_token
            )
            user_verification_record.token = reset_password_token
            user_verification_record.save()
        except Exception:
            return Response(
                {"error": "Error sending password reset email"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Password reset email sent"}, status=status.HTTP_200_OK
        )

    @decorators.action(
        detail=False,
        methods=["post"],
        url_path="account-reset",
        url_name="account-reset",
        permission_classes=[permissions.AllowAny],
    )
    def reset_account_password(self, request: Request) -> Response:
        """
        Reset the user password.

        HTTP Method: POST

        Request Body:
        - password (str): Required, new password.
        - token (str): Required, reset token.
        - uidb64 (str): Required, base64 encoded user UUID.

        Permissions:
        - Public (AllowAny)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        password = serializer.validated_data["password"]
        user_verification_record = serializer.validated_data[
            "user_verification_record"
        ]

        user.set_password(password)
        user.save()
        user_verification_record.token = None
        user_verification_record.save()
        return Response(
            {"message": "Password has been reset successfully"},
            status=status.HTTP_200_OK,
        )
