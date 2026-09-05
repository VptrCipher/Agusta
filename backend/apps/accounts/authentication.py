from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import UserApiKey


class ApiKeyAuthentication(BaseAuthentication):
    keyword = "Api-Key"

    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header:
            return None

        parts = header.split()
        if not parts or parts[0] != self.keyword:
            return None
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid API key header")

        try:
            api_key = UserApiKey.objects.select_related("user").get(key=parts[1])
        except UserApiKey.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid API key") from exc

        if api_key.is_expired:
            raise AuthenticationFailed("API key expired")
        if not api_key.user.is_active:
            raise AuthenticationFailed("API key user disabled")

        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at", "updated_at"])
        return api_key.user, api_key
