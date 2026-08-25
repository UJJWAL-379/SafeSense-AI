# 🛡️ SafeSense AI

### AI/NLP Engine to Detect Safety Precursors

SafeSense turns messy workplace safety reports into **structured risk signals** and detects recurring precursor patterns before they become serious incidents.

> **Hackathon value proposition:** reports already exist — SafeSense makes them searchable, comparable and actionable at scale.

## 🎯 Judge demo in 60 seconds

1. Open the published web frontend or run `frontend/` locally.
2. Open **Precursor cluster demo**.
3. Keep all eight demo reports selected.
4. Click **Detect Emerging Safety Risks**.
5. Show RPT-001, RPT-002, RPT-005 and RPT-007 converging on **Zone B · Tower 3 / fall risk**.
6. The system raises a **CRITICAL emerging precursor cluster** and recommends an immediate safety inspection.
7. Switch to **Live report** and paste a messy Hinglish/English note.
8. Show the structured hazard, location, severity, risk score and urgency.
9. If desired, use the Streamlit dashboard for PDF/image OCR and safety-officer feedback.

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
          ┌─────────┴─────────┐
          ▼                   ▼
   React/Bolt web UI      Streamlit UI
                    │
                    ▼
                 Judges
```

## ✨ Features

- Raw safety-report text analysis
- TXT/PDF/image/Excel upload through the FastAPI backend
- OCR using Tesseract for images
- PDF text extraction using pypdf
- Excel sheet extraction using pandas
- Optional OpenAI structured extraction
- Deterministic local fallback — **the core demo works without an API key**
- Hazard classification: fall, electrical, chemical, fire, equipment, lifting, housekeeping
- Location and asset extraction
- Severity and explainable 0–100 risk score
- Root-cause and precursor-term extraction
- Cross-report hazard/location clustering
- CRITICAL/HIGH/MEDIUM emerging-risk levels
- Recommended corrective action
- Webhook alert integration
- Safety-officer confirm/reject feedback loop
- SQLite persistence for the prototype
- Responsive React/Vite judge-facing frontend
- Streamlit dashboard for local/demo workflows
- Dockerized FastAPI backend
- Health endpoint and deployment configuration

## 🖥️ Published web frontend

The `frontend/` directory is a lightweight Vite + React judge-facing application designed to be imported into Bolt and published. It calls the FastAPI backend through `VITE_API_URL`.

For local frontend development:

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` to the backend URL when the API is not running on `http://localhost:8000`.

### Bolt publishing

Bolt's official QuickStart describes the final publishing flow as **Publish → Publish confirmation → wait for deployment → open the published URL**.

See [`docs/BOLT_PUBLISH.md`](docs/BOLT_PUBLISH.md) for the recommended architecture and exact judge-demo setup.

**Important:** Bolt hosts the browser-facing web experience. The Python FastAPI service still needs to be deployed separately over HTTPS for live AI analysis. Do not expose `OPENAI_API_KEY` in frontend environment variables.

## 🚀 Run locally

Requires Python 3.10+.

### Backend

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

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload
```

API docs are available at `/docs` and health at `/health`.

### Streamlit fallback dashboard

In another terminal:

```bash
streamlit run dashboard/app.py
```

### React web frontend

```bash
cd frontend
npm install
npm run dev
```

## ☁️ Production/demo deployment

The backend includes a Dockerfile and `render.yaml` deployment configuration. Deploy the FastAPI service and obtain its HTTPS URL. Then set the frontend's:

```text
VITE_API_URL=https://YOUR-BACKEND.example.com
```

Also configure backend CORS:

```text
CORS_ORIGINS=https://YOUR-BOLT-PUBLISHED-DOMAIN.example.com
```

Keep `OPENAI_API_KEY` and `ALERT_WEBHOOK_URL` on the backend only.

## 🔌 API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | Service metadata and links |
| `GET /health` | Deployment health check |
| `POST /analyze` | Analyze one text report |
| `POST /analyze-file` | Analyze TXT/PDF/image/Excel upload |
| `POST /cluster` | Analyze multiple reports and detect recurring clusters |
| `POST /feedback` | Save safety-officer confirmation/rejection |
| `GET /feedback-summary` | Feedback counts |

Example:

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

## 🧪 Demo dataset

`data/precursor_export.json` is based on the supplied precursor-safety-dashboard prototype and includes Inspector Log, WhatsApp, Excel, PDF Scan and Email inputs. The strongest demo cluster is **Zone B · Tower 3**, where four reports describe recurring fall/scaffolding precursors.

## 🧪 Verification

Run the dependency-light smoke test before presenting:

```bash
python tests/smoke_test.py
```

The test verifies the eight-report demo dataset, Tower 3 clustering, CRITICAL escalation and live report extraction.

GitHub Actions also compiles the Python code and runs the smoke test on pushes and pull requests.

## 🏗️ Project structure

```text
SafeSense-AI/
├── backend/
│   ├── main.py          # FastAPI API, CORS, upload limits, alerts
│   ├── analyzer.py      # NLP/LLM extraction + risk + clustering
│   ├── schemas.py       # Validated safety schemas
│   ├── storage.py       # SQLite persistence + feedback
│   └── ocr.py           # TXT/PDF/image/Excel extraction
├── dashboard/
│   └── app.py           # Streamlit fallback/judge dashboard
├── frontend/
│   ├── src/App.jsx      # Bolt-publishable judge UI
│   ├── src/style.css
│   └── package.json
├── data/
│   ├── demo_reports.json
│   └── precursor_export.json
├── docs/BOLT_PUBLISH.md
├── render.yaml
├── Dockerfile
├── .env.example
├── requirements.txt
└── README.md
```

## ⚠️ Important safety boundary

SafeSense is a **decision-support prototype**, not an autonomous safety authority. Its outputs must be verified by qualified safety personnel and should not replace emergency procedures, inspections, statutory reporting or formal risk assessments. Production deployment requires organization-specific validation and calibration.

## 🏆 What makes this different

The innovation is not simply extracting keywords. SafeSense connects **time, location, asset, hazard and repeated language across many unstructured reports**. That enables a safety team to act on an emerging pattern before it becomes a major incident.
