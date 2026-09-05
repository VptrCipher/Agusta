from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PlaybookViewSet

router = DefaultRouter()
router.register("playbooks", PlaybookViewSet, basename="playbook")
urlpatterns = [path("", include(router.urls))]
