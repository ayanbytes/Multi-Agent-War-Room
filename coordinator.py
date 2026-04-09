import json
import logging
import re

from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate

from app.agents.pm_agent import run_pm_agent
from app.agents.data_analyst_agent import run_data_analyst_agent
from app.agents.marketing_agent import run_marketing_agent
from app.agents.risk_agent import run_risk_agent
from app.models.output_models import FinalDecision
from app.models.state_models import WorkflowState

logger = logging.getLogger(__name__)

SYNTHESIS_PROMPT = """You are the Coordinator Agent responsible for synthesizing outputs from multiple agents into a final, structured, production-grade decision.

Your primary responsibility is to generate a CLEAN, COMPLETE, and VALID JSON output.

---

### CONTEXT

You will receive analysis from:

- Product Manager Agent
{pm_analysis}

- Data Analyst Agent
{analyst_analysis}

- Marketing/Communications Agent
{marketing_analysis}

- Risk/Critic Agent
{risk_analysis}

Each agent provides partial insights. You must consolidate them into a single, coherent decision.

---

### OUTPUT REQUIREMENTS (STRICT)

You MUST return ONLY a valid JSON object.

Do NOT include:
- Logs
- Explanations outside JSON
- Markdown formatting
- Partial or incomplete fields

The JSON must strictly follow this structure:

{{
  "decision": "PROCEED | PAUSE | ROLL_BACK",
  "rationale": [
    "Concise reason with metric or feedback reference",
    "Another key driver"
  ],
  "risk_register": [
    {{
      "risk": "Clear description of risk",
      "severity": "High | Medium | Low",
      "mitigation": "Specific mitigation action"
    }}
  ],
  "action_plan_24_48h": [
    {{
      "action": "Concrete action to be taken",
      "owner": "Responsible team or role"
    }}
  ],
  "communication_plan": {{
    "internal": "Clear internal communication guidance",
    "external": "Customer-facing communication message"
  }},
  "confidence_score": 0.0,
  "confidence_explanation": [
    "What additional data or validation would improve confidence"
  ]
}}

---

### DECISION LOGIC

- Choose "ROLL_BACK" if critical failures exist (e.g., crash spikes, payment failures, severe UX degradation)
- Choose "PAUSE" if signals are mixed or uncertain
- Choose "PROCEED" only if metrics and feedback are stable or improving

---

### QUALITY RULES

- Ensure ALL fields are present (no missing keys)
- Ensure JSON is syntactically valid
- Ensure no empty arrays unless absolutely necessary
- Ensure each rationale references actual signals (metrics or feedback)
- Ensure risks are actionable and realistic
- Ensure action plan is practical and time-bound (24–48h)

---

### FINAL CHECK BEFORE OUTPUT

Before returning:
- Validate JSON structure
- Ensure no duplicated or truncated content
- Ensure decision is explicitly stated
- Ensure clarity and conciseness

---

### OUTPUT

Return ONLY the JSON. No extra text.
"""


def run_coordinator(llm: ChatMistralAI, context: str) -> tuple[FinalDecision, WorkflowState]:
    """Orchestrate all specialist agents and synthesize their outputs into a final decision."""
    logger.info("=" * 70)
    logger.info("[COORDINATOR] Starting multi-agent decision workflow")
    logger.info("=" * 70)

    state = WorkflowState(release_context=context)

    # Step 1: Run Product Manager Agent
    logger.info("[COORDINATOR] Invoking Product Manager Agent...")
    pm_output = run_pm_agent(llm, context)
    state.add_analysis("Product Manager", "Release evaluation and success criteria", pm_output)
    logger.info("[COORDINATOR] Product Manager analysis received.")

    # Step 2: Run Data Analyst Agent
    logger.info("[COORDINATOR] Invoking Data Analyst Agent...")
    analyst_output = run_data_analyst_agent(llm, context)
    state.add_analysis("Data Analyst", "Quantitative metrics analysis", analyst_output)
    logger.info("[COORDINATOR] Data Analyst analysis received.")

    # Step 3: Run Marketing/Communications Agent
    logger.info("[COORDINATOR] Invoking Marketing/Communications Agent...")
    marketing_output = run_marketing_agent(llm, context)
    state.add_analysis("Marketing/Communications", "Feedback and messaging strategy", marketing_output)
    logger.info("[COORDINATOR] Marketing analysis received.")

    # Step 4: Run Risk/Critic Agent (receives other analyses for critical review)
    logger.info("[COORDINATOR] Invoking Risk/Critic Agent...")
    other_analyses = state.get_all_analyses_text()
    risk_output = run_risk_agent(llm, context, other_analyses)
    state.add_analysis("Risk/Critic", "Risk assessment and critical review", risk_output)
    logger.info("[COORDINATOR] Risk assessment received.")

    # Step 5: Synthesize final decision
    logger.info("[COORDINATOR] Synthesizing final decision from all agent analyses...")
    decision = _synthesize_decision(llm, pm_output, analyst_output, marketing_output, risk_output)
    logger.info(f"[COORDINATOR] Final decision: {decision.decision}")
    logger.info(f"[COORDINATOR] Confidence score: {decision.confidence_score}")

    return decision, state


def _synthesize_decision(
    llm: ChatMistralAI,
    pm_analysis: str,
    analyst_analysis: str,
    marketing_analysis: str,
    risk_analysis: str,
) -> FinalDecision:
    """Use the LLM to synthesize all agent analyses into a structured final decision."""
    prompt = ChatPromptTemplate.from_messages([
        ("human", SYNTHESIS_PROMPT),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "pm_analysis": pm_analysis,
        "analyst_analysis": analyst_analysis,
        "marketing_analysis": marketing_analysis,
        "risk_analysis": risk_analysis,
    })

    raw_text = response.content.strip()

    # Clean up potential markdown code block wrappers
    raw_text = _clean_json_response(raw_text)

    try:
        data = json.loads(raw_text)
        decision = FinalDecision(**data)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"[COORDINATOR] Failed to parse LLM JSON output: {e}")
        logger.warning("[COORDINATOR] Attempting fallback parsing...")
        decision = _fallback_decision(raw_text)

    return decision


def _clean_json_response(text: str) -> str:
    """Remove markdown code block wrappers if present."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _fallback_decision(raw_text: str) -> FinalDecision:
    """Create a fallback decision if JSON parsing fails."""
    logger.warning("[COORDINATOR] Using fallback decision structure.")
    return FinalDecision(
        decision="PAUSE",
        rationale=[
            "Auto-generated fallback. Raw coordinator output could not be parsed.",
            f"Content: {raw_text[:500]}"
        ],
        risk_register=[{
            "risk": "Decision parsing failure",
            "severity": "Medium",
            "mitigation": "Manual review of agent outputs required",
        }],
        action_plan_24_48h=[{
            "action": "Review raw agent outputs and make manual decision",
            "owner": "Engineering Lead",
        }],
        communication_plan={
            "internal": "Decision system encountered parsing issues. Manual review in progress.",
            "external": "No external communication until decision is finalized.",
        },
        confidence_score=0.3,
        confidence_explanation=["Successful re-run of the decision system", "Manual review of agent outputs"],
    )
