import logging

from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.accounts.permissions import IsBusinessWriterOrReadOnly
from apps.agentic.services.playbooks import create_pending_playbook_run, list_playbook_definitions
from apps.audit.context import audit_actor
from apps.cases.models import Case
from apps.common.advanced_filters import AdvancedFilterBackend
from .models import Playbook
from .serializers import PlaybookRunMessageSerializer, PlaybookSerializer

logger = logging.getLogger(__name__)


class PlaybookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Playbook.objects.select_related("user", "case")
    serializer_class = PlaybookSerializer
    permission_classes = [permissions.IsAuthenticated, IsBusinessWriterOrReadOnly]
    lookup_field = "id"
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter, AdvancedFilterBackend)
    search_fields = ("playbook_id", "name", "job_id", "user_input", "remark")
    ordering_fields = ("created_at", "updated_at", "job_status", "started_at", "finished_at")
    filterset_fields = ("job_status", "case__id")
    advanced_filter_fields = {
        "playbook_id": "text",
        "job_status": "select",
        "name": "text",
        "job_id": "text",
        "user_input": "text",
        "remark": "text",
        "created_at": "date",
        "updated_at": "date",
        "started_at": "date",
        "finished_at": "date",
    }

    @action(detail=False, methods=["get"], url_path="definitions")
    def definitions(self, request):
        return Response(list_playbook_definitions())

    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, id=None):
        playbook = self.get_object()
        queryset = playbook.run_messages.order_by("sequence")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PlaybookRunMessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(PlaybookRunMessageSerializer(queryset, many=True).data)

    @action(detail=False, methods=["post"], url_path="run")
    def run(self, request):
        name = request.data.get("name")
        case_id = request.data.get("case")
        user_input = request.data.get("user_input", "")

        if not name:
            return Response({"name": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
        if not case_id:
            return Response({"case": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            case = Case.objects.get(pk=case_id)
        except (Case.DoesNotExist, ValidationError, ValueError, TypeError):
            return Response({"detail": "Case not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            with audit_actor(request.user):
                playbook = create_pending_playbook_run(
                    name=name,
                    case=case,
                    user=request.user,
                    user_input=user_input,
                )
        except ValueError:
            logger.info("Invalid playbook run request", exc_info=True)
            return Response({"detail": "Unknown playbook definition."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(playbook).data, status=status.HTTP_201_CREATED)
