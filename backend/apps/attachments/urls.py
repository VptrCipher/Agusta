from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AttachmentDownloadView, AttachmentViewSet

router = DefaultRouter()
router.register("attachments", AttachmentViewSet, basename="attachment")

urlpatterns = [
    path(
        "attachments/<uuid:access_key>/download/",
        AttachmentDownloadView.as_view(),
        name="attachment-download",
    ),
    path("", include(router.urls)),
]
