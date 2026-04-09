import logging

from langchain_mistralai import ChatMistralAI

from app.agents.agent_runner import run_specialist_agent
from app.tools.metrics_tools import detect_anomalies
from app.tools.release_tools import calculate_risk_score, release_notes_lookup

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Risk and Critic Agent. Your job is to challenge assumptions, identify risks, and push for evidence-based decisions.

Your responsibilities:
- Challenge optimistic interpretations of data
- Identify risks that other agents may overlook
- Assess severity and likelihood of identified risks
- Request additional evidence where conclusions are weak
- Evaluate known issues against observed metric degradations
- Provide a risk register with mitigation recommendations

You have access to tools for calculating risk scores, detecting anomalies, and looking up release notes.
Use them to build an evidence-based risk assessment.

You will also receive analyses from other agents. Critically evaluate their conclusions.

Provide a structured analysis covering:
1. Overall risk assessment with risk score
2. Top risks ranked by severity
3. Challenges to other agents' conclusions (where applicable)
4. Gaps in evidence or analysis
5. Mitigation recommendations for each identified risk
6. Clear recommendation on whether risks are acceptable
"""


def run_risk_agent(
    llm: ChatMistralAI,
    context: str,
    other_analyses: str = "",
) -> str:
    """Run the Risk/Critic agent and return its analysis.

    Args:
        llm: The language model instance.
        context: Dashboard context and release information.
        other_analyses: Combined analyses from other agents for critical review.
    """
    logger.info("=" * 60)
    logger.info("[RISK AGENT] Starting risk assessment and critical review...")
    logger.info("=" * 60)

    tools = [calculate_risk_score, detect_anomalies, release_notes_lookup]

    # Build the full input including other agents' analyses for critical review
    full_input = context
    if other_analyses:
        full_input += (
            "\n\n## Other Agents' Analyses (for your critical review)\n"
            + other_analyses
        )

    output = run_specialist_agent(
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        user_input=full_input,
        agent_name="risk_critic",
    )

    logger.info("[RISK AGENT] Risk assessment complete.")
    return output
