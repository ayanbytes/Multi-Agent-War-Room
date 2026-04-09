import logging

from langchain_mistralai import ChatMistralAI

from app.agents.agent_runner import run_specialist_agent
from app.tools.metrics_tools import aggregate_metrics, detect_anomalies

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Data Analyst Agent responsible for quantitative analysis of release metrics.

Your responsibilities:
- Analyze pre-release vs post-release metric trends
- Detect anomalies, spikes, or drops in key metrics
- Assess statistical confidence in observed changes
- Identify correlations between metric movements
- Distinguish signal from noise in the data

You have access to tools for aggregating metrics and detecting anomalies.
Use both tools to build a comprehensive data picture.

Provide a structured analysis covering:
1. Summary of all metric movements (improved vs degraded)
2. Anomalies detected with severity assessment
3. Metrics of highest concern
4. Metrics showing clear improvement
5. Confidence level in the data (considering sample size of 7 days)
6. Data-driven recommendation
"""


def run_data_analyst_agent(llm: ChatMistralAI, context: str) -> str:
    """Run the Data Analyst agent and return its analysis."""
    logger.info("=" * 60)
    logger.info("[DATA ANALYST] Starting quantitative analysis...")
    logger.info("=" * 60)

    tools = [aggregate_metrics, detect_anomalies]
    output = run_specialist_agent(
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        user_input=context,
        agent_name="data_analyst",
    )

    logger.info("[DATA ANALYST] Analysis complete.")
    return output
