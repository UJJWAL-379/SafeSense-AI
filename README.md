# 🛡️ SafeSense AI

### AI/NLP Engine to Detect Safety Precursors

SafeSense turns messy workplace safety reports into **structured risk signals** and detects recurring precursor patterns before they become serious incidents.

> **Hackathon value proposition:** reports already exist — SafeSense makes them searchable, comparable and actionable at scale.

## 🎯 The judge demo in 60 seconds

1. Start the FastAPI backend.
2. Start the Streamlit dashboard.
3. Open **Precursor cluster demo**.
4. Select all demo reports.
5. Click **Detect Emerging Safety Risks**.
6. Show that RPT-001, RPT-002, RPT-005 and RPT-007 all point to **Zone B · Tower 3 / fall risk**.
7. The system raises a **CRITICAL emerging precursor cluster** and explains the recommended action.
8. Switch to **Live report**, paste a messy Hinglish/English note, and show structured extraction.
9. Optionally upload a TXT/PDF/image to demonstrate the ingestion/OCR path.

The key story is: **minor reports individually → repeated pattern collectively → early warning.**

## 🧠 Architecture

```text
PDF / Image / TXT / WhatsApp / Email / Excel
                    │
                    ▼
              OCR / Text Input
                    │
                    ▼
          Normalization & cleanup
          ├─ OCR noise handling
          ├─ abbreviations (PPE/LOTO)
          └─ mixed-language normalization
                    │
                    ▼
             LLM / NLP extraction
                    │
                    ▼
        Structured SafetySignal JSON
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
    Risk scoring       Cross-report clustering
          │                   │
          └─────────┬─────────┘
                    ▼
          Emerging precursor alert
                    │
                    ▼
             Streamlit dashboard
```

## ✨ Features

- Raw safety-report text analysis
- TXT/PDF/image upload through the backend
- OCR using Tesseract for images
- PDF text extraction using pypdf
- Optional OpenAI structured extraction
- Deterministic local fallback — **the demo works without an API key**
- Hazard classification: fall, electrical, chemical, fire, equipment, lifting, housekeeping
- Location and asset extraction
- Severity and explainable 0–100 risk score
- Root-cause and precursor-term extraction
- Cross-report hazard/location clustering
- CRITICAL/HIGH/MEDIUM emerging-risk levels
- Recommended corrective action
- Dashboard charts and report-level drilldown

## 🧪 Demo dataset

`data/precursor_export.json` is based on the supplied precursor-safety-dashboard prototype and includes different source types such as Inspector Log, WhatsApp, Excel, PDF Scan and Email. The strongest demo cluster is **Zone B · Tower 3**, where four separate reports describe recurring fall/scaffolding precursors.

## 🚀 Run locally

Requires Python 3.10+.

### Terminal 1 — backend

```bash
python -m venv .venv
```

Windows:

```bash
.venv\\Scripts\\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Optional LLM configuration:

```bash
copy .env.example .env
```

or on macOS/Linux:

```bash
cp .env.example .env
```

Then put your API key in `.env` if you want LLM mode. Otherwise leave it empty.

Start API:

```bash
uvicorn backend.main:app --reload
```

### Terminal 2 — dashboard

```bash
streamlit run dashboard/app.py
```

Open the local Streamlit URL shown in the terminal.

## 🔌 API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Backend health check |
| `POST /analyze` | Analyze one text report |
| `POST /analyze-file` | Analyze TXT/PDF/image upload |
| `POST /cluster` | Analyze multiple reports and detect recurring clusters |

Example request:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"report_id":"DEMO-01","text":"Tower 3 scaffolding wobbling again. Bolt missing. Zone B."}'
```

## 🔐 LLM mode

Set:

```text
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

If the LLM is unavailable, SafeSense automatically falls back to the local explainable extractor. This is deliberate for hackathon reliability.

## 🏗️ Project structure

```text
SafeSense-AI/
├── backend/
│   ├── main.py          # FastAPI routes
│   ├── analyzer.py      # NLP/LLM extraction + risk + clustering
│   ├── schemas.py       # Pydantic safety schemas
│   └── ocr.py           # TXT/PDF/image extraction
├── dashboard/
│   └── app.py           # Judge-ready Streamlit UI
├── data/
│   ├── demo_reports.json
│   └── precursor_export.json
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

## ⚠️ Important safety boundary

SafeSense is a **decision-support prototype**, not an autonomous safety authority. Its outputs must be verified by qualified safety personnel and should not replace emergency procedures, inspections, statutory reporting or formal risk assessments. Production deployment requires organization-specific validation and calibration.

## 🏆 What makes this different

The innovation is not simply extracting keywords. SafeSense connects **time, location, asset, hazard and repeated language across many unstructured reports**. That enables a safety team to act on an emerging pattern before it becomes a major incident.
