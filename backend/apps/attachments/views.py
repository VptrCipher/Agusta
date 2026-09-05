import mimetypes

from botocore.exceptions import ClientError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, parsers
from rest_framework.views import APIView

from .models import Attachment
from .serializers import AttachmentSerializer


def attachment_file_response(attachment):
    content_type = mimetypes.guess_type(attachment.filename)[0] or "application/octet-stream"

    try:
        file_obj = attachment.file.open("rb")
    except FileNotFoundError as exc:
        raise Http404("Attachment file not found") from exc
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"403", "404", "AccessDenied", "Forbidden", "NoSuchKey", "NotFound"}:
            raise Http404("Attachment file not found") from exc
        raise

    return FileResponse(
        file_obj,
        as_attachment=False,
        filename=attachment.filename,
        content_type=content_type,
    )

class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        return Attachment.objects.select_related("uploaded_by")

    def perform_create(self, serializer):
        f = self.request.FILES["file"]
        serializer.save(
            uploaded_by=self.request.user,
            filename=f.name,
            size=f.size,
        )

    def perform_destroy(self, instance):
        instance.file.delete(save=False)
        instance.delete()


class AttachmentDownloadView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, access_key):
        attachment = get_object_or_404(Attachment, access_key=access_key)
        return attachment_file_response(attachment)
