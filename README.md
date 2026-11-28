# CompanyOS — Config-Driven Multi-Agent Operations Runtime

[![CompanyOS CI](https://github.com/nagarjunak-pixel/company-os/actions/workflows/ci.yml/badge.svg)](https://github.com/nagarjunak-pixel/company-os/actions/workflows/ci.yml)
[![Release v1.1.0](https://img.shields.io/badge/release-v1.1.0-1f6feb.svg)](https://github.com/nagarjunak-pixel/company-os/releases/tag/v1.1.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-10b981.svg)](LICENSE)

**CompanyOS** is a lightweight Python and Flask runtime that models multi-department operational planning, task delegation, Kanban execution, SHACL shape-bounded 3-way knowledge merges, and financial KPI tracking across seven role-scoped agents configured via a single `company.json` manifest.

Given a `company.json` profile, CompanyOS generates a structured operating plan (objectives → department goals → task backlog), assigns work items to role-specific agents, advances execution ticks on a web Kanban dashboard, records append-only activity events, and updates operational metrics.

---

## Key Capabilities

- **Declarative Configuration (`company.json`)**: Define organization domain, product lines, team size, and target market without modifying application code.
- **Role-Scoped Agent Roster**:
  - **CEO** — Strategic objectives and cross-department alignment
  - **COO** — Workflow sequencing and operational throughput
  - **CMO** — Demand generation and positioning tasks
  - **Head of Sales** — Pipeline progression and conversion tracking
  - **Head of Finance** — Budget allocation, expense tracking, and margin review
  - **Head of Product** — Feature prioritization and release backlog
  - **Head of Support** — Ticket resolution and customer satisfaction (CSAT)
- **Simulation & Live LLM Modes**:
  - **SIM Mode (Default)**: Deterministic offline execution engine requiring zero external API keys or network calls.
  - **LIVE Mode**: Connects role agents to OpenRouter-compatible chat endpoints when `OPENROUTER_API_KEY` is set, with automatic fallback to `SIM` mode if offline.
- **Kanban Dashboard & Event Log**: Interactive board and `/api/events` telemetry stream tracking task state transitions, revenue, expenses, net margin, pipeline value, and CSAT.

---

## Quickstart

### 1. Requirements
- Python 3.9+
- Flask & pytest (`pip install -r requirements.txt`)

### 2. Run Locally
```bash
git clone https://github.com/nagarjunak-pixel/company-os.git
cd company-os
python3 app.py
```
Open `http://localhost:5000` in your browser.

---

## Configuring `company.json`

Edit `company.json` in the repository root:

```json
{
  "name": "Acme SaaS Inc.",
  "industry": "B2B Cloud Analytics",
  "description": "Real-time telemetry and analytics platform for engineering teams.",
  "products": ["Analytics Cloud", "Telemetry SDK", "Enterprise Alerting"],
  "target_market": "VP of Engineering & DevOps Teams",
  "team_size": 25,
  "location": "Remote"
}
```
Trigger a plan rebuild from the UI or via HTTP:
```bash
curl -X POST http://localhost:5000/api/rebuild
```

### Live LLM Mode (Optional)
```bash
export OPENROUTER_API_KEY="your-openrouter-key"
export OPENROUTER_MODEL="deepseek/deepseek-chat"
python3 app.py
```

### Running Tests
```bash
python3 -m pytest test_companyos.py -v
```

---

## v1.1.0 — SHACL 3-Way Knowledge-Graph Merge & OKF Procedure Memory (`company_os/shacl_procedure_merge.py`)

- **SHACL Shape-Bounded 3-Way Merge (`shacl_three_way_merge`, `POST /api/merge-graph`, `arXiv:2611.34870`):** Canonicalizes entity aliases across concurrent multi-agent graph branches, auto-merges multi-valued set additions and removals without human prompts, and escalates only true functional/cardinality violations (`max_count` / `min_count`).
- **OKF Procedure Memory Distillation (`distill_procedure_memory`, `POST /api/procedures/distill`, `arXiv:2611.34576`):** Compresses verbose multi-turn episodic agent logs into deduplicated reusable runbook steps (`>=90%` token reduction) while dropping reverted attempts and preserving guard invariants.

## Directory Layout

```text
company-os/
├── app.py               # Flask application & REST endpoints
├── company.json         # Declarative organization profile
├── company_os/
│   ├── config.py        # Schema loader & defaults
│   ├── agents.py        # 7 role-scoped agent implementations (SIM + LIVE)
│   ├── engine.py        # Plan builder, task scheduler & KPI evaluator
│   └── store.py         # JSON state persistence & append-only event log
├── static/              # Frontend styles & live polling client
├── templates/           # Kanban & KPI HTML view
└── test_companyos.py    # Offline unit test suite
```

---

## Author

Built by **[Nagarjuna Reddy Kamireddy](https://nagarjunak-pixel.github.io/)** (*Nagarjuna Kamireddy / Nagarjuna K*) — Lead AI Architect | AI Solutions Architect | GenAI Lead — Agentic AI & RAG (22 years across enterprise data, SAP BW / BPC / HANA, and production AI; AWS Certified Solutions Architect – Professional & NVIDIA-Certified Professional: Agentic AI).

- **Portfolio & Case Studies:** [https://nagarjunak-pixel.github.io/](https://nagarjunak-pixel.github.io/)
- **Executive Resume:** [https://nagarjunak-pixel.github.io/resume.html](https://nagarjunak-pixel.github.io/resume.html)
- **GitHub:** [https://github.com/nagarjunak-pixel](https://github.com/nagarjunak-pixel) · **LinkedIn:** [https://www.linkedin.com/in/nagarjuna-kamireddy](https://www.linkedin.com/in/nagarjuna-kamireddy)
