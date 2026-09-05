from typing import Any

from pydantic import BaseModel, Field


class CMDBProviderResult(BaseModel):
    artifact_type: str = ""
    artifact_value: str = ""
    provider: str = ""
    supported: bool = False
    record_type: str = ""
    asset: dict[str, Any] = Field(default_factory=dict)
    identity: dict[str, Any] = Field(default_factory=dict)
    mailbox: dict[str, Any] = Field(default_factory=dict)
    resource: dict[str, Any] = Field(default_factory=dict)
    port: dict[str, Any] = Field(default_factory=dict)
    subnet: dict[str, Any] = Field(default_factory=dict)
    business: dict[str, Any] = Field(default_factory=dict)
    owner: dict[str, Any] = Field(default_factory=dict)
    related: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class CMDBQueryOutput(BaseModel):
    artifact_type: str
    artifact_value: str
    results: list[CMDBProviderResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
