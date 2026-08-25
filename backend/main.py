from fastapi import FastAPI, File, UploadFile
from tempfile import NamedTemporaryFile
from pathlib import Path

from .schemas import SafetyReport, ClusterRequest
from .analyzer import llm_extract, cluster_signals
from .ocr import extract_text_from_file

app = FastAPI(title="SafeSense AI", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "SafeSense AI"}


@app.post("/analyze")
def analyze(report: SafetyReport):
    return llm_extract(report.text, report.report_id)


@app.post("/cluster")
def cluster(request: ClusterRequest):
    signals = [llm_extract(r.text, r.report_id) for r in request.reports]
    return {"signals": signals, "clusters": cluster_signals(signals)}


@app.post("/analyze-file")
async def analyze_file(file: UploadFile = File(...)):
    suffix = Path(file.filename or "report.txt").suffix or ".txt"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name
    try:
        text = extract_text_from_file(temp_path)
        return llm_extract(text, file.filename)
    finally:
        Path(temp_path).unlink(missing_ok=True)
