import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel

from .schemas import SafetyReport, ClusterRequest
from .analyzer import llm_extract, cluster_signals
from .ocr import extract_text_from_file
from .storage import init_db, save_signal, save_feedback, feedback_summary

app = FastAPI(title="SafeSense AI", version="0.2.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


class FeedbackRequest(BaseModel):
    cluster_id: str
    decision: str
    comment: str = ""


def _send_alert(clusters: list[dict]) -> dict:
    critical = [c for c in clusters if c.get("risk_level") == "CRITICAL"]
    high = [c for c in clusters if c.get("risk_level") == "HIGH"]
    targets = critical + high
    if not targets:
        return {"sent": False, "reason": "No HIGH/CRITICAL cluster"}
    webhook = os.getenv("ALERT_WEBHOOK_URL")
    if not webhook:
        return {"sent": False, "reason": "No ALERT_WEBHOOK_URL configured", "would_alert": True, "clusters": [c["label"] for c in targets]}
    try:
        import requests
        payload = {"text": "🚨 SafeSense AI safety alert\n" + "\n".join(f"{c['risk_level']}: {c['label']} — {c['explanation']}" for c in targets)}
        response = requests.post(webhook, json=payload, timeout=8)
        response.raise_for_status()
        return {"sent": True, "clusters": [c["cluster_id"] for c in targets]}
    except Exception as exc:
        return {"sent": False, "reason": f"Webhook failed: {exc}"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "SafeSense AI", "version": "0.2.0"}


@app.get("/feedback-summary")
def get_feedback_summary():
    return feedback_summary()


@app.post("/feedback")
def feedback(request: FeedbackRequest):
    try:
        save_feedback(request.cluster_id, request.decision, request.comment)
        return {"status": "saved", "cluster_id": request.cluster_id, "decision": request.decision}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/analyze")
def analyze(report: SafetyReport):
    signal = llm_extract(report.text, report.report_id)
    save_signal(report.report_id or "UNNAMED", report.text, signal)
    return signal


@app.post("/cluster")
def cluster(request: ClusterRequest):
    signals = []
    for report in request.reports:
        signal = llm_extract(report.text, report.report_id)
        signals.append(signal)
        save_signal(report.report_id or "UNNAMED", report.text, signal)
    clusters = cluster_signals(signals)
    return {"signals": signals, "clusters": clusters, "alert": _send_alert(clusters), "feedback": feedback_summary()}


@app.post("/analyze-file")
async def analyze_file(file: UploadFile = File(...)):
    suffix = Path(file.filename or "report.txt").suffix.lower() or ".txt"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name
    try:
        text = extract_text_from_file(temp_path)
        report_id = file.filename or "UPLOADED-REPORT"
        signal = llm_extract(text, report_id)
        save_signal(report_id, text, signal)
        return signal
    finally:
        Path(temp_path).unlink(missing_ok=True)
