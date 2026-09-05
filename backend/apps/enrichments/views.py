from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.accounts.permissions import IsBusinessWriterOrReadOnly
from apps.audit.mixins import AuditActorMixin
from apps.common.advanced_filters import AdvancedFilterBackend
from .models import Enrichment
from .serializers import EnrichmentSerializer


class EnrichmentViewSet(AuditActorMixin, viewsets.ModelViewSet):
    queryset = Enrichment.objects.select_related("case", "alert", "artifact")
    serializer_class = EnrichmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsBusinessWriterOrReadOnly]
    lookup_field = "id"
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter, AdvancedFilterBackend)
    search_fields = ("enrichment_id", "name", "type", "provider", "uid", "value", "desc")
    ordering_fields = ("created_at", "updated_at", "type", "provider")
    filterset_fields = ("type", "provider", "case", "alert", "artifact")
    advanced_filter_fields = {
        "enrichment_id": "text",
        "type": "select",
        "provider": "select",
        "name": "text",
        "uid": "text",
        "value": "text",
        "desc": "text",
        "created_at": "date",
        "updated_at": "date",
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        content_type = self.request.query_params.get("content_type")
        object_id = self.request.query_params.get("object_id")
        if content_type and object_id and content_type in {"case", "alert", "artifact"}:
            return queryset.filter(**{content_type: object_id})
        return queryset
