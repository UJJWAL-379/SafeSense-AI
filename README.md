# SafeSense AI

**AI/NLP Engine to Detect Safety Precursors**

SafeSense converts messy safety reports into structured risk signals and detects recurring near-miss patterns before they become serious incidents.

## Architecture

`Report → OCR/Text cleanup → LLM extraction → Risk scoring → Precursor clustering → Dashboard/Alert`

## Features

- Safety report text and file ingestion
- OCR-ready processing
- Structured hazard extraction
- Explainable risk scoring
- Recurring precursor detection
- Semantic similarity clustering
- FastAPI backend
- Streamlit dashboard
- Synthetic demo data
- LLM API with deterministic fallback

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload
```

In another terminal:

```bash
streamlit run dashboard/app.py
```

## API

- `GET /health`
- `POST /analyze`
- `POST /cluster`

## Demo story

Several reports can look harmless individually: a loose board, missing guard rail, repeated worker complaint, or temporary equipment issue. SafeSense combines them by hazard, location, asset and semantic similarity to surface an **emerging precursor cluster**.

## Safety note

This is a hackathon decision-support prototype. It does not replace qualified safety professionals, statutory reporting, emergency procedures, inspections, or formal risk assessments. Production deployment requires validation against the organization's safety methodology.
