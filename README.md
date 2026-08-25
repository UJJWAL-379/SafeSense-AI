# 🛡️ SafeSense AI

### AI/NLP Early-Warning Engine for Safety Precursors

SafeSense turns messy workplace safety reports into **structured risk signals**, connects recurring precursor patterns across reports, and gives safety teams an explainable early warning before a serious incident.

> **Core idea:** minor reports individually → repeated pattern collectively → actionable early warning.

## 🎯 Why this matters

Factories, mines, construction sites and other high-risk organizations generate incident logs, near-miss reports, inspection notes, worker complaints, emails and spreadsheets. These reports are often noisy, abbreviated, typo-filled or mixed-language, so important precursor signals can remain buried in paperwork.

SafeSense adds an intelligence layer **without requiring organizations to change how they report incidents**.

---

## 🏆 60-second SIH judge demo

1. Open the web frontend.
2. Choose **Precursor Cluster Demo**.
3. Keep all eight demo reports selected.
4. Click **Detect Emerging Safety Risks**.
5. Show how `RPT-001`, `RPT-002`, `RPT-005` and `RPT-007` converge on **Zone B · Tower 3 / fall risk**.
6. Show the **CRITICAL emerging-risk alert** and recommended corrective action.
7. Open the linked reports and show that they came from different reporting channels and contain different wording.
8. Switch to **Live Report** and enter:

   `Tower 3 scaffolding loose hai, gir sakta hai. 2nd time. Guard rail missing. Zone B.`

9. Show the extracted hazard, location, asset, severity, risk score, root causes and urgency.
10. Explain the differentiator: **SafeSense connects reports that humans may review separately.**

### The "aha" moment

```text
RPT-001  Missing guard rail        ┐
RPT-002  Scaffolding loose         │
RPT-005  Wobbling / 3rd complaint  ├──► Zone B · Tower 3
RPT-007  Expired fall harness      │
                                   ┘
                                       ↓
                               🚨 CRITICAL RISK
                               Immediate inspection
```

---

## 🧠 Technical architecture

```text
PDF / Image / TXT / WhatsApp / Email / Excel
                    │
                    ▼
             Ingestion + OCR
                    │
                    ▼
         Text normalization layer
         ├─ OCR noise cleanup
         ├─ PPE / LOTO normalization
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
    Explainable risk     Similarity / clustering
       scoring                 │
          │                    │
          └─────────┬──────────┘
                    ▼
             Emerging risk
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      Web frontend       Streamlit fallback
          │
          ▼
       Judges / Safety Team
```

---

## ✨ Key features

### Ingestion
- TXT reports
- PDF reports
- Scanned images
- Excel logs
- Free-text / WhatsApp-style reports

### NLP / AI
- Hazard classification
- Location and asset extraction
- Severity classification
- Root-cause extraction
- Precursor-term extraction
- Date/frequency signals
- Hinglish/code-mixed normalization
- Optional structured LLM extraction
- Deterministic local fallback for reliable demos

### Intelligence
- Explainable 0–100 risk score
- Cross-report precursor clustering
- Recurring hazard/location detection
- Emerging-risk levels: **MEDIUM / HIGH / CRITICAL**
- Recommended corrective action
- Alert/webhook integration
- Safety-officer confirm/reject feedback loop

### Product
- Judge-focused React/Vite frontend
- Streamlit fallback dashboard
- SQLite persistence for the prototype
- FastAPI API
- Docker support
- Health endpoint
- GitHub Actions CI
- Bolt-compatible frontend publishing workflow

---

## 🔍 How the risk score works

The prototype combines:

- Base severity
- Critical/high-risk language
- Repeated complaints or recurrence
- Exposure indicators
- Root-cause signals
- Hazard context

The score is deliberately **explainable** rather than a black-box prediction.

Example:

```text
Missing guard rail       → precursor
Wobbling scaffolding     → structural signal
3rd complaint            → recurrence bonus
Tower 3 / Zone B         → repeated location
Expired harness          → exposure increase

                 ↓
        Emerging CRITICAL cluster
```

Production deployments should calibrate the scoring model against the organization's formal risk matrix and safety procedures.

---

## 🧩 Cross-report intelligence

The strongest differentiator is not extracting keywords from one report. SafeSense combines signals across reports using **hazard, location, asset, recurrence and similarity**.

The demo dataset contains eight reports from multiple source types, including Inspector Log, WhatsApp, Excel, PDF Scan and Email. Four reports converge on **Zone B · Tower 3**, creating the central demo cluster.

```text
4 separate reports
       ↓
Different wording + different channels
       ↓
Structured signals
       ↓
Cross-report pattern detection
       ↓
Emerging precursor cluster
       ↓
Human verification + corrective action
```

---

## 🖥️ Web frontend and Bolt publishing

The `frontend/` directory contains the judge-facing Vite + React application.

It is designed to be imported into Bolt and published as the browser-facing experience. Bolt's official QuickStart says to publish by clicking **Publish**, confirming the second Publish action, waiting for deployment, and opening the generated URL. urlBolt QuickStart — Part 8: Publish your projecthttps://support.bolt.new/get-started/quickstart#part-8-publish-your-project

### Recommended deployment architecture

```text
Bolt-published React frontend
            │
            │ HTTPS
            ▼
      FastAPI backend
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
     OCR   NLP   SQLite
            │
            ▼
       Risk engine
            │
            ▼
        Clustering
```

The Python backend must be deployed separately if the published frontend needs live API access. The backend should be exposed through HTTPS and configured with the frontend origin.

**Never expose `OPENAI_API_KEY` in frontend variables.** Keep secrets only on the backend.

See [`docs/BOLT_PUBLISH.md`](docs/BOLT_PUBLISH.md) for the deployment checklist.

---

## 🚀 Local setup

Requires Python 3.10+ and Node.js 18+ for the React frontend.

### 1. Clone

```bash
git clone https://github.com/UJJWAL-379/SafeSense-AI.git
cd SafeSense-AI
```

### 2. Backend

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
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

API docs: `http://localhost:8000/docs`

Health check: `http://localhost:8000/health`

### 3. React frontend

```bash
cd frontend
npm install
npm run dev
```

If the backend is not on the default URL, set:

```text
VITE_API_URL=http://localhost:8000
```

### 4. Streamlit fallback

```bash
streamlit run dashboard/app.py
```

---

## 🔌 API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | Service metadata |
| `GET /health` | Deployment health check |
| `POST /analyze` | Analyze one text report |
| `POST /analyze-file` | Analyze TXT/PDF/image/Excel upload |
| `POST /cluster` | Analyze multiple reports and detect recurring patterns |
| `POST /feedback` | Save safety-officer confirmation/rejection |
| `GET /feedback-summary` | Feedback statistics |

Example:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"report_id":"DEMO-01","text":"Tower 3 scaffolding wobbling again. Bolt missing. Zone B."}'
```

---

## 🤖 LLM mode

Configure:

```text
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

The application uses structured JSON extraction when an API key is available.

If the LLM is unavailable, SafeSense automatically uses the deterministic local extractor. This is intentional: **the core judge demo should not fail because of an external API.**

---

## 🧪 Pre-presentation verification

Run:

```bash
python tests/smoke_test.py
```

Then verify the frontend production build:

```bash
cd frontend
npm install
npm run build
```

Before the event, perform the complete judge flow once from the same environment you will use during the presentation.

GitHub Actions compiles the Python code and runs the smoke test on pushes and pull requests.

---

## 📁 Project structure

```text
SafeSense-AI/
├── backend/
│   ├── main.py              # FastAPI API + validation + alerts
│   ├── analyzer.py          # NLP/LLM + scoring + clustering
│   ├── schemas.py           # Pydantic models
│   ├── storage.py           # SQLite persistence + feedback
│   └── ocr.py               # TXT/PDF/image/Excel extraction
├── dashboard/
│   └── app.py               # Streamlit fallback dashboard
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Judge-facing React UI
│   │   ├── main.jsx
│   │   └── style.css
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── demo_reports.json
│   └── precursor_export.json
├── docs/
│   └── BOLT_PUBLISH.md
├── tests/
│   └── smoke_test.py
├── .github/workflows/
│   └── ci.yml
├── Dockerfile
├── render.yaml
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🛡️ Safety boundary

SafeSense is a **decision-support prototype**, not an autonomous safety authority.

Its outputs must be reviewed by qualified safety professionals and should not replace emergency procedures, statutory reporting, site inspections, formal risk assessments, permit-to-work systems, or organization-specific safety standards.

Production deployment requires validation, security review, privacy controls and calibration against the organization's approved safety methodology.

---

## 🚀 Future enhancements

1. **True semantic embeddings** for reports with different wording but the same meaning.
2. **Timeline-based precursor escalation** showing how risk grows over days.
3. **Explainable “Why flagged?” panel** showing exactly which signals triggered an alert.
4. **Before/after comparison**: separate reports versus one emerging-risk cluster.
5. **One-click Judge Demo** that automatically runs the complete Tower 3 scenario.
6. Organization-specific hazard taxonomies and risk matrices.
7. Role-based access control and audit trails.
8. PostgreSQL/vector database deployment for production scale.

---

## 🏆 Why SafeSense is different

Traditional safety systems store reports. SafeSense **connects them**.

```text
Unstructured reports
        ↓
Structured signals
        ↓
Recurring patterns
        ↓
Prioritized risk
        ↓
Human action
```

The goal is not to replace safety officers. The goal is to help them notice warning signs they would otherwise have to discover manually across hundreds or thousands of reports.
