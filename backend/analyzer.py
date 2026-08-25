import json
import os
import re
from collections import Counter
from typing import Any
from dotenv import load_dotenv
from .schemas import SafetySignal
load_dotenv()

HAZARDS = {
    "fall": ["fall", "scaffold", "scaffolding", "ladder", "guard rail", "guardrail", "height", "wobbl", "bolt"],
    "electrical": ["electrical", "electric", "electrocution", "shock", "wire", "cable", "panel", "spark", "live wire"],
    "chemical": ["chemical", "solvent", "gas", "hcl", "toxic", "spill", "leak", "acid"],
    "fire": ["fire", "smoke", "flame", "ignition", "spark"],
    "equipment_failure": ["machine", "equipment", "pump", "valve", "brake", "failure", "malfunction", "damaged"],
    "lifting": ["crane", "lifting", "load", "rigging", "hoist"],
    "housekeeping": ["oil spill", "slip", "trip", "obstruction", "housekeeping"],
}
SEVERITY_WEIGHT = {"low": 10, "medium": 30, "high": 60, "critical": 85, "near-miss": 25}


def _contains(text: str, words: list[str]) -> list[str]:
    return [w for w in words if w.lower() in text.lower()]


def _clean(text: str) -> str:
    replacements = {"guardrail":"guard rail", "ppe":"personal protective equipment", "loto":"lock out tag out", "hai":"is", "tha":"was", "gaya":"went", "gir sakta hai":"may fall", "loose hai":"is loose"}
    out = text
    for src, dst in replacements.items():
        out = re.sub(rf"\b{re.escape(src)}\b", dst, out, flags=re.I)
    return re.sub(r"\s+", " ", out).strip()


def _extract_location(text: str) -> str:
    zone = re.search(r"\b(zone\s+[A-Za-z0-9]+)", text, flags=re.I)
    tower = re.search(r"\b(tower\s+[A-Za-z0-9]+)", text, flags=re.I)
    if zone and tower:
        return f"{zone.group(1).title()} · {tower.group(1).title()}"
    if zone:
        return zone.group(1).title()
    return "unknown"


def _extract_asset(text: str) -> str:
    patterns = [r"\b(scaffolding\s+tower\s+\w+)", r"\b(conveyor\s+\w+-?\w*)", r"\b(panel\s+[A-Za-z0-9-]+)", r"\b(pump\s+house)", r"\b(HCl\s+drum\s+\w+)", r"\b(welding\s+station\s+\w+-?\w*)"]
    for p in patterns:
        m = re.search(p, text, flags=re.I)
        if m:
            return m.group(1).strip()
    return "unknown"


def _date_signal(text: str) -> str | None:
    for p in [r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b"]:
        m = re.search(p, text, flags=re.I)
        if m:
            return m.group(0)
    return None


def fallback_extract(text: str, report_id: str | None = None) -> SafetySignal:
    original = text or ""
    t = _clean(original).lower()
    hazard_scores = {h: len(_contains(t, words)) for h, words in HAZARDS.items()}
    hazard = max(hazard_scores, key=hazard_scores.get) if max(hazard_scores.values()) else "unknown"
    critical_terms = ["fatal", "collapse", "unconscious", "live wire", "electrocution"]
    high_terms = ["injury", "fire", "shock", "sparks", "chemical leak", "wobbling", "wobbling again", "may collapse"]
    precursor_terms = ["missing", "damaged", "unsafe", "loose", "expired", "no ppe", "without ppe", "near miss", "near-miss", "complaint", "repeat", "again", "not followed", "not immediately tagged out"]
    found = [w for w in critical_terms + high_terms + precursor_terms if w in t]
    if any(w in t for w in critical_terms): severity = "critical"
    elif any(w in t for w in high_terms): severity = "high"
    elif "near miss" in t or "near-miss" in t: severity = "near-miss"
    elif found: severity = "medium"
    else: severity = "low"
    root_causes = []
    cause_map = {
        "missing guard rail": ["missing guard rail", "guard rail missing"],
        "structural failure": ["loose scaffolding", "scaffolding loose", "wobbling", "bolt missing"],
        "bolt missing": ["bolt missing", "missing bolt"],
        "worker fatigue": ["fatigue", "12hr shift", "12 hr shift"],
        "LOTO violation": ["loto not followed", "lock out tag out not followed", "lock out tag out"],
        "PPE non-compliance": ["no ppe", "without ppe", "ppe kit unavailable", "personal protective equipment"],
        "damaged cable": ["damaged cable", "insulation damaged", "exposed wire"],
        "poor housekeeping": ["oil spill", "oil rags", "slipped near storage"],
        "expired equipment": ["expired", "checked date 2023"],
    }
    for cause, phrases in cause_map.items():
        if any(p in t for p in phrases): root_causes.append(cause)
    base = SEVERITY_WEIGHT[severity]
    repetition_bonus = 15 if any(x in t for x in ["2nd time", "3rd complaint", "again", "repeat"]) else 0
    exposure_bonus = 10 if any(x in t for x in ["exposed", "live wire", "may collapse", "sparks"] ) else 0
    score = min(100, base + repetition_bonus + exposure_bonus + min(10, len(found) * 2))
    urgency = "immediate" if score >= 80 else "urgent" if score >= 55 else "monitor"
    event_type = "injury" if ("injury" in t and "no injury" not in t) or ("irritation" in t and "exposed" in t) else "near_miss"
    return SafetySignal(report_id=report_id, hazard_type=hazard, location=_extract_location(original), asset=_extract_asset(original), event_type=event_type, severity=severity, root_causes=root_causes, precursor_terms=sorted(set(found)), date_signal=_date_signal(original), risk_score=score, urgency=urgency, rationale=f"Detected {hazard} indicators, {len(root_causes)} root-cause signals and {len(found)} precursor terms. Score is an explainable fallback heuristic.")


def llm_extract(text: str, report_id: str | None = None) -> SafetySignal:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: return fallback_extract(text, report_id)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0, response_format={"type":"json_object"}, messages=[{"role":"system","content":"You are a conservative workplace safety analyst. Extract only evidence supported by the report. Normalize abbreviations and mixed-language phrases. Never invent location, asset, injury, or severity. Return JSON matching this schema exactly. Risk score is 0-100. " + json.dumps(SafetySignal.model_json_schema())},{"role":"user","content":text}])
        data: dict[str, Any] = json.loads(response.choices[0].message.content)
        data["report_id"] = report_id
        return SafetySignal.model_validate(data)
    except Exception:
        return fallback_extract(text, report_id)


def cluster_signals(signals: list[SafetySignal]) -> list[dict[str, Any]]:
    groups: dict[str, list[SafetySignal]] = {}
    for s in signals:
        key = f"{s.hazard_type}|{(s.location or 'unknown').strip().lower()}"
        groups.setdefault(key, []).append(s)
    results = []
    for idx, (key, items) in enumerate(groups.items(), start=1):
        if len(items) < 2: continue
        causes = Counter(c for s in items for c in s.root_causes + s.precursor_terms)
        avg_score = round(sum(s.risk_score for s in items) / len(items))
        repetition = sum(1 for s in items if any(x in s.precursor_terms for x in ["again", "repeat", "complaint"]))
        # Four linked reports in one location is itself a strong precursor signal.
        risk = "CRITICAL" if avg_score >= 80 or len(items) >= 5 or (len(items) >= 4 and avg_score >= 55) or repetition >= 2 else "HIGH" if avg_score >= 55 or len(items) >= 3 else "MEDIUM"
        top_cause = causes.most_common(1)[0][0] if causes else key.split("|")[0]
        action = {"CRITICAL":"Stop or isolate the affected activity/asset and perform an immediate safety inspection.","HIGH":"Escalate to the safety officer and close the recurring precursor before work continues.","MEDIUM":"Create a corrective action and verify the condition during the next inspection."}[risk]
        results.append({"cluster_id":idx,"label":key.replace("|"," / "),"report_ids":[s.report_id or str(i) for i,s in enumerate(items)],"count":len(items),"risk_level":risk,"average_risk_score":avg_score,"recurring_signal":top_cause,"recommendation":action,"explanation":f"{len(items)} reports share the same hazard/location pattern. Recurring signal: {top_cause}. Average risk score: {avg_score}."})
    return sorted(results, key=lambda x: (x["risk_level"] != "CRITICAL", -x["average_risk_score"], -x["count"]))
