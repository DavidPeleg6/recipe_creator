# Research: Agent Chat UI Frontend

**Feature**: 3-agent-chat-frontend  
**Date**: December 1, 2025  

---

## Research Questions

### RQ-1: How does Agent Chat UI connect to backend agents?

**Decision**: Use LangGraph Server protocol

**Rationale**: 
Per the [agent-chat-ui repository](https://github.com/langchain-ai/agent-chat-ui), the UI expects a LangGraph-compatible server. The UI communicates with backends using:

1. **Environment Variables** (for self-hosted UI):
   - `NEXT_PUBLIC_API_URL`: Backend server URL (e.g., `http://localhost:2024`)
   - `NEXT_PUBLIC_ASSISTANT_ID`: Graph/agent identifier (e.g., `agent`)

2. **Connection Form** (for hosted UI):
   - Users enter the deployment URL and assistant ID in the UI setup form
   - The hosted app at https://agentchat.vercel.app provides this form

**Alternatives Considered**:
- Custom HTTP endpoints: Not compatible, would require forking the UI
- WebSocket direct connection: Not how Agent Chat UI works

---

### RQ-2: What server infrastructure is needed?

**Decision**: Use `langgraph-cli` to serve the agent

**Rationale**:
The agent-chat-ui expects endpoints provided by LangGraph Server. Options:

1. **LangGraph CLI** (`langgraph dev`): Development server that exposes the required endpoints
2. **LangGraph API Server**: For production deployments
3. **Custom FastAPI wrapper**: Would need to implement LangGraph protocol manually

The CLI approach is simplest for local development and matches the spec's "under 5 minutes setup" requirement.

**Key Finding**:
Per the [LangChain 1.0 reference](https://reference.langchain.com/python/langchain/agents/), `create_agent` **already returns a `CompiledStateGraph`**—it's a LangGraph graph under the hood. No wrapping needed!

```python
# create_agent returns:
CompiledStateGraph[AgentState[ResponseT], ContextT, _InputAgentState, _OutputAgentState[ResponseT]]
```

This significantly simplifies implementation—the existing `agent.py` already produces a LangGraph-compatible graph.

**Alternatives Considered**:
- Custom graph wrapper: Not needed—create_agent is already a graph
- FastAPI server with custom streaming: Too complex, not compatible with Agent Chat UI
- LangServe: Deprecated in favor of LangGraph

---

### RQ-3: What changes are needed to the existing backend?

**Decision**: Add `langgraph.json` configuration only

**Rationale**:
Current state:
- `agent.py` uses `create_agent()` which **already returns a `CompiledStateGraph`**
- `main.py` runs a CLI loop

Required changes:
1. Create `langgraph.json` to configure the LangGraph server (point directly to agent.py)
2. The CLI can remain for direct terminal usage

**No graph wrapper needed!** The `create_agent` function already returns a LangGraph-compatible `CompiledStateGraph`.

**Alternatives Considered**:
- Create separate graph.py wrapper: Unnecessary—create_agent is already a graph
- Rewrite agent using LangGraph from scratch: Unnecessary
- Dual-mode server (CLI + HTTP): Adds complexity, separate entry points cleaner

---

### RQ-4: What is the default port and configuration?

**Decision**: Port 2024, assistant ID "recipe_creator"

**Rationale**:
From the agent-chat-ui `.env.example`:
```
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=recipe_creator
```

Port 2024 is the LangGraph default. Assistant ID "recipe_creator" is more descriptive than the default "agent".

**Configuration**:
- Port: `2024` (LangGraph server default)
- Assistant ID: `recipe_creator` (configured in langgraph.json)

---

### RQ-5: How are tool calls visualized in the UI?

**Decision**: Tool calls are automatically rendered by Agent Chat UI

**Rationale**:
The Agent Chat UI has built-in support for rendering tool calls. When the agent executes tools (web_search, get_youtube_transcript), the UI will:

1. Show tool invocation with parameters
2. Display tool results
3. Show the final agent response

No special formatting is needed from the backend—the LangGraph protocol includes tool call metadata in the response stream.

**Optional Customization**:
- Add `langsmith:nostream` tag to hide certain LLM calls
- Prefix message IDs with `do-not-render-` to hide messages entirely

For the Recipe Agent, default rendering is appropriate.

---

## Technical Findings Summary

| Topic | Finding |
|-------|---------|
| Protocol | LangGraph Server HTTP/streaming |
| Server | `langgraph dev` for local development |
| Port | 2024 (default) |
| Assistant ID | "recipe_creator" |
| Backend Changes | Add langgraph.json only (no wrapper needed!) |
| create_agent | Already returns `CompiledStateGraph` |
| Tool Visualization | Automatic via Agent Chat UI |
| Existing CLI | Remains functional for direct use |

---

## Dependencies Identified

1. **langgraph-cli** - for running the development server
2. **Existing agent.py** - already exports a `CompiledStateGraph` via `create_agent`

**Note**: No additional `langgraph` package needed—`create_agent` from `langchain.agents` already uses LangGraph internally.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| `create_agent` not compatible with LangGraph | Test wrapping early; fallback to direct LangGraph agent |
| CORS issues with hosted UI | LangGraph dev server handles CORS by default |
| Port 2024 conflict | Make port configurable via environment |

---

*Research complete. Ready for Phase 1: Design & Contracts.*

