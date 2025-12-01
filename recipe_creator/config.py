"""Configuration management for Recipe Agent."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()


class Config(BaseModel):
    """Configuration for the recipe agent using Pydantic."""

    # Model selection (supports both Anthropic and OpenAI)
    model: str = Field(
        default_factory=lambda: os.getenv("RECIPE_AGENT_MODEL")
    )

    # Prompt file path (not the prompt content!)
    prompt_file: Path = Field(
        default_factory=lambda: Path(os.getenv("RECIPE_AGENT_PROMPT_FILE", "prompts/default_prompt.txt"))
    )

    # API Keys
    anthropic_api_key: str | None = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
    openai_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    tavily_api_key: str | None = Field(
        default_factory=lambda: os.getenv("TAVILY_API_KEY")
    )

    # LangSmith (optional)
    langsmith_api_key: str | None = Field(
        default_factory=lambda: os.getenv("LANGSMITH_API_KEY")
    )
    langsmith_project: str = Field(
        default_factory=lambda: os.getenv("LANGSMITH_PROJECT", "recipe-agent")
    )

    @property
    def system_prompt(self) -> str:
        """Load system prompt from file."""
        return self.prompt_file.read_text().strip()


# Global config instance
config = Config()

