import secrets
import string

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import serializers

from .models import UserApiKey
from .permissions import ASSIGNABLE_ROLES, set_user_role

User = get_user_model()


def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdigit() for char in password)
        ):
            return password


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)
    has_avatar = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "mobile_phone",
            "auth_type",
            "role",
            "is_active",
            "notify_on_playbook_completion",
            "notify_on_case_assignment",
            "has_avatar",
            "avatar_url",
            "date_joined",
            "last_login",
        )
        read_only_fields = (
            "id",
            "username",
            "auth_type",
            "role",
            "has_avatar",
            "avatar_url",
            "date_joined",
            "last_login",
        )

    def get_has_avatar(self, obj):
        return bool(obj.avatar_attachment_id)

    def get_avatar_url(self, obj):
        if not obj.avatar_attachment:
            return ""
        return reverse("attachment-download", kwargs={"access_key": obj.avatar_attachment.access_key})


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "mobile_phone",
            "notify_on_playbook_completion",
            "notify_on_case_assignment",
        )


class UserCreateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=ASSIGNABLE_ROLES)
    generated_password = None

    class Meta:
        model = User
        fields = (
            "username",
            "auth_type",
            "role",
            "email",
            "first_name",
            "last_name",
            "mobile_phone",
        )

    def create(self, validated_data):
        role = validated_data.pop("role")
        auth_type = validated_data.get("auth_type", User.AuthType.LOCAL)
        user = User(**validated_data)
        if auth_type == User.AuthType.LOCAL:
            self.generated_password = generate_password()
            user.set_password(self.generated_password)
        else:
            user.set_unusable_password()
        user.save()
        set_user_role(user, role)
        return user


class UserAdminUpdateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=ASSIGNABLE_ROLES, required=False)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "mobile_phone",
            "role",
            "is_active",
        )

    def update(self, instance, validated_data):
        role = validated_data.pop("role", None)
        instance = super().update(instance, validated_data)
        if role:
            set_user_role(instance, role)
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    auth_type = serializers.ChoiceField(choices=User.AuthType.choices)


class UserApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserApiKey
        fields = (
            "id",
            "name",
            "key",
            "expires_at",
            "last_used_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "key", "last_used_at", "created_at", "updated_at")
