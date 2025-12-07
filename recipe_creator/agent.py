"""Agent factory for Recipe Agent."""

from langchain.agents import create_agent

from config import config
from tools.web_search import web_search
from tools.youtube import get_youtube_transcript
from tools.save_recipe import save_recipe
from tools.execute_sql import execute_recipe_sql


def create_recipe_agent(model: str | None = None, system_prompt: str | None = None):
    """Create and return a configured recipe agent.

    Args:
        model: Model identifier (default from config, e.g., 'anthropic:claude-sonnet-4-5-20250929')
        system_prompt: Custom system prompt (default loaded from prompt file)

    Returns:
        Configured LangChain agent (CompiledStateGraph)
    """
    return create_agent(
        model=model or config.model,
        tools=[web_search, get_youtube_transcript, save_recipe, execute_recipe_sql],
        system_prompt=system_prompt or config.system_prompt,
    )


# Pre-compiled graph instance for LangGraph server
# langgraph.json points to this instance directly
graph = create_recipe_agent()

