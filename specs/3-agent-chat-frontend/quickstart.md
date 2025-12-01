# Quickstart: Agent Chat UI Frontend

**Feature**: 3-agent-chat-frontend  
**Time to Complete**: ~5 minutes  

---

## Prerequisites

- Recipe Agent backend code (from spec 1-recipe-agent-backend) ✅
- Python 3.11+ with pip
- API keys configured in `.env` (Anthropic/OpenAI, Tavily)
- Modern web browser

---

## Step 1: Install LangGraph CLI

```bash
cd recipe_creator
pip install langgraph-cli
```

**Note**: No need to install `langgraph` separately—`create_agent` from LangChain 1.0 already uses LangGraph internally and returns a `CompiledStateGraph`.

---

## Step 2: Start the LangGraph Server

```bash
langgraph dev
```

Expected output:
```
🚀 LangGraph server running at http://localhost:2024
📊 API docs at http://localhost:2024/docs
```

**Troubleshooting**:
- Port in use? Set `PORT=2025` environment variable
- Missing dependencies? Run `pip install -r requirements.txt`

---

## Step 3: Connect Agent Chat UI

1. Open your browser and go to: **https://agentchat.vercel.app**

2. In the connection form, enter:
   - **Deployment URL**: `http://localhost:2024`
   - **Assistant ID**: `recipe_creator`

3. Click **Connect**

---

## Step 4: Start Chatting!

Once connected, you'll see the chat interface. Try:

> "How do I make a margarita?"

You should see:
- Your message appear in the chat
- Tool calls (web search) displayed as the agent researches
- The recipe response streaming in

---

## Verification Checklist

- [ ] Server starts without errors
- [ ] Browser can access http://localhost:2024/health
- [ ] Agent Chat UI connects successfully
- [ ] Messages send and receive
- [ ] Tool calls (web search, YouTube) are visible in UI

---

## Quick Commands

| Action | Command |
|--------|---------|
| Start server | `langgraph dev` |
| Start server (different port) | `PORT=2025 langgraph dev` |
| Check server health | `curl http://localhost:2024/health` |
| Stop server | `Ctrl+C` |

---

## Using the Original CLI

The original CLI still works for direct terminal interaction:

```bash
python main.py
```

Both interfaces (CLI and Agent Chat UI) can be used—they're separate entry points to the same agent.

---

## Next Steps

- Try multi-turn conversations
- Test with YouTube video URLs
- Explore the tool visualization in the UI

---

*Quickstart complete. You're ready to use the Recipe Agent with Agent Chat UI!*

