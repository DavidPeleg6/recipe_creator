"""Agent factory for Recipe Agent."""

from langchain.agents import create_agent

from config import config
from middlewares import hitl_middleware

from tools.recipe_storage import explore_recipes_db, save_recipe
from tools.web_search import web_search
from tools.youtube import get_youtube_transcript


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
        tools=[
            web_search,
            get_youtube_transcript,
            save_recipe,
            explore_recipes_db,
        ],
        system_prompt=system_prompt or config.system_prompt,
        # Middleware applied in reverse order; HITL runs outermost, formatting runs first.
        middleware=[hitl_middleware],
    )


# Pre-compiled graph instance for LangGraph server
# langgraph.json points to this instance directly
graph = create_recipe_agent()

