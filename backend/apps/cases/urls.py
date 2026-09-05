from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CaseRelationshipViewSet, CaseViewSet

router = DefaultRouter()
router.register("cases", CaseViewSet, basename="case")
router.register("case-relationships", CaseRelationshipViewSet, basename="case-relationship")

urlpatterns = [path("", include(router.urls))]
