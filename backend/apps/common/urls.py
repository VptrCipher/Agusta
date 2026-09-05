from django.urls import path

from .views import HealthView, ResourceMetadataView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("metadata/resources/", ResourceMetadataView.as_view(), name="resource-metadata"),
]
