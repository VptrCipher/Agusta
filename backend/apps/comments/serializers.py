from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.attachments.models import Attachment
from apps.attachments.serializers import AttachmentSerializer
from apps.common.serializers import ContentTypeField
from .models import Comment
from .services import create_record_comment

User = get_user_model()


class CommentSerializer(serializers.ModelSerializer):
    content_type = ContentTypeField()
    author_name = serializers.SerializerMethodField()
    author_username = serializers.SerializerMethodField()
    author_avatar_url = serializers.SerializerMethodField()
    mentions = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    mentioned_users = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)
    can_delete = serializers.SerializerMethodField()
    parent_author_name = serializers.SerializerMethodField()
    parent_author_username = serializers.SerializerMethodField()
    parent_body = serializers.SerializerMethodField()
    attachment_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Attachment.objects.all(),
        required=False,
        write_only=True,
        source="attachments",
    )
    body = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "content_type",
            "object_id",
            "author",
            "author_name",
            "author_username",
            "author_avatar_url",
            "parent",
            "mentions",
            "mentioned_users",
            "attachments",
            "can_delete",
            "parent_author_name",
            "parent_author_username",
            "parent_body",
            "attachment_ids",
            "body",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "author",
            "can_delete",
            "parent_author_name",
            "parent_author_username",
            "parent_body",
            "created_at",
            "updated_at",
        )

    def get_mentioned_users(self, obj):
        return [
            {"id": user.id, "username": user.username, "name": user.get_full_name()}
            for user in obj.mentions.all()
        ]

    def get_author_name(self, obj):
        if not obj.author:
            return "Deleted user"
        return obj.author.get_full_name()

    def get_author_username(self, obj):
        if not obj.author:
            return "deleted-user"
        return obj.author.username

    def get_author_avatar_url(self, obj):
        if not obj.author:
            return ""
        return UserSerializer(obj.author, context=self.context).data["avatar_url"]

    def get_can_delete(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.author_id == request.user.id)

    def get_parent_author_name(self, obj):
        if not obj.parent:
            return ""
        if not obj.parent.author:
            return "Deleted user"
        return obj.parent.author.get_full_name()

    def get_parent_author_username(self, obj):
        if not obj.parent:
            return ""
        if not obj.parent.author:
            return "deleted-user"
        return obj.parent.author.username

    def get_parent_body(self, obj):
        if not obj.parent:
            return ""
        return obj.parent.body

    def validate(self, attrs):
        body = attrs.get("body", "")
        attachments = attrs.get("attachments", [])
        if not body.strip() and not attachments:
            raise serializers.ValidationError("Comment body or attachments are required.")
        return attrs

    def create(self, validated_data):
        mentions = validated_data.pop("mentions", [])
        attachments = validated_data.pop("attachments", [])
        return create_record_comment(
            author=self.context["request"].user,
            content_type=validated_data.get("content_type"),
            object_id=validated_data.get("object_id", ""),
            body=validated_data.get("body", ""),
            parent=validated_data.get("parent"),
            mentions=mentions,
            attachments=attachments,
        )
