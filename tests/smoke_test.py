"""Fast, dependency-light smoke test for the hackathon demo."""
import json
from pathlib import Path

from backend.analyzer import fallback_extract, cluster_signals
from backend.schemas import SafetyReport


def main():
    data = json.loads(Path("data/demo_reports.json").read_text(encoding="utf-8"))
    signals = [fallback_extract(r["text"], r["report_id"]) for r in data]
    clusters = cluster_signals(signals)

    assert len(signals) == 8, f"Expected 8 demo reports, got {len(signals)}"
    tower = [c for c in clusters if "zone b" in c["label"].lower() and "tower 3" in c["label"].lower()]
    assert tower, "Expected the Zone B / Tower 3 precursor cluster"
    assert tower[0]["count"] >= 4, "Expected at least four linked Tower 3 reports"
    assert tower[0]["risk_level"] == "CRITICAL", f"Unexpected cluster risk: {tower[0]['risk_level']}"

    sample = SafetyReport(text="Tower 3 scaffolding wobbling again. Bolt missing. Zone B.")
    signal = fallback_extract(sample.text, "SMOKE-001")
    assert signal.hazard_type == "fall"
    assert signal.location.lower() == "zone b · tower 3"
    assert signal.risk_score > 50

    print("SafeSense smoke test PASSED")
    print(f"Reports: {len(signals)} | Clusters: {len(clusters)} | Tower 3: {tower[0]['risk_level']}")


if __name__ == "__main__":
    main()
