from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from storages.backends.s3boto3 import S3Boto3Storage


class AttachmentS3Storage(S3Boto3Storage):
    required_settings = (
        "AWS_S3_ENDPOINT_URL",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_STORAGE_BUCKET_NAME",
    )

    def __init__(self, *args, **kwargs):
        missing_settings = [
            setting_name
            for setting_name in self.required_settings
            if not getattr(settings, setting_name, None)
        ]
        if missing_settings:
            missing_display = ", ".join(missing_settings)
            raise ImproperlyConfigured(
                f"Missing required attachment object storage settings: {missing_display}"
            )

        super().__init__(*args, **kwargs)
