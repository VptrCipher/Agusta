from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel


class AgenticJobStatus(models.TextChoices):
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILED = "Failed"


class CaseAnalysisJob(BaseModel):
    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="agentic_analysis_jobs",
    )
    status = models.CharField(
        max_length=20,
        choices=AgenticJobStatus,
        default=AgenticJobStatus.PENDING,
        db_index=True,
    )
    trigger = models.CharField(max_length=100, blank=True, default="")
    scheduled_at = models.DateTimeField(default=timezone.now, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    queue_message_id = models.CharField(max_length=255, blank=True, default="")
    error = models.TextField(blank=True, default="")
    result_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "agentic_case_analysis_jobs"
        ordering = ["scheduled_at", "created_at"]

    def __str__(self):
        return f"{self.case.case_id or self.case_id} {self.status}"
