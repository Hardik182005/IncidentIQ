<div align="center">

# 🛡️ IncidentIQ

### The AI SRE that finds the root cause while you're still reading the alert.

**Meet ARIA** — an autonomous Site-Reliability agent that plugs into Datadog, Grafana & New Relic, reads your live telemetry, runs a **three-model AI pipeline**, and hands you the root cause, an evidence trail, ready-to-run fix commands, a Slack alert, and a spoken briefing — in **under 15 seconds**.

<br>

[![▶ Open the Live App](https://img.shields.io/badge/▶_OPEN_THE_LIVE_APP-Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://incidentiq-1099197368634.us-central1.run.app)

### 🔗 Live: **https://incidentiq-1099197368634.us-central1.run.app**
### 💬 Watch alerts land in real time: **[Join the IncidentIQ Slack →](https://join.slack.com/t/incidentiq-world/shared_invite/zt-3yu7eu01h-cov54rryirD67XPYz97eOw)**

<br>

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-F55036?style=flat-square)](https://groq.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-8E75B2?style=flat-square&logo=googlegemini&logoColor=white)](https://ai.google.dev)
[![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-Voice-000000?style=flat-square)](https://elevenlabs.io)
[![Datadog](https://img.shields.io/badge/Datadog-LIVE-632CA6?style=flat-square&logo=datadog&logoColor=white)](https://datadoghq.com)
[![Grafana](https://img.shields.io/badge/Grafana_Loki-LIVE-F46800?style=flat-square&logo=grafana&logoColor=white)](https://grafana.com)
[![New Relic](https://img.shields.io/badge/New_Relic-LIVE-00AC69?style=flat-square&logo=newrelic&logoColor=white)](https://newrelic.com)
[![Cloud Run](https://img.shields.io/badge/Deployed-Cloud_Run-4285F4?style=flat-square&logo=googlecloud&logoColor=white)](https://cloud.google.com/run)

</div>

---

## 🎬 Demo Video

### 🔗 **[Watch the IncidentIQ Live Demo on Google Drive →](https://drive.google.com/file/d/1gGgeCSzF4UzDQD-25KYLs2xA9g57eAZE/view?usp=sharing)**

See ARIA in action: resolving simulated chaos outages, pulling live logs from Datadog, Grafana Loki & New Relic, posting deep-linked alerts to Slack, and speaking the root cause briefing in real-time.

---

## 🕹️ Try it yourself (90 seconds, no install)

1. **Open the live app →** [https://incidentiq-1099197368634.us-central1.run.app](https://incidentiq-1099197368634.us-central1.run.app)
2. **Join the Slack** (optional but worth it) → [IncidentIQ Slack](https://join.slack.com/t/incidentiq-world/shared_invite/zt-3yu7eu01h-cov54rryirD67XPYz97eOw) — so you can watch the alert land in real time.
3. **Go to the Command Center** (`Dashboard`) and hit **⚡ Trigger Chaos** — pick a scenario like `database_deadlock`.
4. **Watch ARIA work** — in ~15s you get the root cause, a real confidence score, blast radius, a causal timeline, and copy-paste fix commands. The service topology degrades live and a Slack alert fires with deep-link buttons.
5. **Click the voice orb** 🎙️ and ask *"what's the root cause?"* — ARIA briefs you out loud (try it in Hindi, Marathi, Tamil, Gujarati… too).
6. **Open the Data Room** (`/screens/integrations.html`) → click **Seed providers**, then **Pull live data** to see real records stream back from Datadog, Grafana Loki & New Relic — each tagged by source.

> Prefer the terminal? Skip the UI and hit the live API directly — see **[Judge it in 30 seconds](#️-judge-it-in-30-seconds-no-setup--hits-the-live-deployment)** below.

---

## 🎯 Problem Statement

<div style="background-color: #1e1e1e; color: white; padding: 20px; border-radius: 8px; margin: 15px 0; border: 1px solid #333;">
  <h3 style="color: white; margin-top: 0;">3. AI Incident Root Cause Analyzer for SRE Teams</h3>
  <p style="color: #e0e0e0;"><strong>Problem:</strong> During outages, engineers waste valuable time searching logs, dashboards, and alerts to identify the root cause.</p>
  <p style="color: #e0e0e0; margin-bottom: 0;"><strong>Build:</strong> An AI agent that connects with monitoring tools like Datadog, Grafana, or New Relic, analyzes logs and incidents in real-time, identifies probable root causes, and suggests fixes instantly.</p>
</div>

---

## ✅ Our Solution

**IncidentIQ** is exactly that agent — built, deployed, and running live. It turns the slowest, most stressful part of incident response into a 15-second automated flow.

| The brief asks for… | IncidentIQ delivers |
|---|---|
| **Connect with Datadog, Grafana, New Relic** | ✅ Native connectors to **all three**, via their official APIs — **verified live** (Datadog Logs intake, Grafana Loki, New Relic NerdGraph + Log API). |
| **Analyze logs & incidents in real-time** | ✅ A **3-model AI cascade** (Groq → Gemini → OpenAI) processes the live log window in seconds and streams incidents over WebSocket. |
| **Identify probable root cause** | ✅ Returns the root cause with a **real, evidence-derived confidence score**, blast radius, correlated timeline, and the exact log lines that prove it. |
| **Suggest fixes instantly** | ✅ Generates **risk-rated, copy-paste fix commands** (shell / SQL / kubectl) + a prevention plan, and one-click posts a Slack alert. |

**Plus the things that make it demo-proof:** a **Data Room** that shows real records being pulled from all three tools (tagged by source), a **voice assistant** that answers in your language (English + Hindi, Marathi, Tamil, Gujarati…), a **chaos simulator** with 5 failure scenarios, and a **runbook builder** backed by a real API.

---

## ⏱️ Judge it in 30 seconds (no setup — hits the live deployment)

```bash
# 1) Is the brain online?  (Groq · Gemini · OpenAI · ElevenLabs)
curl https://incidentiq-1099197368634.us-central1.run.app/api/health

# 2) Are all 3 monitoring tools connected live?
curl https://incidentiq-1099197368634.us-central1.run.app/api/integrations/status

# 3) Break something on purpose and watch the AI solve it end-to-end.
#    scenarios: database_deadlock | network_latency_spike | db_connection_leak | memory_leak | api_cascade
curl -X POST https://incidentiq-1099197368634.us-central1.run.app/api/chaos \
     -H "Content-Type: application/json" -d '{"scenario":"database_deadlock"}'

# 4) Pull REAL records back from Datadog + Grafana + New Relic
curl -X POST https://incidentiq-1099197368634.us-central1.run.app/api/integrations/sync \
     -H "Content-Type: application/json" -d '{"window_minutes":120,"auto_analyze":false}'
```

Step 3 returns a full incident — **severity, real confidence, probable trigger, blast radius, causal timeline, exact fix commands, prevention, and a voice summary** — and broadcasts it to every open dashboard, degrades the affected services on the **Metrics** screen, and fires a **Slack** alert with deep-link buttons.

---

## 🧠 How it works — the 3-model AI pipeline

```
   LIVE TELEMETRY INGEST                    ┌──────────────────────────────┐
   ┌──────────┬──────────┬──────────┐       │   ARIA — 3-Model AI Pipeline │
   │ Datadog  │ Grafana  │ New Relic│  ───▶  │                              │
   └──────────┴──────────┴──────────┘       │  ① Groq    →  Triage  (<2s)  │
        official APIs · real logs           │  ② Gemini  →  Correlation    │
                                            │  ③ OpenAI  →  Root Cause     │
                                            └───────────────┬──────────────┘
                                                            │
        ┌───────────────┬───────────────────┬──────────────┼───────────────┐
        ▼               ▼                    ▼              ▼               ▼
  Root cause +    Fix commands +      Live WebSocket    Slack alert     Voice briefing
  REAL confidence prevention plan     broadcast + UI    (deep links)    (ElevenLabs)
```

| Stage | Provider | Model | Job |
|:---:|---|---|---|
| **1 · Triage** | Groq | `llama-3.3-70b-versatile` | Anomalies, severity, affected services — sub-second |
| **2 · Correlation** | Google Gemini | `gemini-2.0-flash` | Link events into a causal timeline + blast radius |
| **3 · Root Cause** | OpenAI | `gpt-4o-mini` | Root cause, fix commands, prevention, impact, voice summary |

Each stage catches its own errors and feeds the next — if one provider is down, the others still return a useful partial diagnosis and **confidence drops honestly** to reflect the missing evidence.

> **The confidence score is real.** Most demos hard-code "92%". IncidentIQ computes it from actual evidence — number of corroborating log lines, whether correlation found a trigger + blast radius, root-cause specificity — so weak incidents score ~0.35 and well-evidenced ones reach 0.95+. It *moves*.

---

## 🔌 Live integrations (verified, not mocked)

All three monitoring tools are wired **bidirectionally** — IncidentIQ can **push** demo telemetry into them *and* **pull** real records back.

| Provider | Connect | Push (seed) | Pull (fetch) | Last live pull |
|---|:---:|:---:|:---:|:---:|
| **Datadog** | ✅ | ✅ Logs intake | ✅ Logs/Monitors/Events | **96 records** |
| **Grafana Loki** | ✅ | ✅ Loki push | ✅ Loki query + alerts | **19 records** |
| **New Relic** | ✅ | ✅ Log API | ✅ NerdGraph NRQL + aiIssues | **18 records** |

**🟣 The Data Room** (`/screens/integrations.html`) is the proof screen for judges: hit **Seed providers**, then **Pull live data**, and watch real records stream in — **each tagged with its source tool** — with "Open console ↗" links to show the same logs inside Datadog / Grafana / New Relic.

---

## ✨ Full feature set

| | Feature | What it does |
|---|---|---|
| 🧠 | **3-stage AI root-cause engine** | Groq triages → Gemini correlates the cascade → OpenAI delivers root cause, fixes & impact. |
| 🎯 | **Real evidence-based confidence** | Confidence is *computed* from the evidence, not echoed — it genuinely varies per incident. |
| 🔌 | **Native monitoring connectors** | Live logs, events & alerts from **Datadog**, **Grafana / Loki**, and **New Relic**. |
| 🟣 | **Data Room** | Live view of records fetched from all three tools, tagged by source, with seed + pull controls. |
| 🖥️ | **Command Center** | Live incident feed + service topology, streaming over `/ws/live`, with a one-click chaos trigger. |
| 📊 | **Live Metrics** | Per-service health degrades in real time as active incidents arrive. |
| 🧪 | **5 chaos scenarios** | `database_deadlock`, `network_latency_spike`, `db_connection_leak`, `memory_leak`, `api_cascade`. |
| 🛠️ | **Runbook builder** | Browse AI-linked runbooks **and create your own**, persisted via `/api/runbooks`. |
| 🔔 | **Slack alerts w/ deep links** | Block Kit cards whose buttons open the exact incident & the matching runbook. |
| 🎙️ | **Multilingual voice assistant** | ElevenLabs TTS + Groq Whisper; replies in your language — English default, plus Hindi, Marathi, Tamil, Telugu, Bengali, Gujarati, Punjabi, Kannada, Malayalam. |
| 🕒 | **IST clocks** | All timestamps render in India Standard Time (Asia/Kolkata). |

---

## 🏗️ Architecture

One Cloud Run container hosts both the **FastAPI** backend and the **static dashboard** — the UI is served from `/`, all `/api/*` and WebSocket routes take precedence.

```
                         ┌───────────────────────────── Google Cloud Run ─────────────────────────────┐
                         │                                                                             │
  Browser ──HTTPS──▶     │   FastAPI (main.py)                                                          │
  (dashboard, Data Room) │   ├── /                       → static UI (index + screens/ + components/)  │
        ▲                │   ├── /api/health             → provider health                            │
        │  WebSocket     │   ├── /api/chaos              → generate scenario + run pipeline            │
        └────────────────┤   ├── /api/analyze            → 3-stage pipeline on logs                    │
   /ws/live (incidents)  │   ├── /api/incidents[/{id}]   → store + single incident                     │
   /api/voice/listen     │   ├── /api/metrics            → live service health                         │
                         │   ├── /api/runbooks (GET/POST)→ runbook store                               │
                         │   ├── /api/chat               → multilingual SRE assistant                  │
                         │   ├── /api/slack              → deep-linking Block Kit alert                 │
                         │   ├── /api/integrations/seed  → push demo telemetry INTO providers          │
                         │   └── /api/integrations/sync  → pull real logs FROM providers               │
                         │                                                                             │
                         │   services/  groq · gemini · openai · elevenlabs · slack ·                  │
                         │              datadog · grafana · newrelic · monitoring_agent · chaos        │
                         └─────────────────────────────────────────────────────────────────────────────┘
                                 │              │               │
                                 ▼              ▼               ▼
                             Datadog        Grafana Loki     New Relic        ◀── live, bidirectional
```

### Repository layout

```
incidentiq/
├── Dockerfile              # Single image: FastAPI API + bundled UI
├── index.html              # Landing page (live topology + ingest bar + seed button)
├── screens/
│   ├── dashboard.html      # Command Center — live feed, topology, incident detail, voice orb
│   ├── incidents.html      # Incident history table (live + deep-linkable)
│   ├── metrics.html        # Live per-service telemetry
│   ├── alerts.html         # Alert rules + notification channels (Join-Slack link)
│   ├── runbooks.html       # Runbook library + "New Runbook" builder
│   └── integrations.html   # 🟣 Data Room — live ingest proof
├── components/             # React components (charts, topology, incident cards, voice orb)
└── backend/
    ├── main.py             # FastAPI app — all routes + WebSockets
    ├── models.py           # Pydantic request models
    ├── store.py            # In-memory incident store, runbook store, WS manager
    └── services/
        ├── groq_service.py        # Stage 1 — triage + Whisper transcription
        ├── gemini_service.py      # Stage 2 — event correlation
        ├── openai_service.py      # Stage 3 — root cause + real confidence + multilingual chat
        ├── elevenlabs_service.py  # Multilingual text-to-speech
        ├── slack_service.py       # Deep-linking Block Kit alerts
        ├── datadog_service.py     # Datadog logs/monitors/events + push
        ├── grafana_service.py     # Grafana alerts + Loki query/push
        ├── newrelic_service.py    # New Relic NerdGraph + Log API push
        ├── monitoring_agent.py    # Autonomous polling agent
        └── chaos_service.py       # 5 failure-scenario generators
```

---

## 🚀 Quick start (local)

**Prerequisites:** Python 3.11+, plus API keys for whichever providers you enable.

```bash
cd backend
cp .env.example .env                 # fill in your API keys
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open `index.html` in a browser, or hit the API directly (see Quick demo above).

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
| `POST` | `/api/integrations/seed` | Push demo telemetry **into** Datadog/Grafana/New Relic |
| `POST` | `/api/integrations/sync` | Pull real logs **from** providers; returns records (+ optional auto-analyze) |
| `POST` | `/api/ingest` | Ingest logs (raw, GCP, Datadog, or Grafana webhook formats) |
| `POST` | `/api/analyze` | Run the full 3-stage pipeline on logs |
| `POST` | `/api/chaos` | Generate a failure scenario and analyze it end-to-end |
| `GET`  | `/api/incidents` | List analyzed incidents |
| `GET`  | `/api/incidents/{id}` | Fetch one incident (used by Slack "View Dashboard" deep link) |
| `GET`  | `/api/metrics` | Live per-service health (degrades with active incidents) |
| `GET`/`POST` | `/api/runbooks` | List / create runbooks |
| `POST` | `/api/slack` | Send a deep-linking Slack alert for an incident |
| `POST` | `/api/chat` | Multilingual conversational SRE assistant, grounded in an incident |
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
| `OPENAI_API_KEY` | Stage-3 root-cause + multilingual chat |
| `ELEVENLABS_API_KEY` | Voice synthesis |
| `SLACK_WEBHOOK_URL` | Slack incident alerts |
| `FRONTEND_URL` | Base URL used for Slack deep links |
| `DATADOG_API_KEY` · `DATADOG_APP_KEY` · `DATADOG_SITE` | Datadog connector (logs intake works with the API key) |
| `GRAFANA_URL` · `GRAFANA_API_KEY` · `GRAFANA_LOKI_URL` | Grafana + Loki connector |
| `GRAFANA_LOKI_USER` · `GRAFANA_LOKI_TOKEN` | Grafana Cloud Loki basic-auth (instance id + `logs:read/write` token) |
| `NEW_RELIC_API_KEY` · `NEW_RELIC_ACCOUNT_ID` · `NEW_RELIC_REGION` | New Relic NerdGraph (user key) |
| `NEW_RELIC_LICENSE_KEY` | New Relic Log API ingest (license key) |
| `AGENT_AUTOSTART` | Auto-start the monitoring agent on boot (`true`/`false`) |

---

## 🧰 Tech stack

**Backend:** FastAPI · Uvicorn · Pydantic · httpx · WebSockets
**AI:** Groq (`llama-3.3-70b`) · Google Gemini (`2.0-flash`) · OpenAI (`gpt-4o-mini`) · ElevenLabs (`eleven_turbo_v2_5`) · Groq Whisper
**Monitoring:** Datadog · Grafana / Loki · New Relic
**Frontend:** React 18 · Babel standalone · canvas visualizations · custom CSS
**Infra:** Docker · Google Cloud Run · Cloud Build · Artifact Registry

---

<div align="center">

### ▶ Try it now: **https://incidentiq-1099197368634.us-central1.run.app**
### 💬 [Join the Slack](https://join.slack.com/t/incidentiq-world/shared_invite/zt-3yu7eu01h-cov54rryirD67XPYz97eOw) to watch live incident alerts land.

**Built to give engineers their incident-response time back.** ⏱️

</div>
