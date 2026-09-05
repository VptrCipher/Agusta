import uuid

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.common.readable_ids import save_with_readable_id


class PlaybookJobStatus(models.TextChoices):
    SUCCESS = "Success"
    FAILED = "Failed"
    PENDING = "Pending"
    RUNNING = "Running"


class Playbook(BaseModel):
    playbook_id = models.CharField(max_length=32, unique=True, editable=False, db_index=True, blank=True, default="", help_text="Record ID e.g. playbook_000001 (记录 ID e.g. playbook_000001)")
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, related_name="playbooks", help_text="Trigger source record ID e.g. case_000001(触发源记录 ID e.g. case_0000001)")
    name = models.CharField(max_length=255, blank=True, default="", help_text="Executed playbook name (执行剧本名称)")
    user_input = models.TextField(blank=True, default="", help_text="Initial or follow-up user input (初始或后续用户输入)")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="playbooks",
        help_text="Playbook requester (剧本请求者)",
    )
    job_status = models.CharField(
        max_length=20, choices=PlaybookJobStatus, blank=True, default="",
        help_text="Background job status (后台任务状态)",
    )
    job_id = models.CharField(max_length=255, blank=True, default="", help_text="Background job ID (后台任务 ID)")
    started_at = models.DateTimeField(null=True, blank=True, help_text="Execution start time (执行开始时间)")
    finished_at = models.DateTimeField(null=True, blank=True, help_text="Execution finish time (执行结束时间)")
    remark = models.TextField(blank=True, default="", help_text="Execution remark (执行备注)")

    class Meta:
        db_table = "playbooks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at", "job_status"], name="playbook_created_job_idx"),
        ]

    def save(self, *args, **kwargs):
        return save_with_readable_id(self, "playbook_id", "playbook", *args, **kwargs)

    def __str__(self):
        return self.name or str(self.id)


class PlaybookRunMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playbook_run = models.ForeignKey(
        Playbook,
        on_delete=models.CASCADE,
        related_name="run_messages",
    )
    sequence = models.PositiveBigIntegerField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "playbook_run_messages"
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["playbook_run", "sequence"],
                name="playbook_msg_run_seq_uniq",
            ),
        ]
        indexes = [
            models.Index(
                fields=["playbook_run", "sequence"],
                name="playbook_msg_run_seq_idx",
            ),
        ]
