# Research: Recipe Agent Backend

**Feature**: 1-recipe-agent-backend  
**Date**: December 1, 2025  

## Executive Summary

This document captures research findings for implementing the Recipe Agent Backend using LangChain 1.0.

---

## 1. LangChain 1.0 Agent Architecture

### Decision: Use `create_agent` from `langchain.agents`

**Rationale**: LangChain 1.0 introduces `create_agent` as the standard method for building agents, replacing the deprecated `create_react_agent`. This provides a simplified interface for integrating language models with tools.

**Key API Pattern**:

```python
from langchain.agents import create_agent

agent = create_agent(
    model="anthropic:claude-sonnet-4-5-20250929",  # Model identifier
    tools=[tool1, tool2],                           # List of tool functions
    system_prompt="Your system prompt here",        # Agent persona
)

# Invoke the agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "User message"}]
})
```

**Key Features**:
- Simplified agent loop: model selects tools, executes them, halts on completion
- Middleware support for customizing behavior at various execution stages
- Tools are plain Python functions with docstrings

**Alternatives Considered**:
- `create_react_agent` - Deprecated in LangChain 1.0
- LangGraph custom agents - Out of scope for this phase

**Reference**: https://reference.langchain.com/python/langchain/langchain/

---

## 2. Language Model Integration

### Decision: Support both Anthropic and OpenAI, Claude as default

**Rationale**: Supporting multiple providers gives flexibility. Both `langchain-anthropic` and `langchain-openai` packages provide integrations.

**Model String Format**:
- Anthropic: `"anthropic:claude-sonnet-4-5-20250929"`
- OpenAI: `"openai:gpt-4o"` or `"openai:gpt-4o-mini"`

**Required Packages**:
```
langchain-anthropic   # For Claude models
langchain-openai      # For GPT models
```

**Configuration Approach**:
- Store model string in config
- Allow switching via environment variable
- Default: `anthropic:claude-sonnet-4-5-20250929`

**Required Environment Variables**:
- `ANTHROPIC_API_KEY` - For Claude models
- `OPENAI_API_KEY` - For OpenAI models

**Alternatives Considered**:
- Hardcoded model - Less flexible
- Model factory pattern - Over-engineered for personal use

**Reference**: https://docs.langchain.com/oss/python/integrations/llms/openai

---

## 3. Web Search Tool

### Decision: Custom tool using Tavily API

**Rationale**: Tavily is designed specifically for AI agents and provides clean, structured search results. It's well-integrated with LangChain ecosystem.

**Implementation Pattern**:

```python
from tavily import TavilyClient

def web_search(query: str) -> str:
    """Search the web for information about recipes, ingredients, or cooking techniques.
    
    Args:
        query: The search query string
        
    Returns:
        Relevant search results as formatted text
    """
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(query, max_results=5)
    # Format and return results
    return format_search_results(response)
```

**Required Environment Variables**:
- `TAVILY_API_KEY`

**Alternatives Considered**:
- DuckDuckGo Search - Free but less reliable, rate limited
- SerpAPI - More expensive, broader coverage
- Custom scraping - Complex, maintenance burden

---

## 4. YouTube Transcript Tool

### Decision: Use `youtube-transcript-api` Python library

**Rationale**: Simple, well-maintained library that retrieves transcripts from YouTube videos without requiring API keys. Supports auto-generated captions.

**Implementation Pattern**:

```python
from youtube_transcript_api import YouTubeTranscriptApi

def get_youtube_transcript(video_url: str) -> str:
    """Get the transcript from a YouTube video.
    
    Args:
        video_url: Full YouTube video URL or video ID
        
    Returns:
        Complete transcript text from the video
    """
    video_id = extract_video_id(video_url)
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([entry["text"] for entry in transcript])
```

**Features**:
- No API key required
- Supports auto-generated captions
- Handles multiple languages (English priority)

**Alternatives Considered**:
- YouTube Data API - Requires OAuth, more complex setup
- yt-dlp - Overkill for just transcripts

---

## 5. LangSmith Observability

### Decision: Environment variable configuration for LangSmith tracing

**Rationale**: LangSmith provides automatic tracing when environment variables are set. No code changes needed beyond configuration.

**Configuration**:

```bash
export LANGSMITH_API_KEY="your-api-key"
export LANGSMITH_PROJECT="recipe-agent"
export LANGSMITH_TRACING="true"
```

**What Gets Traced**:
- All agent invocations
- Tool calls and results
- Model inputs/outputs
- Latency metrics

**Alternatives Considered**:
- Custom logging - Less powerful, manual effort
- OpenTelemetry - More complex setup
- No observability - Harder to debug

---

## 6. Configuration Management

### Decision: Environment variables + file-based prompts

**Rationale**: API keys in .env, prompts in separate files for easier editing and version control.

**Configuration Module Structure**:

```python
# config.py
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class Config(BaseModel):
    model: str = Field(
        default_factory=lambda: os.getenv("RECIPE_AGENT_MODEL", "anthropic:claude-sonnet-4-5-20250929")
    )
    prompt_file: Path = Field(
        default_factory=lambda: Path(os.getenv("RECIPE_AGENT_PROMPT_FILE", "prompts/default.txt"))
    )
    anthropic_api_key: str | None = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    openai_api_key: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    tavily_api_key: str | None = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    
    @property
    def system_prompt(self) -> str:
        return self.prompt_file.read_text().strip()
```

**Prompt File Structure**:
```
prompts/
├── default.txt          # Default recipe assistant prompt
├── healthy.txt          # Health-focused variant
└── cocktail_expert.txt  # Mixology specialist variant
```

**Environment Variables** (.env):
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
RECIPE_AGENT_MODEL=anthropic:claude-sonnet-4-5-20250929
RECIPE_AGENT_PROMPT_FILE=prompts/default.txt
```

**Alternatives Considered**:
- Prompt in .env - Hard to edit multiline text
- YAML config - Overkill
- Hardcoded prompts - Less flexible

---

## 7. Interactive CLI

### Decision: Simple input loop with rich formatting

**Rationale**: Provides good UX for personal use without complexity. The `rich` library provides nice terminal formatting.

**Implementation Pattern**:

```python
from rich.console import Console
from rich.markdown import Markdown

console = Console()

def main():
    console.print("[bold green]Recipe Agent Ready![/]")
    console.print("Type 'quit' or 'exit' to stop.\n")
    
    messages = []
    while True:
        user_input = console.input("[bold blue]You:[/] ")
        if user_input.lower() in ("quit", "exit"):
            break
        
        messages.append({"role": "user", "content": user_input})
        result = agent.invoke({"messages": messages})
        
        # Extract and display response
        response = result["messages"][-1]["content"]
        console.print(Markdown(response))
```

**Alternatives Considered**:
- Plain print/input - Less visually appealing
- prompt_toolkit - Over-engineered for this use case
- Click CLI - Good but unnecessary complexity

---

## 8. Project Structure

### Decision: Flat module structure

**Rationale**: Simple, easy to navigate for a personal project.

```
recipe_creator/
├── main.py              # Entry point with CLI loop
├── agent.py             # Agent creation and configuration
├── tools/
│   ├── __init__.py
│   ├── web_search.py    # Tavily web search tool
│   └── youtube.py       # YouTube transcript tool
├── config.py            # Configuration management
├── prompts.py           # System prompts
├── requirements.txt     # Dependencies
└── .env.example         # Environment variable template
```

---

## Dependencies Summary

```
langchain>=1.0.0
langchain-anthropic
langchain-openai
tavily-python
youtube-transcript-api
pydantic>=2.0
rich
python-dotenv
```

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| Which agent API to use? | `create_agent` from `langchain.agents` |
| Default model? | `anthropic:claude-sonnet-4-5-20250929` |
| Web search provider? | Tavily API |
| YouTube transcript method? | `youtube-transcript-api` library |
| Observability? | LangSmith via environment variables |
| Interaction mode? | Interactive CLI with rich formatting |

---

*Research complete. Ready for implementation planning.*

