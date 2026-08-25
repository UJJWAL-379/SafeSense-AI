from typing import List, Optional
from pydantic import BaseModel, Field


class SafetyReport(BaseModel):
    text: str = Field(min_length=3, max_length=20000)
    report_id: Optional[str] = Field(default=None, max_length=120)


class SafetySignal(BaseModel):
    report_id: Optional[str] = None
    hazard_type: str = "unknown"
    location: str = "unknown"
    asset: str = "unknown"
    event_type: str = "near_miss"
    severity: str = "low"
    root_causes: List[str] = Field(default_factory=list)
    precursor_terms: List[str] = Field(default_factory=list)
    date_signal: Optional[str] = None
    risk_score: int = Field(default=0, ge=0, le=100)
    urgency: str = "monitor"
    rationale: str = ""


class ClusterRequest(BaseModel):
    reports: List[SafetyReport] = Field(min_length=1, max_length=100)


class Cluster(BaseModel):
    cluster_id: int
    label: str
    report_ids: List[str]
    count: int
    risk_level: str
    explanation: str
