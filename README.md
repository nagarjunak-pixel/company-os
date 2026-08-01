# CompanyOS 🏢 — Autonomous Company Engine

**CompanyOS** is an autonomous company operating system that runs ANY company with a team of 7 executive AI agents.

Given a single `company.json` configuration file, CompanyOS stands up a fully functioning company, generates an operating plan (mission → department goals → backlog tasks), assigns tasks to executive agent roles, tracks execution on an interactive Kanban board, streams live agent activity logs, and updates real-time financial KPIs.

---

## ⚡ Key Features

- **Generic & Configurable**: Adapt CompanyOS to SaaS, retail, manufacturing, agencies, or cafes simply by editing `company.json`.
- **7 Executive AI Agent Roster**:
  - 👑 **CEO** (Strategy & Corporate Alignment)
  - ⚙️ **COO** (Operations, Supply Chain & Workflows)
  - 📢 **CMO** (Marketing & Customer Acquisition)
  - 💼 **Head of Sales** (B2B/B2C Pipelines & Revenue)
  - 📊 **Head of Finance** (Capital Allocation & Margin Audits)
  - 🛠️ **Head of Product** (R&D, UX & Feature Roadmap)
  - 💬 **Head of Support** (CSAT, SLAs & Customer Service)
- **Dual Execution Engine (SIM & LIVE)**:
  - **SIM Mode (Default)**: Fully self-contained deterministic agent execution engine that works out-of-the-box with **zero API keys** or network dependencies.
  - **LIVE Mode**: Set `OPENROUTER_API_KEY` to connect your agents to live OpenRouter LLM endpoints (e.g. `deepseek/deepseek-v4-flash`). If key is absent or network fails, automatically falls back to SIM mode cleanly.
- **Real-Time Kanban & Financial KPIs**: Tracks revenue, expenses, net profit, profit margin %, pipeline value, and customer satisfaction (CSAT) score across execution ticks.
- **Live Event Log**: Activity feed polled in real-time (`/api/events`) showing agent decisions and status transitions.

---

## 🚀 Quickstart Guide

### 1. Requirements
- Python 3.9+
- Flask & pytest

### 2. Run Locally
```bash
# Navigate to company_os directory
cd /Users/venkataswaraswamy/company_os

# Run the app
python3 app.py
```
Open your browser and navigate to:
👉 **`http://localhost:5000`**

---

## 🎯 Pointing CompanyOS at ANY Company

Edit `company.json` in the root directory:

```json
{
  "name": "Acme SaaS Inc.",
  "industry": "B2B Cloud Analytics",
  "description": "Real-time telemetry and predictive analytics platform for mid-market engineering teams.",
  "products": ["Analytics Cloud", "Telemetry SDK", "Enterprise Alerting"],
  "target_market": "VP of Engineering & DevOps Managers",
  "team_size": 25,
  "location": "San Francisco, CA"
}
```
Then click **`🔄 Rebuild Plan`** in the dashboard UI or execute:
```bash
curl -X POST http://localhost:5000/api/rebuild
```

CompanyOS will dynamically regenerate the entire company plan, department goals, and task backlog tailored specifically to your company profile!

---

## 🔑 Running in LIVE Mode (Optional)

To enable live LLM intelligence for all 7 executive agents:

```bash
export OPENROUTER_API_KEY="your-openrouter-key"
export OPENROUTER_MODEL="deepseek/deepseek-v4-flash"  # Optional, default is deepseek/deepseek-v4-flash
python3 app.py
```

---

## 🧪 Running Unit Tests

Run the offline pytest suite to verify agent logic, plan generation, board transitions, and KPI calculations:

```bash
python3 -m pytest test_companyos.py -v
```

---

## 📁 Directory Architecture

```
company_os/
├── app.py               # Flask application & HTTP REST API endpoints
├── company.json         # Company configuration file
├── company_os/
│   ├── __init__.py
│   ├── config.py        # Config loader & defaults
│   ├── agents.py        # 7 Executive AI Agent classes (SIM + LIVE think)
│   ├── engine.py        # Plan generation, Assign loop, Board advance & KPIs
│   └── store.py         # JSON storage & append-only event logger
├── data/                # Data storage directory (plan, board, kpis, events)
├── static/
│   ├── style.css        # Dark theme dashboard styles
│   └── app.js           # Frontend interactivity & live polling
├── templates/
│   └── index.html       # Dashboard HTML template
├── test_companyos.py    # Offline unit test suite
├── requirements.txt     # Python dependencies
└── README.md
```
