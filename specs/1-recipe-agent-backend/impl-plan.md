# Implementation Plan: Recipe Agent Backend

**Feature**: 1-recipe-agent-backend  
**Date**: December 1, 2025  
**Status**: Ready for Implementation  

---

## Overview

Build a Python backend for an AI agent that searches the web, retrieves YouTube transcripts, and generates recipes for cocktails and food. Uses LangChain 1.0 with `create_agent`, integrated with LangSmith for observability.

---

## Technical Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Agent Framework | LangChain | 1.0+ |
| LLM Providers | Anthropic (default), OpenAI | Latest |
| Data Validation | Pydantic | 2.0+ |
| Web Search | Tavily | Latest |
| YouTube Transcripts | youtube-transcript-api | Latest |
| CLI Formatting | Rich | Latest |
| Config | python-dotenv | Latest |
| Observability | LangSmith | Via env vars |

---

## Project Structure

```
recipe_creator/
├── main.py                 # Entry point - CLI loop
├── agent.py                # Agent factory and configuration
├── config.py               # Environment and configuration (Pydantic)
├── models/
│   ├── __init__.py         # Export all models
│   ├── recipe.py           # Recipe, Ingredient, RecipeType
│   └── config.py           # AgentConfig model
├── tools/
│   ├── __init__.py         # Tool exports
│   ├── web_search.py       # Tavily web search
│   └── youtube.py          # YouTube transcript retrieval
├── prompts/
│   ├── default.txt         # Default recipe assistant prompt
│   └── healthy.txt         # Health-focused variant (optional)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
└── specs/                  # Feature specifications (existing)
```

---

## Implementation Tasks

### Phase 1: Project Setup

#### Task 1.1: Initialize Python Project
- Create `requirements.txt` with dependencies
- Create `.env.example` template
- Create directory structure

**Dependencies** (`requirements.txt`):
```
langchain>=1.0.0
langchain-anthropic
langchain-openai
pydantic>=2.0
tavily-python
youtube-transcript-api
rich
python-dotenv
```

#### Task 1.2: Create Pydantic Models
- Create `models/recipe.py` with Recipe, Ingredient, RecipeType
- Create `models/config.py` with AgentConfig

**File**: `models/recipe.py`

```python
from enum import Enum
from pydantic import BaseModel, Field

class RecipeType(str, Enum):
    COCKTAIL = "cocktail"
    FOOD = "food"
    DESSERT = "dessert"

class Ingredient(BaseModel):
    name: str = Field(..., description="Ingredient name")
    quantity: str = Field(..., description="Amount")
    unit: str | None = Field(default=None, description="Measurement unit")
    notes: str | None = Field(default=None, description="Preparation notes")

class Recipe(BaseModel):
    name: str
    recipe_type: RecipeType
    ingredients: list[Ingredient]
    instructions: list[str]
    prep_time: str | None = None
    cook_time: str | None = None
    servings: str | None = None
    source_references: list[str] = Field(default_factory=list)
    notes: str | None = None
```

#### Task 1.3: Create Configuration Module
- Load environment variables with dotenv
- Use Pydantic for validation
- Load prompts from file (path in .env)

**File**: `config.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class Config(BaseModel):
    # Model selection (supports both Anthropic and OpenAI)
    model: str = Field(
        default_factory=lambda: os.getenv("RECIPE_AGENT_MODEL", "anthropic:claude-sonnet-4-5-20250929")
    )
    
    # Prompt file path (not the prompt content!)
    prompt_file: Path = Field(
        default_factory=lambda: Path(os.getenv("RECIPE_AGENT_PROMPT_FILE", "prompts/default.txt"))
    )
    
    # API Keys
    anthropic_api_key: str | None = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    openai_api_key: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    tavily_api_key: str | None = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    
    # LangSmith (optional)
    langsmith_api_key: str | None = Field(default_factory=lambda: os.getenv("LANGSMITH_API_KEY"))
    langsmith_project: str = Field(
        default_factory=lambda: os.getenv("LANGSMITH_PROJECT", "recipe-agent")
    )
    
    @property
    def system_prompt(self) -> str:
        """Load system prompt from file."""
        return self.prompt_file.read_text().strip()

# Global config instance
config = Config()
```

---

### Phase 2: Tools Implementation

#### Task 2.1: Web Search Tool
- Implement Tavily search wrapper
- Format results for agent consumption
- Handle errors gracefully

**File**: `tools/web_search.py`

```python
import os
from tavily import TavilyClient

def web_search(query: str) -> str:
    """Search the web for recipe information, ingredients, cooking techniques, or cocktail recipes.
    
    Use this tool when you need to find recipes, look up cooking methods,
    research ingredients, or discover new recipe ideas.
    
    Args:
        query: Search query about recipes, cooking, or cocktails
        
    Returns:
        Formatted search results with titles, snippets, and source URLs
    """
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(query, max_results=5)
    
    results = []
    for item in response.get("results", []):
        results.append(f"**{item['title']}**\n{item['content']}\nSource: {item['url']}\n")
    
    return "\n---\n".join(results) if results else "No results found."
```

#### Task 2.2: YouTube Transcript Tool
- Extract video ID from various URL formats
- Retrieve transcript using youtube-transcript-api
- Handle missing transcripts gracefully

**File**: `tools/youtube.py`

```python
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

def get_youtube_transcript(video_url_or_id: str) -> str:
    """Get the transcript from a YouTube video to extract recipe information.
    
    Use this tool when a user wants to get a recipe from a specific YouTube video,
    or when you need to analyze cooking tutorial content.
    
    Args:
        video_url_or_id: YouTube video URL (any format) or video ID
        
    Returns:
        Full transcript text from the video, or error message if unavailable
    """
    # Extract video ID from various URL formats
    video_id = extract_video_id(video_url_or_id)
    
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([entry["text"] for entry in transcript])
        return f"Transcript for video {video_id}:\n\n{full_text}"
    except TranscriptsDisabled:
        return f"Transcripts are disabled for video {video_id}"
    except NoTranscriptFound:
        return f"No transcript available for video {video_id}"
    except Exception as e:
        return f"Error retrieving transcript: {str(e)}"

def extract_video_id(url_or_id: str) -> str:
    """Extract YouTube video ID from URL or return as-is if already an ID."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([^&\s]+)',
        r'(?:youtu\.be\/)([^\?\s]+)',
        r'(?:youtube\.com\/embed\/)([^\?\s]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id  # Assume it's already a video ID
```

---

### Phase 3: Agent Implementation

#### Task 3.1: Create System Prompt File
- Define recipe assistant persona in a text file
- Include instructions for tool usage
- Specify recipe output format

**File**: `prompts/default.txt`

```text
You are a helpful recipe assistant specializing in both cocktails and food recipes.

Your capabilities:
- Search the web for recipes, cooking techniques, and ingredient information
- Retrieve transcripts from YouTube cooking and cocktail videos
- Generate clear, actionable recipes based on user requests

When providing recipes, always include:
1. Recipe name
2. Complete ingredients list with measurements
3. Step-by-step instructions
4. Prep time and cook time (for food) or preparation notes (for cocktails)
5. Serving size
6. Any helpful tips or variations

When using tools:
- Use web_search to find recipes, techniques, or ingredient information
- Use get_youtube_transcript when a user shares a YouTube video or asks about a specific video

Be conversational, helpful, and enthusiastic about cooking and mixology. 
Ask clarifying questions if needed (dietary restrictions, available ingredients, skill level).
```

#### Task 3.2: Create Agent Factory
- Initialize agent with `create_agent`
- Wire up tools
- Load prompt from config (file-based)

**File**: `agent.py`

```python
from langchain.agents import create_agent
from config import config
from tools.web_search import web_search
from tools.youtube import get_youtube_transcript

def create_recipe_agent(
    model: str | None = None,
    system_prompt: str | None = None
):
    """Create and return a configured recipe agent.
    
    Args:
        model: Model identifier (default from config)
        system_prompt: Custom system prompt (default loaded from prompt file)
        
    Returns:
        Configured LangChain agent
    """
    return create_agent(
        model=model or config.model,
        tools=[web_search, get_youtube_transcript],
        system_prompt=system_prompt or config.system_prompt,
    )
```

---

### Phase 4: CLI Implementation

#### Task 4.1: Create Interactive CLI
- Input/output loop with rich formatting
- Use LangChain message types (HumanMessage, AIMessage)
- Clean exit handling

**File**: `main.py`

```python
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from langchain.messages import HumanMessage, AIMessage
from agent import create_recipe_agent
from config import config

console = Console()

def main():
    # Display startup banner
    console.print(Panel.fit(
        "[bold green]🍹 Recipe Agent Ready! 🍳[/]\n"
        f"Model: {config.model}\n"
        f"Prompt: {config.prompt_file}\n"
        "Type 'quit' or 'exit' to stop.",
        title="Recipe Creator"
    ))
    
    # Create agent
    agent = create_recipe_agent()
    
    # Conversation history using LangChain message types
    messages: list[HumanMessage | AIMessage] = []
    
    # Main conversation loop
    while True:
        try:
            user_input = console.input("\n[bold blue]You:[/] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ("quit", "exit", "q"):
                console.print("[yellow]Goodbye! Happy cooking! 🍳[/]")
                break
            
            # Add user message using LangChain type
            messages.append(HumanMessage(content=user_input))
            
            # Invoke agent
            console.print("[dim]Thinking...[/]")
            result = agent.invoke({"messages": messages})
            
            # Extract and display response
            assistant_message = result["messages"][-1]
            messages.append(assistant_message)  # Already an AIMessage
            
            console.print("\n[bold green]Assistant:[/]")
            console.print(Markdown(assistant_message.content))
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Goodbye![/]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")

if __name__ == "__main__":
    main()
```

---

### Phase 5: Environment Setup

#### Task 5.1: Create Environment Template

**File**: `.env.example`

```bash
# LLM API Keys (at least one required)
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key

# Required: Tavily API Key (for web search)
TAVILY_API_KEY=your-tavily-api-key

# Optional: Override default model
# Anthropic: anthropic:claude-sonnet-4-5-20250929
# OpenAI: openai:gpt-4o, openai:gpt-4o-mini
RECIPE_AGENT_MODEL=anthropic:claude-sonnet-4-5-20250929

# Optional: Path to system prompt file
RECIPE_AGENT_PROMPT_FILE=prompts/default.txt

# Optional: LangSmith observability
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=recipe-agent
LANGSMITH_TRACING=true
```

#### Task 5.2: Create Default Prompt File

Create `prompts/default.txt` with the recipe assistant prompt (see Phase 3).

---

## Acceptance Criteria Mapping

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| FR-1: Web Search | `tools/web_search.py` with Tavily | Planned |
| FR-2: YouTube Analysis | `tools/youtube.py` with youtube-transcript-api | Planned |
| FR-3: Recipe Generation | System prompt defines output format | Planned |
| FR-4: Conversational | Message history in CLI loop | Planned |
| FR-5: Configurable | Config.py + environment variables | Planned |
| FR-6: Observability | LangSmith via env vars | Planned |
| FR-7: Simple Execution | `python main.py` starts CLI | Planned |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| YouTube transcripts unavailable | Graceful error message, suggest alternative |
| Tavily API rate limits | Implement basic retry logic |
| Model API errors | Display error, allow retry |
| LangChain 1.0 API changes | Pin version in requirements.txt |

---

## Testing Strategy

For personal use, manual testing is sufficient:

1. **Smoke Test**: Start CLI, ask "How do I make a mojito?"
2. **Web Search Test**: Ask about an obscure recipe
3. **YouTube Test**: Provide a cooking video URL
4. **Conversation Test**: Multi-turn recipe modification
5. **Error Test**: Invalid YouTube URL handling

---

## Next Steps

1. Run `/speckit.tasks` to generate detailed implementation tasks
2. Implement in order: setup → tools → agent → CLI
3. Test manually after each phase

---

*Implementation plan complete. Ready for task breakdown.*

