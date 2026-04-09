import logging

from langchain_mistralai import ChatMistralAI

from app.agents.agent_runner import run_specialist_agent
from app.tools.feedback_tools import feedback_summary
from app.tools.release_tools import release_notes_lookup

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Marketing and Communications Agent responsible for analyzing customer perception and messaging strategy.

Your responsibilities:
- Analyze user feedback sentiment and recurring themes
- Assess customer perception of the release
- Identify messaging risks and opportunities
- Recommend internal and external communication actions
- Highlight feedback that requires immediate response

You have access to tools for summarizing feedback and looking up release notes.
Use them to understand what customers are saying and what was released.

Provide a structured analysis covering:
1. Overall sentiment breakdown (positive, negative, neutral)
2. Top recurring themes and concerns from users
3. Customer perception assessment
4. Messaging risks (what could go wrong publicly)
5. Recommended communication actions (internal team updates, external customer messaging)
6. Any feedback requiring urgent response
"""


def run_marketing_agent(llm: ChatMistralAI, context: str) -> str:
    """Run the Marketing/Communications agent and return its analysis."""
    logger.info("=" * 60)
    logger.info("[MARKETING AGENT] Starting feedback and communications analysis...")
    logger.info("=" * 60)

    tools = [feedback_summary, release_notes_lookup]
    output = run_specialist_agent(
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        user_input=context,
        agent_name="marketing_communications",
    )

    logger.info("[MARKETING AGENT] Analysis complete.")
    return output
