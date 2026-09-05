from typing import Any

from pydantic import BaseModel, Field


class SplunkPayload(BaseModel):
    search_name: str
    result: dict[str, Any]
    sid: str | None = None
    app: str | None = None
    owner: str | None = None
    results_link: str | None = None


class KibanaRule(BaseModel):
    name: str


class KibanaContext(BaseModel):
    hits: list[Any]


class KibanaPayload(BaseModel):
    rule: KibanaRule
    context: KibanaContext


class WebhookResult(BaseModel):
    status: str = "success"
    stream: str
    sent: int = 0
    skipped: int = 0
    message_ids: list[str] = Field(default_factory=list)
