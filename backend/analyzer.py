import json
import os
import re
from collections import Counter
from typing import Any

from dotenv import load_dotenv
from .schemas import SafetySignal

load_dotenv()

HAZARDS = {
    "fall": ["fall", "scaffold", "scaffolding", "ladder", "guard rail", "guardrail", "height", "wobbl", "bolt", "slip"],
    "electrical": ["electrical", "electric", "electrocution", "shock", "wire", "cable", "panel", "spark", "live wire"],
    "chemical": ["chemical", "solvent", "gas", "hcl", "toxic", "spill", "leak", "acid"],
    "fire": ["fire", "smoke", "flame", "ignition", "spark"],
    "equipment_failure": ["machine", "equipment", "pump", "valve", "brake", "failure", "malfunction", "damaged"],
    "lifting": ["crane", "lifting", "load", "rigging", "hoist"],
    "housekeeping": ["oil spill", "slip", "trip", "obstruction", "housekeeping", "leakage"],
}
SEVERITY_WEIGHT = {"low": 10, "medium": 30, "high": 60, "critical": 85, "near-miss": 25}


def _contains(text: str, words: list[str]) -> list[str]:
    return [w for w in words if w.lower() in text.lower()]


def _clean(text: str) -> str:
    replacements = {
        "guardrail": "guard rail", "ppe": "personal protective equipment", "loto": "lock out tag out",
        "hai": "is", "tha": "was", "gaya": "went", "gir sakta hai": "may fall", "loose hai": "is loose",
    }
    out = text or ""
    for src, dst in replacements.items():
        out = re.sub(rf"\b{re.escape(src)}\b", dst, out, flags=re.I)
    return re.sub(r"\s+", " ", out).strip()


def _extract_location(text: str) -> str:
    zone = re.search(r"\b(zone\s+[A-Za-z0-9-]+)", text, flags=re.I)
    tower = re.search(r"\b(tower\s+[A-Za-z0-9-]+)", text, flags=re.I)
    area = re.search(r"\b((?:plant|production|tank|boiler|warehouse|workshop)\s*(?:area|zone)?\s*[A-Za-z0-9-]*)", text, flags=re.I)
    if zone and tower:
        return f"{zone.group(1).title()} · {tower.group(1).title()}"
    if zone:
        return zone.group(1).title()
    if area:
        return area.group(1).strip().title()
    return "unknown"


def _extract_asset(text: str) -> str:
    patterns = [
        r"\b(scaffolding\s+tower\s+\w+)", r"\b(conveyor\s+\w+-?\w*)", r"\b(panel\s+[A-Za-z0-9-]+)",
        r"\b(pump\s+house)", r"\b(HCl\s+drum\s+\w+)", r"\b(welding\s+station\s+\w+-?\w*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(1).strip()
    return "unknown"


def _date_signal(text: str) -> str | None:
    for pattern in [r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b"]:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(0)
    return None


def fallback_extract(text: str, report_id: str | None = None) -> SafetySignal:
    original = text or ""
    t = _clean(original).lower()
    hazard_scores = {h: len(_contains(t, words)) for h, words in HAZARDS.items()}
    hazard = max(hazard_scores, key=hazard_scores.get) if max(hazard_scores.values()) else "unknown"
    critical_terms = ["fatal", "collapse", "unconscious", "live wire", "electrocution"]
    high_terms = ["injury", "fire", "shock", "sparks", "chemical leak", "wobbling", "wobbling again", "may collapse", "expired equipment", "expired", "still in use at height", "loose"]
    precursor_terms = ["missing", "damaged", "unsafe", "loose", "expired", "no ppe", "without ppe", "near miss", "near-miss", "complaint", "repeat", "again", "not followed", "not immediately tagged out"]
    found = [w for w in critical_terms + high_terms + precursor_terms if w in t]
    if any(w in t for w in critical_terms): severity = "critical"
    elif any(w in t for w in high_terms): severity = "high"
    elif "near miss" in t or "near-miss" in t: severity = "near-miss"
    elif found: severity = "medium"
    else: severity = "low"
    root_causes = []
    cause_map = {
        "missing guard rail": ["missing guard rail", "guard rail missing"], "structural failure": ["loose scaffolding", "scaffolding loose", "wobbling", "bolt missing"],
        "bolt missing": ["bolt missing", "missing bolt"], "worker fatigue": ["fatigue", "12hr shift", "12 hr shift"],
        "LOTO violation": ["loto not followed", "lock out tag out not followed", "lock out tag out"],
        "PPE non-compliance": ["no ppe", "without ppe", "ppe kit unavailable", "personal protective equipment"],
        "damaged cable": ["damaged cable", "insulation damaged", "exposed wire"], "poor housekeeping": ["oil spill", "oil rags", "slipped near storage"],
        "expired equipment": ["expired", "checked date 2023"],
    }
    for cause, phrases in cause_map.items():
        if any(p in t for p in phrases): root_causes.append(cause)
    base = SEVERITY_WEIGHT[severity]
    repetition_bonus = 15 if any(x in t for x in ["2nd time", "3rd complaint", "again", "repeat"]) else 0
    exposure_bonus = 10 if any(x in t for x in ["exposed", "live wire", "may collapse", "sparks"]) else 0
    score = min(100, base + repetition_bonus + exposure_bonus + min(10, len(found) * 2))
    urgency = "immediate" if score >= 80 else "urgent" if score >= 55 else "monitor"
    event_type = "injury" if (("injury" in t and "no injury" not in t) or ("irritation" in t and "exposed" in t)) else "near_miss"
    return SafetySignal(report_id=report_id, hazard_type=hazard, location=_extract_location(original), asset=_extract_asset(original), event_type=event_type, severity=severity, root_causes=root_causes, precursor_terms=sorted(set(found)), date_signal=_date_signal(original), risk_score=score, urgency=urgency, rationale=f"Detected {hazard} indicators, {len(root_causes)} root-cause signals and {len(found)} precursor terms. Score is an explainable fallback heuristic.")


def llm_extract(text: str, report_id: str | None = None) -> SafetySignal:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback_extract(text, report_id)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        context = "Indian industrial safety context: when relevant, classify using applicable Indian requirements such as the Factories Act, DGMS guidance for mines, and relevant BIS standards. Do not claim compliance unless the report supports it."
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a conservative workplace safety analyst. Extract only evidence supported by the report. Normalize abbreviations and mixed-language phrases. Never invent location, asset, injury, or severity. Return JSON matching this schema exactly. Risk score is 0-100. " + context + " " + json.dumps(SafetySignal.model_json_schema())},
                {"role": "user", "content": text},
            ],
        )
        data: dict[str, Any] = json.loads(response.choices[0].message.content)
        data["report_id"] = report_id
        return SafetySignal.model_validate(data)
    except Exception:
        return fallback_extract(text, report_id)


def _semantic_groups(signals: list[SafetySignal], threshold: float = 0.52) -> list[list[int]]:
    """Group reports by meaning; falls back to TF-IDF if the embedding model is unavailable."""
    if len(signals) < 2:
        return []
    texts = [f"{s.hazard_type} {s.location} {s.asset} {s.event_type} {' '.join(s.root_causes)} {' '.join(s.precursor_terms)}" for s in signals]
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
        matrix = model.encode(texts, normalize_embeddings=True)
        sim = cosine_similarity(matrix)
    except Exception:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform(texts)
        sim = cosine_similarity(matrix)
    parent = list(range(len(signals)))
    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb: parent[rb] = ra
    for i in range(len(signals)):
        for j in range(i + 1, len(signals)):
            same_location = signals[i].location != "unknown" and signals[i].location.lower() == signals[j].location.lower()
            same_hazard = signals[i].hazard_type == signals[j].hazard_type and signals[i].hazard_type != "unknown"
            if sim[i, j] >= threshold or (same_hazard and same_location and sim[i, j] >= 0.35):
                union(i, j)
    groups: dict[int, list[int]] = {}
    for i in range(len(signals)):
        groups.setdefault(find(i), []).append(i)
    return [g for g in groups.values() if len(g) >= 2]


def cluster_signals(signals: list[SafetySignal]) -> list[dict[str, Any]]:
    results = []
    for idx, indices in enumerate(_semantic_groups(signals), start=1):
        items = [signals[i] for i in indices]
        causes = Counter(c for s in items for c in s.root_causes + s.precursor_terms)
        avg_score = round(sum(s.risk_score for s in items) / len(items))
        repetition = sum(1 for s in items if any(x in s.precursor_terms for x in ["again", "repeat", "complaint"]))
        risk = "CRITICAL" if avg_score >= 80 or len(items) >= 5 or (len(items) >= 4 and avg_score >= 55) or repetition >= 2 else "HIGH" if avg_score >= 55 or len(items) >= 3 else "MEDIUM"
        top_cause = causes.most_common(1)[0][0] if causes else items[0].hazard_type
        locations = Counter(s.location for s in items if s.location != "unknown")
        hazards = Counter(s.hazard_type for s in items if s.hazard_type != "unknown")
        location = locations.most_common(1)[0][0] if locations else "multiple/unknown locations"
        hazard = hazards.most_common(1)[0][0] if hazards else "mixed hazard"
        action = {
            "CRITICAL": "Stop or isolate the affected activity/asset and perform an immediate safety inspection.",
            "HIGH": "Escalate to the safety officer and close the recurring precursor before work continues.",
            "MEDIUM": "Create a corrective action and verify the condition during the next inspection.",
        }[risk]
        results.append({
            "cluster_id": idx, "label": f"{hazard.replace('_', ' ').title()} / {location}",
            "report_ids": [s.report_id or str(i) for i, s in enumerate(items)], "count": len(items), "risk_level": risk,
            "average_risk_score": avg_score, "recurring_signal": top_cause, "recommendation": action,
            "explanation": f"{len(items)} reports are semantically similar and indicate a recurring {hazard.replace('_', ' ')} risk around {location}. Top signal: {top_cause}. Average risk score: {avg_score}.",
            "similarity_method": "sentence-transformers cosine similarity with TF-IDF fallback",
        })
    return sorted(results, key=lambda x: (x["risk_level"] != "CRITICAL", -x["average_risk_score"], -x["count"]))
