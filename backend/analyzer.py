import json
import os
import re
from collections import Counter
from typing import Any

from dotenv import load_dotenv

from .schemas import SafetySignal

load_dotenv()

HAZARDS = {
    "fire": ["fire", "smoke", "spark", "flame"],
    "electrical": ["electrical", "electric", "shock", "wire", "cable", "panel"],
    "fall": ["fall", "scaffold", "scaffolding", "ladder", "guard rail", "guardrail", "height"],
    "chemical": ["chemical", "solvent", "gas", "leak", "toxic", "spill"],
    "equipment_failure": ["machine", "equipment", "pump", "valve", "brake", "failure", "malfunction"],
    "lifting": ["crane", "lifting", "load", "rigging", "hoist"],
}

SEVERITY_WEIGHT = {"low": 10, "medium": 30, "high": 60, "critical": 85}


def _contains(text: str, words: list[str]) -> list[str]:
    t = text.lower()
    return [w for w in words if w in t]


def fallback_extract(text: str, report_id: str | None = None) -> SafetySignal:
    t = text.lower()
    hazard_scores = {h: len(_contains(t, words)) for h, words in HAZARDS.items()}
    hazard = max(hazard_scores, key=hazard_scores.get) if max(hazard_scores.values()) else "unknown"

    critical_terms = ["injury", "fatal", "fire", "shock", "leak", "collapse", "unconscious"]
    high_terms = ["missing", "failed", "damaged", "unsafe", "loose", "expired", "no ppe", "without ppe"]
    precursors = critical_terms + high_terms + ["near miss", "complaint", "repeat", "again"]
    found = [w for w in precursors if w in t]

    if any(w in t for w in ["fatal", "collapse", "unconscious"]):
        severity = "critical"
    elif any(w in t for w in ["injury", "fire", "shock", "chemical leak"]):
        severity = "high"
    elif found:
        severity = "medium"
    else:
        severity = "low"

    location = "unknown"
    m = re.search(r"(?:at|near|in|zone|area)\s+([A-Z][A-Za-z0-9 -]{2,30})", text)
    if m:
        location = m.group(1).strip(" .,")

    root_causes = []
    for phrase in ["missing guard rail", "loose scaffolding", "worker fatigue", "expired equipment", "poor housekeeping", "no ppe", "damaged cable"]:
        if phrase in t:
            root_causes.append(phrase)

    score = min(100, SEVERITY_WEIGHT[severity] + min(20, len(found) * 5) + min(15, hazard_scores.get(hazard, 0) * 5))
    urgency = "immediate" if score >= 80 else "urgent" if score >= 55 else "monitor"
    return SafetySignal(
        report_id=report_id,
        hazard_type=hazard,
        location=location,
        asset="unknown",
        event_type="incident" if "injury" in t or "fire" in t else "near_miss",
        severity=severity,
        root_causes=root_causes,
        precursor_terms=found,
        risk_score=score,
        urgency=urgency,
        rationale=f"Detected {hazard} indicators and {severity} severity language. Score is an explainable demo heuristic."
    )


def llm_extract(text: str, report_id: str | None = None) -> SafetySignal:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback_extract(text, report_id)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        schema = SafetySignal.model_json_schema()
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a safety analyst. Extract only evidence supported by the report. Return JSON matching this schema. Do not invent facts. Risk score is 0-100 and should be conservative. Schema: " + json.dumps(schema)},
                {"role": "user", "content": text},
            ],
        )
        data: dict[str, Any] = json.loads(response.choices[0].message.content)
        data["report_id"] = report_id
        return SafetySignal.model_validate(data)
    except Exception:
        return fallback_extract(text, report_id)


def cluster_signals(signals: list[SafetySignal]) -> list[dict[str, Any]]:
    groups: dict[str, list[SafetySignal]] = {}
    for s in signals:
        key = f"{s.hazard_type}|{s.location.lower()}"
        groups.setdefault(key, []).append(s)

    results = []
    for idx, (key, items) in enumerate(groups.items(), start=1):
        if len(items) < 2:
            continue
        hazards = Counter(s.hazard_type for s in items)
        causes = Counter(c for s in items for c in s.root_causes + s.precursor_terms)
        avg_score = round(sum(s.risk_score for s in items) / len(items))
        risk = "critical" if avg_score >= 80 or len(items) >= 5 else "high" if avg_score >= 55 or len(items) >= 3 else "medium"
        top_cause = causes.most_common(1)[0][0] if causes else hazards.most_common(1)[0][0]
        results.append({
            "cluster_id": idx,
            "label": key.replace("|", " / "),
            "report_ids": [s.report_id or str(i) for i, s in enumerate(items)],
            "count": len(items),
            "risk_level": risk,
            "explanation": f"{len(items)} related reports share the same hazard/location pattern; recurring signal: {top_cause}. Average risk score: {avg_score}."
        })
    return sorted(results, key=lambda x: (x["count"], x["risk_level"]), reverse=True)
