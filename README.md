<div align="center">

# 🛡️ IncidentIQ

### AI Incident Intelligence Platform — *root cause in seconds, not hours*

**Meet ARIA** — an autonomous SRE agent that connects to your monitoring stack, reads logs and alerts in real time, pinpoints the probable root cause, and tells you exactly how to fix it.

[![Live Demo](https://img.shields.io/badge/▶_Live_Demo-Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://incidentiq-1099197368634.us-central1.run.app)
&nbsp;
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Cloud Run](https://img.shields.io/badge/Deployed_on-Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/run)

**🔗 Live:** https://incidentiq-1099197368634.us-central1.run.app

</div>

---

## 🔥 The Problem

During an outage, every minute counts — yet engineers burn the most valuable ones **manually hunting** through scattered logs, dashboards, and alerts across Datadog, Grafana, and New Relic just to answer one question: *what actually broke?*

## 💡 The Solution

**IncidentIQ** plugs directly into your monitoring tools and runs a **three-stage AI pipeline** that turns raw telemetry into an actionable diagnosis — automatically.

```
   Logs · Alerts · Metrics                 ┌─────────────────────────────┐
   ┌──────────┬──────────┬──────────┐      │   ARIA — AI Pipeline        │
   │ Datadog  │ Grafana  │ New Relic│ ───▶ │                             │
   └──────────┴──────────┴──────────┘      │  ① Groq    →  Triage        │
                                            │  ② Gemini  →  Correlation   │
                                            │  ③ OpenAI  →  Root Cause    │
                                            └──────────────┬──────────────┘
                                                           │
              ┌────────────────────────────────────────────┼───────────────┐
              ▼                        ▼                     ▼               ▼
       Probable root cause     Step-by-step fixes      Slack alert     Voice briefing
       + confidence score      + prevention plan       (Block Kit)     (ElevenLabs TTS)
```

---

## ✨ Features

| | Feature | What it does |
|---|---|---|
| 🔌 | **Native monitoring connectors** | Pulls logs, events & metrics from **Datadog**, **Grafana/Loki**, and **New Relic** via their official APIs. |
| 🧠 | **3-stage AI root-cause engine** | **Groq** triages → **Gemini** correlates the cascade → **OpenAI** delivers root cause, fix commands, and impact estimate. |
| ⚡ | **Real-time autonomous agent** | Polls providers on an interval, auto-analyzes anomalies, and broadcasts incidents over WebSocket. |
| 🎯 | **Confidence-scored diagnoses** | Every incident ships with a confidence score, evidence trail, blast radius, and timeline. |
| 🛠️ | **Instant remediation** | Concrete `fix_commands` (shell / SQL / kubectl) plus a prevention recommendation. |
| 🔔 | **Slack alerting** | Rich Block Kit incident cards posted to your channel on critical events. |
| 🎙️ | **Voice interface** | ElevenLabs TTS spoken summaries + voice-driven Q&A over the incident (Groq Whisper). |
| 🧪 | **Chaos simulator** | Three realistic failure scenarios (`db_connection_leak`, `memory_leak`, `api_cascade`) to demo the full flow end-to-end. |
| 📊 | **Live dashboard** | React UI for incidents, metrics, alerts, and runbooks — served from the same service. |

---

## 🏗️ Architecture

A single Cloud Run service hosts both the **FastAPI** backend and the **static React dashboard**.

```
incidentiq/
├── Dockerfile              # Single-image build: API + bundled UI
├── index.html              # Dashboard, incidents, metrics, alerts, runbooks
├── dashboard.html · ...    # (static, served by FastAPI at "/")
├── components/             # React components (charts, voice orb, cards)
└── backend/
    ├── main.py             # FastAPI app — all /api routes + WebSockets
    ├── models.py           # Pydantic request models
    ├── store.py            # In-memory incident store + WS manager
    └── services/
        ├── groq_service.py        # Stage 1 — triage + Whisper transcription
        ├── gemini_service.py      # Stage 2 — event correlation
        ├── openai_service.py      # Stage 3 — root cause + remediation
        ├── elevenlabs_service.py  # Text-to-speech
        ├── slack_service.py       # Block Kit incident alerts
        ├── datadog_service.py     # Datadog logs/events connector
        ├── grafana_service.py     # Grafana + Loki connector
        ├── newrelic_service.py    # New Relic NerdGraph connector
        ├── monitoring_agent.py    # Autonomous polling agent
        └── chaos_service.py       # Failure-scenario generator
```

### The AI pipeline

| Stage | Provider | Model | Job |
|:---:|---|---|---|
| **1 · Triage** | Groq | `llama-3.3-70b-versatile` | Detect anomalies, severity, affected services (sub-second) |
| **2 · Correlation** | Google Gemini | `gemini-2.5-flash` | Link events into a causal timeline + blast radius |
| **3 · Root Cause** | OpenAI | `gpt-4o-mini` | Probable root cause, fix commands, prevention, impact |

> The pipeline **degrades gracefully** — if any stage is unavailable, the others still return a useful partial diagnosis.

---

## 🚀 Quick Start (Local)

**Prerequisites:** Python 3.11+, and API keys for the providers you want to enable.

```bash
# 1. Configure environment
cd backend
cp .env.example .env        # then fill in your API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server (serves API; UI if a frontend/ dir is present)
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open the dashboard `index.html` in a browser, or hit the API directly:

```bash
curl http://127.0.0.1:8000/api/health                 # AI provider status
curl http://127.0.0.1:8000/api/integrations/status     # monitoring status
curl -X POST http://127.0.0.1:8000/api/chaos \
     -H "Content-Type: application/json" \
     -d '{"scenario":"api_cascade"}'                    # full pipeline demo
```

---

## ☁️ Deploy to Google Cloud Run

The repo ships with a production `Dockerfile` that bundles the UI + API into one container.

```bash
# Enable the required APIs (once per project)
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# Build & deploy from source (uses the root Dockerfile)
gcloud run deploy incidentiq \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --env-vars-file .deploy-env.yaml      # your secrets, NOT committed
```

> `.deploy-env.yaml` and `.env` are git-ignored. **Never commit real keys** — supply them as Cloud Run environment variables or Secret Manager references.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/api/health` | AI provider health (Groq, Gemini, OpenAI, ElevenLabs) |
| `GET`  | `/api/integrations/status` | Monitoring connector health (Datadog, Grafana, New Relic) |
| `POST` | `/api/integrations/sync` | Pull logs from providers; optionally auto-analyze |
| `POST` | `/api/ingest` | Ingest logs (raw, GCP, Datadog, or Grafana webhook formats) |
| `POST` | `/api/analyze` | Run the full 3-stage pipeline on logs |
| `GET`  | `/api/incidents` | List analyzed incidents |
| `POST` | `/api/chaos` | Generate a failure scenario and analyze it |
| `POST` | `/api/slack` | Send a Slack alert for an incident |
| `POST` | `/api/voice/speak` | Text-to-speech (ElevenLabs) |
| `WS`   | `/api/voice/listen` | Voice Q&A over an incident |
| `WS`   | `/ws/live` | Live incident stream |
| `POST` | `/api/agent/{start,stop,poll}` | Control the autonomous monitoring agent |

---

## ⚙️ Configuration

All configuration is via environment variables — see [`backend/.env.example`](backend/.env.example).

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Stage-1 triage + Whisper transcription |
| `GOOGLE_API_KEY` | Stage-2 Gemini correlation |
| `OPENAI_API_KEY` | Stage-3 root-cause analysis |
| `ELEVENLABS_API_KEY` | Voice synthesis |
| `SLACK_WEBHOOK_URL` | Slack incident alerts |
| `DATADOG_API_KEY` / `DATADOG_APP_KEY` / `DATADOG_SITE` | Datadog connector |
| `GRAFANA_URL` / `GRAFANA_API_KEY` / `GRAFANA_LOKI_URL` | Grafana + Loki connector |
| `NEW_RELIC_API_KEY` / `NEW_RELIC_ACCOUNT_ID` / `NEW_RELIC_REGION` | New Relic connector |
| `AGENT_AUTOSTART` | Auto-start the monitoring agent on boot (`true`/`false`) |

---

## 🧰 Tech Stack

**Backend:** FastAPI · Uvicorn · Pydantic · httpx · WebSockets
**AI:** Groq · Google Gemini · OpenAI · ElevenLabs
**Monitoring:** Datadog · Grafana / Loki · New Relic
**Frontend:** React 18 · Babel standalone · custom CSS
**Infra:** Docker · Google Cloud Run · Cloud Build · Artifact Registry

---

<div align="center">

**Built to give engineers their incident-response time back.** ⏱️

</div>
