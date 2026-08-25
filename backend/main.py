import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .schemas import SafetyReport, ClusterRequest
from .analyzer import llm_extract, cluster_signals
from .ocr import extract_text_from_file
from .storage import init_db, save_signal, save_feedback, feedback_summary

APP_VERSION = "0.3.0"
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024

app = FastAPI(title="SafeSense AI", version=APP_VERSION, description="AI/NLP early-warning engine for safety precursors")

# Public frontend deployments need browser CORS. Keep it configurable instead of
# allowing every origin by default in production.
allowed_origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8501").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


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


@app.get("/")
def root():
    return {"service": "SafeSense AI", "version": APP_VERSION, "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "SafeSense AI", "version": APP_VERSION}


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
    allowed = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".webp", ".xlsx", ".xls"}
    filename = file.filename or "report.txt"
    suffix = Path(filename).suffix.lower() or ".txt"
    if suffix not in allowed:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {suffix}")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds MAX_UPLOAD_MB={MAX_UPLOAD_BYTES // (1024 * 1024)}")

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        temp_path = tmp.name
    try:
        text = extract_text_from_file(temp_path)
        report_id = filename
        signal = llm_extract(text, report_id)
        save_signal(report_id, text, signal)
        return signal
    finally:
        Path(temp_path).unlink(missing_ok=True)
