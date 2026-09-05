from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EnrichmentViewSet

router = DefaultRouter()
router.register("enrichments", EnrichmentViewSet, basename="enrichment")
urlpatterns = [path("", include(router.urls))]
