import logging

from pydantic import ValidationError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.webhook.service import (
    WebhookRedisError,
    handle_kibana_webhook,
    handle_splunk_webhook,
)

logger = logging.getLogger(__name__)
INVALID_WEBHOOK_PAYLOAD_DETAIL = "Invalid webhook payload."
WEBHOOK_STREAM_UNAVAILABLE_DETAIL = "Webhook stream service is unavailable."


class SplunkWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            result = handle_splunk_webhook(request.data)
        except (ValidationError, ValueError):
            logger.info("Invalid Splunk webhook payload", exc_info=True)
            return Response({"detail": INVALID_WEBHOOK_PAYLOAD_DETAIL}, status=status.HTTP_400_BAD_REQUEST)
        except WebhookRedisError:
            logger.exception("Failed to process Splunk webhook")
            return Response({"detail": WEBHOOK_STREAM_UNAVAILABLE_DETAIL}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(result.model_dump(), status=status.HTTP_200_OK)


class KibanaWebhookView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            result = handle_kibana_webhook(request.data)
        except (ValidationError, ValueError):
            logger.info("Invalid Kibana webhook payload", exc_info=True)
            return Response({"detail": INVALID_WEBHOOK_PAYLOAD_DETAIL}, status=status.HTTP_400_BAD_REQUEST)
        except WebhookRedisError:
            logger.exception("Failed to process Kibana webhook")
            return Response({"detail": WEBHOOK_STREAM_UNAVAILABLE_DETAIL}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(result.model_dump(), status=status.HTTP_200_OK)
