from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel
from apps.common.readable_ids import save_with_readable_id


class KnowledgeSource(models.TextChoices):
    MANUAL = "Manual"
    CASE = "Case"


class Knowledge(BaseModel):
    knowledge_id = models.CharField(max_length=32, unique=True, editable=False, db_index=True, blank=True, default="", help_text="Record ID e.g. knowledge_000001 (记录 ID e.g. knowledge_000001)")
    title = models.CharField(max_length=500, blank=True, default="", help_text="Knowledge title (知识标题)")
    body = models.TextField(blank=True, default="", help_text="Knowledge content (知识内容)")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Knowledge expiration time; empty means permanently valid (知识过期时间，空表示永久有效)")
    source = models.CharField(max_length=20, choices=KnowledgeSource, blank=True, default="", help_text="Knowledge source (知识来源)")
    tags = models.JSONField(default=list, blank=True, help_text="Knowledge tags (知识标签)")
    case = models.OneToOneField(
        "cases.Case",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="extracted_knowledge",
        help_text="Case this Knowledge was extracted from; empty for manual Knowledge (知识提取来源 Case, 手动知识为空)",
    )

    class Meta:
        db_table = "knowledge"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at", "source"], name="knowledge_created_src_idx"),
        ]

    def save(self, *args, **kwargs):
        return save_with_readable_id(self, "knowledge_id", "knowledge", *args, **kwargs)

    def clean(self):
        super().clean()
        if self.source == KnowledgeSource.CASE and self.case_id is None:
            raise ValidationError({"case": "Case-derived knowledge requires a case."})
        if self.source == KnowledgeSource.MANUAL and self.case_id is not None:
            raise ValidationError({"case": "Manual knowledge cannot be linked to a case."})

    def __str__(self):
        return self.title or str(self.id)
