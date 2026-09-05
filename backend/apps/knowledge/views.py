from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.accounts.permissions import IsBusinessWriterOrReadOnly
from apps.audit.mixins import AuditActorMixin
from apps.common.advanced_filters import AdvancedFilterBackend
from .models import Knowledge
from .serializers import KnowledgeSerializer


class KnowledgeViewSet(AuditActorMixin, viewsets.ModelViewSet):
    queryset = Knowledge.objects.select_related("case")
    serializer_class = KnowledgeSerializer
    permission_classes = [permissions.IsAuthenticated, IsBusinessWriterOrReadOnly]
    lookup_field = "id"
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter, AdvancedFilterBackend)
    search_fields = ("knowledge_id", "title", "body", "source")
    ordering_fields = ("created_at", "updated_at", "expires_at", "source")
    filterset_fields = ("source", "case")
    advanced_filter_fields = {
        "knowledge_id": "text",
        "source": "select",
        "tags": "tag",
        "title": "text",
        "body": "text",
        "expires_at": "date",
        "created_at": "date",
        "updated_at": "date",
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        tags = self.request.query_params.getlist("tags")
        if len(tags) == 1 and "," in tags[0]:
            tags = [item.strip() for item in tags[0].split(",") if item.strip()]
        for tag in tags:
            queryset = queryset.filter(tags__contains=tag)
        return queryset
