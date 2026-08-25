# Publish SafeSense with Bolt

Bolt's QuickStart publishing flow is designed for web apps: build/import the project, verify it in Preview, then use **Publish** and the second **Publish** confirmation to deploy it to Bolt hosting. See the official guide: https://support.bolt.new/get-started/quickstart#part-8-publish-your-project

## Recommended SafeSense setup

This repository now has two presentation surfaces:

1. `frontend/` — Vite + React judge-facing web app. This is the surface to import into Bolt and publish.
2. `dashboard/` — Streamlit dashboard for local/hackathon use and as a richer Python-side fallback.
3. `backend/` — FastAPI API for NLP extraction, OCR, risk scoring, clustering, feedback and alerts.

### 1. Import the repository into Bolt

Use the GitHub integration to open `UJJWAL-379/SafeSense-AI`. If Bolt asks what to work on, point it to `frontend/` and keep the existing visual design.

### 2. Configure the API URL

The frontend reads:

```text
VITE_API_URL
```

For local development it defaults to `http://localhost:8000`.

For a public demo, deploy the FastAPI backend first and set `VITE_API_URL` to the public HTTPS API origin before publishing the frontend.

### 3. Verify in Preview

Judge flow:

- Open **Precursor cluster demo**.
- Keep all eight demo reports selected.
- Click **Detect Emerging Safety Risks**.
- Verify the Zone B / Tower 3 critical cluster appears.
- Switch to **Live report**.
- Paste a messy Hinglish report and verify structured extraction.

### 4. Publish

Follow Bolt's documented flow:

1. Click **Publish** in the top-right.
2. Click the second **Publish** button.
3. Wait for deployment.
4. Open the published URL from the chat window.

### Important architecture note

Bolt hosting publishes the web experience; it does not turn the Python FastAPI/Streamlit process into a browser-side service. For the full live AI flow, the FastAPI backend must also be reachable over HTTPS. The included `render.yaml` and `Dockerfile` provide a straightforward backend deployment path.

Never put `OPENAI_API_KEY` in frontend code or `VITE_*` variables. Frontend environment variables are exposed to the browser. Keep LLM and webhook secrets only on the backend.

## No-backend fallback

The local Streamlit demo intentionally has a deterministic fallback extractor, so the judges can still see the core extraction and clustering story if the external LLM is unavailable.
