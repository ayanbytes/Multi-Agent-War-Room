# Multi-Agent-War-Room
# Multi-Agent War Room Decision System

A production-style multi-agent system that simulates a cross-functional **“War Room”** during a product launch to determine whether to **Proceed, Pause, or Roll Back** a release.

---

##  Overview

This system models real-world decision-making by orchestrating multiple specialized AI agents:

* **Product Manager Agent** — Defines success criteria and business impact
* **Data Analyst Agent** — Analyzes metrics, trends, and anomalies
* **Marketing/Communications Agent** — Evaluates user feedback and sentiment
* **Risk/Critic Agent** — Identifies risks and challenges assumptions
* **Coordinator Agent** — Synthesizes insights into a final decision

---

## Key Features

*  Multi-agent orchestration with clear role separation
*  Tool-driven analysis (metrics aggregation, anomaly detection, sentiment analysis)
*  Realistic mock dashboard (metrics + feedback + release notes)
*  Structured decision output (JSON)
*  End-to-end traceability via logs

---

## 🛠️ Tools Used

* `aggregate_metrics` — KPI aggregation
* `detect_anomalies` — anomaly detection
* `feedback_summary` — sentiment + themes extraction
* `release_notes_lookup` — release context
* `calculate_risk_score` — risk evaluation

---

##  Example Final Output

```json
{
  "decision": "ROLL_BACK",
  "confidence_score": 0.85,
  "rationale": ["Crash rate +177%", "Payment failures impacting revenue"],
  "risk_register": [...],
  "action_plan_24_48h": [...],
  "communication_plan": {...}
}
```

---

##  Setup Instructions

```bash
# Clone repo
git clone https://github.com/your-username/purplemerit-war-room.git

# Navigate to project
cd purplemerit-war-room

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

---

##  Run the System

```bash
python -m app.main
```

---

##  Output

Final decision is saved at:

```
outputs/final_decision.json
```

---

##  Environment Variables

Create a `.env` file:

```
LLM_API_KEY=your_api_key_here
```

---

##  System Design

The system uses a **Coordinator-based orchestration pattern**, where each agent contributes domain-specific insights and the final decision is synthesized into a structured output.

---
