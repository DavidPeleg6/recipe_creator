# Recipe Creator Agent

A conversational AI agent that helps you find and create recipes for cocktails, drinks, and food. Powered by LangChain and Claude.

## Features

- 🍹 **Recipe Discovery**: Ask for any recipe and get detailed instructions
- 🔍 **Web Search**: Searches the web for the latest recipes and techniques
- 📺 **YouTube Integration**: Can extract recipes from YouTube video transcripts
- 💬 **Chat Interface**: Use via CLI or web-based Agent Chat UI

## Prerequisites

- Python 3.11+
- API Keys:
  - **Anthropic** (Claude) or **OpenAI** API key
  - **Tavily** API key (for web search)

## Quick Start

### 1. Setup Environment

```bash
cd recipe_creator

# Create virtual environment
python -m venv ../.venv
source ../.venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the `recipe_creator/` directory:

```env
ANTHROPIC_API_KEY=your_anthropic_key_here
TAVILY_API_KEY=your_tavily_key_here
```

## Running the Agent

### Option A: Command Line Interface (CLI)

Run the agent directly in your terminal:

```bash
cd recipe_creator
python main.py
```

Then chat with the agent:
```
You: How do I make a mojito?
Agent: [searches web and provides recipe]
```

Type `quit` or `exit` to end the session.

### Option B: Web Chat Interface (Agent Chat UI)

Connect to LangChain's hosted Agent Chat UI for a visual chat experience.

#### Step 1: Start the LangGraph Server

```bash
cd recipe_creator
source ../.venv/bin/activate
langgraph dev --no-browser --port 2024
```

You should see:
```
🚀 API: http://127.0.0.1:2024
📚 API Docs: http://127.0.0.1:2024/docs
```

#### Step 2: Connect Agent Chat UI

1. Open **https://agentchat.vercel.app** in your browser

2. Enter the connection details:
   - **Deployment URL**: `http://localhost:2024`
   - **Assistant / Graph ID**: `recipe_creator`
   - **LangSmith API Key**: Leave empty (not required for local server)

3. Click **Continue**

4. Start chatting! Try: "How do I make a mojito?"

#### Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 2024 in use | Use `PORT=2025 langgraph dev` |
| Connection fails | Ensure server is running and showing "API: http://..." |
| Server stops unexpectedly | Restart with `langgraph dev` |

## Project Structure

```
recipe_creator/
├── main.py              # CLI entry point
├── agent.py             # Agent factory (creates the LangGraph agent)
├── config.py            # Configuration management
├── langgraph.json       # LangGraph server configuration
├── requirements.txt     # Python dependencies
├── models/              # Data models (Recipe, etc.)
├── tools/               # Agent tools
│   ├── web_search.py    # Tavily web search
│   └── youtube.py       # YouTube transcript extraction
└── prompts/             # System prompts
    └── default_prompt.txt
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | Anthropic Claude API key |
| `OPENAI_API_KEY` | Yes* | OpenAI API key (alternative to Anthropic) |
| `TAVILY_API_KEY` | Yes | Tavily API key for web search |
| `PORT` | No | Server port (default: 2024) |

*At least one LLM API key is required.

### Customizing the Agent

Edit `prompts/default_prompt.txt` to customize the agent's behavior and personality.

## License

MIT

