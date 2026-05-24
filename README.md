<div align="center">

# 🛡️ IncidentIQ

### The AI SRE that finds the root cause while you're still reading the alert.

**Meet ARIA** — an autonomous Site-Reliability agent that plugs into Datadog, Grafana & New Relic, reads your live telemetry, runs a **three-model AI pipeline**, and hands you the root cause, an evidence trail, ready-to-run fix commands, a Slack alert, and a spoken briefing — in **under 15 seconds**.

<br>

[![▶ Open the Live App](https://img.shields.io/badge/▶_OPEN_THE_LIVE_APP-Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://incidentiq-1099197368634.us-central1.run.app)

### 🔗 Live: **https://incidentiq-1099197368634.us-central1.run.app**

<br>

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-F55036?style=flat-square)](https://groq.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-8E75B2?style=flat-square&logo=googlegemini&logoColor=white)](https://ai.google.dev)
[![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Voice-000000?style=flat-square)](https://elevenlabs.io)
[![Cloud Run](https://img.shields.io/badge/Deployed-Cloud_Run-4285F4?style=flat-square&logo=googlecloud&logoColor=white)](https://cloud.google.com/run)

</div>

---

## ⏱️ Judge it in 30 seconds (no setup — hits the live deployment)

```bash
# 1) Is the brain online?  (Groq · Gemini · OpenAI · ElevenLabs)
curl https://incidentiq-1099197368634.us-central1.run.app/api/health

# 2) Break something on purpose and watch the AI solve it end-to-end.
#    Try any of 5 scenarios: database_deadlock | network_latency_spike |
#    db_connection_leak | memory_leak | api_cascade
curl -X POST https://incidentiq-1099197368634.us-central1.run.app/api/chaos \
     -H "Content-Type: application/json" \
     -d '{"scenario":"database_deadlock"}'
```

You get back a full incident: **severity, a real confidence score, the probable trigger, blast radius, a causal timeline, exact fix commands, a prevention plan, and a voice summary** — and the same incident is broadcast live over WebSocket to every open dashboard, degrades the affected services on the **Metrics** screen, and fires a **Slack** alert with deep-link buttons.

Then open the app → click **⚡ Trigger Incident** in the Command Center and watch it happen in the UI.

---

## 🔥 The problem

During an outage every minute is on fire — and engineers burn the most expensive ones **manually hunting** through logs, dashboards and alerts spread across Datadog, Grafana and New Relic, just to answer one question: *what actually broke?*

## 💡 The solution

IncidentIQ connects to all three monitoring stacks, then runs a **cascading three-stage AI pipeline** that turns raw telemetry into an actionable diagnosis — automatically, in seconds.

```
   LIVE TELEMETRY INGEST                    ┌──────────────────────────────┐
   ┌──────────┬──────────┬──────────┐       │   ARIA — 3-Model AI Pipeline │
   │ Datadog  │ Grafana  │ New Relic│  ───▶  │                              │
   └──────────┴──────────┴──────────┘       │  ① Groq    →  Triage  (<2s)  │
        official APIs, real logs            │  ② Gemini  →  Correlation    │
                                            │  ③ OpenAI  →  Root Cause     │
                                            └───────────────┬──────────────┘
                                                            │
        ┌───────────────┬───────────────────┬──────────────┼───────────────┐
        ▼               ▼                    ▼              ▼               ▼
  Root cause +    Fix commands +      Live WebSocket    Slack alert     Voice briefing
  REAL confidence prevention plan     broadcast + UI    (deep links)    (ElevenLabs)
```

---

## 🏆 Why this one is different

- **The confidence score is real.** Most demos hardcode "92%". IncidentIQ computes it from actual evidence — number of corroborating log lines, whether the correlation stage found a trigger and blast radius, root-cause specificity — so weak incidents honestly score ~0.35 and well-evidenced ones reach 0.95+. It *moves*.
- **It runs on real monitoring data.** Not mock JSON — live Datadog logs, Grafana Loki queries and New Relic NerdGraph, pulled through their official APIs.
- **It's stress-tested like production.** We fired 5 simulated companies × 5 failure modes in parallel at the live Cloud Run service; the pipeline held, incidents streamed over WebSocket, and the Metrics screen degraded the right services live.
- **Slack actually deep-links back.** "View Dashboard" opens the *exact* incident (`?incident=…`); "Open Runbook" jumps straight to the matching procedure for that scenario.
- **It talks.** Spoken root-cause briefings and voice-driven Q&A over the current incident.

---

## ✨ Features

| | Feature | What it does |
|---|---|---|
| 🔌 | **Native monitoring connectors** | Live logs, events & metrics from **Datadog**, **Grafana / Loki**, and **New Relic** via official APIs. |
| 🧠 | **3-stage AI root-cause engine** | **Groq** triages → **Gemini** correlates the cascade → **OpenAI** delivers root cause, fixes, and impact. |
| 🎯 | **Real evidence-based confidence** | Confidence is *computed* from the evidence, not echoed — it genuinely varies per incident. |
| ⚡ | **Autonomous agent** | Polls providers on an interval, auto-analyzes anomalies, broadcasts incidents over WebSocket. |
| 🖥️ | **The Command Center** | Live incident feed + service topology, real-time over `/ws/live`, with a one-click chaos trigger. |
| 📊 | **Live metrics** | Service health degrades in real time as active incidents come in — driven by `/api/metrics`. |
| 🧪 | **5 chaos scenarios** | `database_deadlock`, `network_latency_spike`, `db_connection_leak`, `memory_leak`, `api_cascade`. |
| 🛠️ | **Runbook builder** | Browse AI-linked runbooks **and create your own** — persisted to the backend via `/api/runbooks`. |
| 🔔 | **Slack alerting w/ deep links** | Block Kit cards whose buttons route back to the exact incident & matching runbook. |
| 🎙️ | **Voice interface** | ElevenLabs TTS briefings + Groq Whisper voice Q&A over the incident. |
| 🕒 | **IST clocks** | All timestamps render in India Standard Time (Asia/Kolkata). |

---

## 🏗️ Architecture

One Cloud Run service hosts both the **FastAPI** backend and the **static React dashboard**.

```
incidentiq/
├── Dockerfile              # Single image: API + bundled UI (served at "/")
├── index.html              # Landing page (live topology + ingest bar)
├── screens/                # Command Center, Incidents, Metrics, Alerts, Runbooks
├── components/             # React components (charts, topology, voice orb, cards)
└── backend/
    ├── main.py             # FastAPI — all /api routes + WebSockets
    ├── models.py           # Pydantic request models
    ├── store.py            # In-memory incident store, runbook store, WS manager
    └── services/
        ├── groq_service.py        # Stage 1 — triage + Whisper transcription
        ├── gemini_service.py      # Stage 2 — event correlation
        ├── openai_service.py      # Stage 3 — root cause + real confidence
        ├── elevenlabs_service.py  # Text-to-speech
        ├── slack_service.py       # Block Kit alerts w/ deep-link buttons
        ├── datadog_service.py     # Datadog logs/events connector
        ├── grafana_service.py     # Grafana + Loki connector
        ├── newrelic_service.py    # New Relic NerdGraph connector
        ├── monitoring_agent.py    # Autonomous polling agent
        └── chaos_service.py       # 5 failure-scenario generators
```

### The AI pipeline

| Stage | Provider | Model | Job |
|:---:|---|---|---|
| **1 · Triage** | Groq | `llama-3.3-70b-versatile` | Anomalies, severity, affected services — sub-second |
| **2 · Correlation** | Google Gemini | `gemini-2.0-flash` | Link events into a causal timeline + blast radius |
| **3 · Root Cause** | OpenAI | `gpt-4o-mini` | Root cause, fix commands, prevention, impact, voice summary |

> The pipeline **degrades gracefully** — if any stage is unavailable the others still return a useful partial diagnosis, and confidence drops accordingly.

---

## 🚀 Quick start (local)

**Prerequisites:** Python 3.11+, plus API keys for whichever providers you enable.

```bash
cd backend
cp .env.example .env                 # fill in your API keys
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open `index.html` in a browser, or hit the API:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/integrations/status
curl -X POST http://127.0.0.1:8000/api/chaos -H "Content-Type: application/json" -d '{"scenario":"api_cascade"}'
```

---

## ☁️ Deploy to Google Cloud Run

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

gcloud run deploy incidentiq \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --env-vars-file .deploy-env.yaml      # your secrets — NOT committed
```

> `.deploy-env.yaml` and `.env` are git-ignored. **Never commit real keys.**

---

## 📡 API reference

| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/api/health` | AI provider health (Groq, Gemini, OpenAI, ElevenLabs) |
| `GET`  | `/api/integrations/status` | Monitoring connector health (Datadog, Grafana, New Relic) |
| `POST` | `/api/integrations/sync` | Pull live logs from providers; optionally auto-analyze |
| `POST` | `/api/ingest` | Ingest logs (raw, GCP, Datadog, or Grafana webhook formats) |
| `POST` | `/api/analyze` | Run the full 3-stage pipeline on logs |
| `GET`  | `/api/incidents` | List analyzed incidents |
| `GET`  | `/api/metrics` | Live per-service health (degrades with active incidents) |
| `POST` | `/api/chaos` | Generate a failure scenario and analyze it end-to-end |
| `GET`  | `/api/runbooks` | List runbooks (defaults + user-created) |
| `POST` | `/api/runbooks` | Create a new runbook |
| `POST` | `/api/slack` | Send a deep-linking Slack alert for an incident |
| `POST` | `/api/chat` | Conversational SRE assistant, grounded in an incident |
| `POST` | `/api/voice/speak` | Text-to-speech (ElevenLabs) |
| `WS`   | `/api/voice/listen` | Voice Q&A over an incident |
| `WS`   | `/ws/live` | Live incident stream |
| `POST` | `/api/agent/{start,stop,poll}` | Control the autonomous monitoring agent |

---

## ⚙️ Configuration

All config is via environment variables — see [`backend/.env.example`](backend/.env.example).

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Stage-1 triage + Whisper transcription |
| `GOOGLE_API_KEY` | Stage-2 Gemini correlation |
| `OPENAI_API_KEY` | Stage-3 root-cause analysis |
| `ELEVENLABS_API_KEY` | Voice synthesis |
| `SLACK_WEBHOOK_URL` | Slack incident alerts |
| `FRONTEND_URL` | Base URL used for Slack deep links |
| `DATADOG_API_KEY` · `DATADOG_APP_KEY` · `DATADOG_SITE` | Datadog connector |
| `GRAFANA_URL` · `GRAFANA_API_KEY` · `GRAFANA_LOKI_URL` | Grafana + Loki connector |
| `NEW_RELIC_API_KEY` · `NEW_RELIC_ACCOUNT_ID` · `NEW_RELIC_REGION` | New Relic connector |
| `AGENT_AUTOSTART` | Auto-start the monitoring agent on boot (`true`/`false`) |

---

## 🧰 Tech stack

**Backend:** FastAPI · Uvicorn · Pydantic · httpx · WebSockets
**AI:** Groq · Google Gemini · OpenAI · ElevenLabs · Groq Whisper
**Monitoring:** Datadog · Grafana / Loki · New Relic
**Frontend:** React 18 · Babel standalone · canvas viz · custom CSS
**Infra:** Docker · Google Cloud Run · Cloud Build · Artifact Registry

---

<div align="center">

### ▶ Try it now: **https://incidentiq-1099197368634.us-central1.run.app**

**Built to give engineers their incident-response time back.** ⏱️

</div>
