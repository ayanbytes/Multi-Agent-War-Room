import logging

from langchain_mistralai import ChatMistralAI

from app.agents.agent_runner import run_specialist_agent
from app.tools.metrics_tools import aggregate_metrics
from app.tools.release_tools import release_notes_lookup

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Product Manager Agent responsible for evaluating a product release.

Your responsibilities:
- Define release success criteria based on business goals
- Assess user impact from metrics and release context
- Frame the go/no-go decision from a product perspective
- Identify which metrics matter most for this release

You have access to tools to look up release notes and aggregate metrics.
Use them to gather data before forming your assessment.

Provide a structured analysis covering:
1. Release objectives and what success looks like
2. Key metrics that indicate success or failure
3. User impact assessment
4. Product recommendation (proceed, pause, or roll back) with reasoning
"""


def run_pm_agent(llm: ChatMistralAI, context: str) -> str:
    """Run the Product Manager agent and return its analysis."""
    logger.info("=" * 60)
    logger.info("[PM AGENT] Starting Product Manager analysis...")
    logger.info("=" * 60)

    tools = [release_notes_lookup, aggregate_metrics]
    output = run_specialist_agent(
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        user_input=context,
        agent_name="product_manager",
    )

    logger.info("[PM AGENT] Analysis complete.")
    return output
