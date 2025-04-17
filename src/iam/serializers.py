import django.contrib.auth.password_validation as validators
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from iam.models import User, UserVerification


class RefreshTokenSerializer(serializers.Serializer):
    """
    Handles blacklisting the refresh token during logout.

    Validation:
    - Ensures the refresh token is provided and valid.

    Notes:
    - Used to invalidate the token and prevent further use after logout.
    """

    refresh = serializers.CharField(
        required=True, allow_blank=False, label="Refresh token"
    )

    def validate_refresh(self, value):
        if not value:
            raise serializers.ValidationError(
                "Refresh token is required", code="authorization"
            )
        return value


class UserSerializer(serializers.ModelSerializer):
    """
    Manages user account creation and updates, including email, password,
    first name, and last name.

    Validation:
    - Ensures that the email is unique and the password conforms to
    validation rules.

    Notes:
    - The user's username is set to the provided email, and the account
    is inactive until email verification.
    """

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
        allow_blank=False,
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        allow_blank=False,
        validators=[validators.validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = (
            "last_login",
            "is_superuser",
            "username",
            "is_staff",
            "is_active",
            "date_joined",
            "groups",
            "user_permissions",
        )

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.username = user.email
        user.save()

        return user


class UserVerificationSerializer(serializers.ModelSerializer):
    """
    Verifies user tokens and checks whether they have expired.

    Validation:
    - Ensures that the token is valid and has not expired.
    """

    class Meta:
        model = UserVerification
        fields = "__all__"

    def validate(self, attrs):
        user = attrs.get("user")
        token = attrs.get("token")
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError("Invalid token")
        if self.instance and self.instance.is_expired():
            raise serializers.ValidationError("Token has expired")

        return attrs


class GenericRequestSerializer(serializers.Serializer):
    """
    Validates user requests based on email and verification status.

    Validation:
    - Ensures that the user exists and the verification record matches the
    expected status.

    """

    username = serializers.EmailField(required=True, allow_blank=False)
    should_be_verified = False

    def validate(self, attrs):
        username = attrs.get("username")

        try:
            user = get_object_or_404(
                User, username=username, is_active=self.should_be_verified
            )
            user_verification_record = get_object_or_404(
                UserVerification,
                user=user,
                is_verified=self.should_be_verified,
            )
        except (User.DoesNotExist, UserVerification.DoesNotExist):
            raise serializers.ValidationError(
                {"username": "No valid user found"}
            )

        attrs["user"] = user
        attrs["user_verification_record"] = user_verification_record
        return attrs


class AccountActivationSerializer(serializers.Serializer):
    """
    Validates user activation based on the provided token.

    Validation:
    - Ensures that the token is valid, not already used, and has not expired.
    """

    token = serializers.CharField(required=True, allow_blank=False)

    def validate(self, attrs):
        token = attrs.get("token")

        try:
            user_verification_record = UserVerification.objects.get(
                token=token
            )
        except UserVerification.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid token"})

        if user_verification_record.is_expired():
            raise serializers.ValidationError({"token": "Token has expired"})

        if not default_token_generator.check_token(
            user_verification_record.user, user_verification_record.token
        ):
            raise serializers.ValidationError({"token": "Invalid token"})
        attrs["user_verification_record"] = user_verification_record

        return attrs


class RequestAccountActivationSerializer(GenericRequestSerializer):
    """
    Validates user activation requests based on email and verification status.

    Validation:
    - Ensures that the user exists, is not already activated,
    and the token is valid and has not expired.
    """

    should_be_verified = False


class RequestPasswordResetSerializer(GenericRequestSerializer):
    """
    Validates user password reset requests based on email
    and verification status.

    Validation:
    - Ensures that the user exists, is already activated,
    and the token is valid and has not expired.
    """

    should_be_verified = True


class ResetPasswordSerializer(serializers.Serializer):
    """
    Validates user password reset action based on the provided token.

    Validation:
    - Ensures that the password is valid, the uidb64 matches an active user,
      and the token is valid and has not expired.

    Notes:
    - The password is validated using Django's password validators.
    - A user who is not active yet cannot reset their password.
    """

    password = serializers.CharField(
        required=True,
        allow_blank=False,
        validators=[validators.validate_password],
        style={"input_type": "password"},
    )
    uidb64 = serializers.CharField(required=True, allow_blank=False)
    token = serializers.CharField(required=True, allow_blank=False)

    def validate(self, attrs):
        token = attrs.get("token")
        uidb64 = attrs.get("uidb64")

        invalid_dict = {
            key: "Invalid token or UID" for key in ["token", "uidb64"]
        }

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(uuid=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        user_verification_record = get_object_or_404(
            UserVerification, user=user, token=token, is_verified=True
        )

        if user_verification_record.is_expired():
            raise serializers.ValidationError({"token": "Token has expired"})

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError(invalid_dict)

        attrs["user_verification_record"] = user_verification_record
        attrs["user"] = user
        return attrs
