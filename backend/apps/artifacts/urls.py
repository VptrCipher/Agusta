from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ArtifactViewSet

router = DefaultRouter()
router.register("artifacts", ArtifactViewSet, basename="artifact")
urlpatterns = [path("", include(router.urls))]
