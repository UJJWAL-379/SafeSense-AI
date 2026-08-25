from typing import List, Optional
from pydantic import BaseModel, Field


class SafetyReport(BaseModel):
    text: str = Field(min_length=3)
    report_id: Optional[str] = None


class SafetySignal(BaseModel):
    report_id: Optional[str] = None
    hazard_type: str = "unknown"
    location: str = "unknown"
    asset: str = "unknown"
    event_type: str = "near_miss"
    severity: str = "low"
    root_causes: List[str] = []
    precursor_terms: List[str] = []
    date_signal: Optional[str] = None
    risk_score: int = 0
    urgency: str = "monitor"
    rationale: str = ""


class ClusterRequest(BaseModel):
    reports: List[SafetyReport]


class Cluster(BaseModel):
    cluster_id: int
    label: str
    report_ids: List[str]
    count: int
    risk_level: str
    explanation: str
