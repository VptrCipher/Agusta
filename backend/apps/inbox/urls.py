from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InboxMessageViewSet

router = DefaultRouter()
router.register("inbox/messages", InboxMessageViewSet, basename="inbox-message")

urlpatterns = [path("", include(router.urls))]
