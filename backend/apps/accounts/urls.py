from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import AuthViewSet, UserApiKeyViewSet, UserViewSet

router = DefaultRouter()
router.register("auth", AuthViewSet, basename="auth")
router.register("auth/users", UserViewSet, basename="user")
router.register("auth/api-keys", UserApiKeyViewSet, basename="api-key")

urlpatterns = [
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
