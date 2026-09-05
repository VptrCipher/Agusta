from pydantic import BaseModel, ConfigDict, Field


class AffectedAsset(BaseModel):
    asset_type: str
    asset_value: str


class EvidenceFinding(BaseModel):
    title: str
    finding_type: str
    subject: str
    evidence: str
    conclusion: str


class AttackChainStep(BaseModel):
    attack_stage: str
    description: str


class TimelineEvent(BaseModel):
    timestamp: str
    attack_behavior: str
    evidence_field: str


class IndicatorOfCompromise(BaseModel):
    indicator_type: str
    value: str
    context: str


class Remediation(BaseModel):
    action_type: str
    description: str
    priority: str


class InvestigationReport(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    verdict: str
    severity: str
    impact: str
    priority: str
    confidence: str
    digest: str
    affected_assets: list[AffectedAsset] = Field(default_factory=list)
    evidence_findings: list[EvidenceFinding] = Field(default_factory=list)
    attack_chain: list[AttackChainStep] = Field(default_factory=list)
    attack_timeline: list[TimelineEvent] = Field(default_factory=list)
    ioc_indicators: list[IndicatorOfCompromise] = Field(default_factory=list)
    remediations: list[Remediation] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class KnowledgeSearchKeywords(BaseModel):
    keywords: list[str] = Field(default_factory=list)


class AnalysisRecord(BaseModel):
    trigger: str
    source_type: str = ""
    source_id: str = ""
    profile_version: str
    generated_at: str
    knowledge_keywords: list[str] = Field(default_factory=list)
    knowledge_records: list[dict] = Field(default_factory=list)
    report: InvestigationReport
