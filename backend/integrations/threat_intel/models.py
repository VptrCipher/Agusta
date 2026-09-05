from pydantic import BaseModel, Field


class TIProviderResult(BaseModel):
    indicator: str = ""
    indicator_type: str = "unknown"
    provider: str = ""
    risk_level: str | None = None
    reputation_score: int | None = None
    is_malicious: bool | None = None
    tags: list[str] = Field(default_factory=list)
    attack_techniques: list[str] = Field(default_factory=list)
    malware_families: list[str] = Field(default_factory=list)
    adversaries: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    pulses: list[dict] = Field(default_factory=list)
    network_context: dict | None = None
    raw: dict = Field(default_factory=dict)
    error: str | None = None


class TIQueryOutput(BaseModel):
    indicator: str
    indicator_type: str
    results: list[TIProviderResult] = Field(default_factory=list)
    aggregated_risk_level: str | None = None
    errors: list[str] = Field(default_factory=list)
