# Quickstart: Recipe Agent Backend

Get the Recipe Agent running in under 5 minutes.

---

## Prerequisites

- Python 3.11+
- Anthropic API key OR OpenAI API key
- Tavily API key
- (Optional) LangSmith API key

---

## Setup

### 1. Install Dependencies

```bash
cd recipe_creator
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# At least one LLM API key required
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# Required for web search
TAVILY_API_KEY=tvly-your-key-here

# Optional: Override model (default: anthropic:claude-sonnet-4-5-20250929)
# RECIPE_AGENT_MODEL=openai:gpt-4o

# Optional: Custom prompt file
# RECIPE_AGENT_PROMPT_FILE=prompts/healthy.txt

# Optional: LangSmith for observability
LANGSMITH_API_KEY=lsv2-your-key-here
LANGSMITH_PROJECT=recipe-agent
LANGSMITH_TRACING=true
```

### 3. Run the Agent

```bash
python main.py
```

---

## Usage

Once running, simply type your recipe questions:

```
You: How do I make an Old Fashioned?

You: Can you find a pasta carbonara recipe?

You: Get the recipe from this video: https://youtube.com/watch?v=xyz123

You: Make that vegetarian

You: quit
```

---

## Configuration

### Change the Model

Set `RECIPE_AGENT_MODEL` in your `.env`:

```bash
# Use GPT-4 instead
RECIPE_AGENT_MODEL=openai:gpt-4o
```

Note: If using OpenAI, also set `OPENAI_API_KEY`.

### Custom System Prompt

1. Create a new prompt file in `prompts/` (e.g., `prompts/healthy.txt`)
2. Set the path in `.env`:

```bash
RECIPE_AGENT_PROMPT_FILE=prompts/healthy.txt
```

Or create different prompt variants:
- `prompts/default.txt` - General recipe assistant
- `prompts/healthy.txt` - Health-focused recipes
- `prompts/cocktail_expert.txt` - Mixology specialist

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key not found" | Check `.env` file exists and has valid keys |
| "No transcript found" | Video may not have captions enabled |
| "Rate limited" | Wait a moment and retry |
| Import errors | Run `pip install -r requirements.txt` again |

---

## API Keys

### Anthropic

Get your key at: https://console.anthropic.com/

### OpenAI

Get your key at: https://platform.openai.com/api-keys

### Tavily

Get your key at: https://tavily.com/ (free tier available)

### LangSmith (Optional)

Get your key at: https://smith.langchain.com/

---

*Happy cooking! 🍳🍹*

