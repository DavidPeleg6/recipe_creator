# Implementation Plan: Agent Chat UI Frontend

**Feature**: 3-agent-chat-frontend  
**Date**: December 1, 2025  
**Status**: Ready for Implementation  

---

## Overview

Connect the existing Recipe Agent backend to LangChain's hosted Agent Chat UI. Since `create_agent` from LangChain 1.0 already returns a `CompiledStateGraph`, only minimal configuration is needed—just a `langgraph.json` file to configure the development server.

---

## Technical Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Server | LangGraph CLI | Latest |
| Existing Backend | LangChain `create_agent` (returns `CompiledStateGraph`) | 1.0+ |
| Frontend | Hosted Agent Chat UI | N/A (Vercel) |

---

## Project Structure Changes

```
recipe_creator/
├── main.py                 # CLI entry point (unchanged)
├── agent.py                # Agent factory (already returns CompiledStateGraph!)
├── langgraph.json          # NEW: LangGraph server configuration
├── config.py               # Configuration (unchanged)
├── models/                 # Data models (unchanged)
├── tools/                  # Tools (unchanged)
├── prompts/                # Prompts (unchanged)
└── requirements.txt        # Updated: add langgraph-cli
```

**New Files**: 1 (`langgraph.json`)
**Modified Files**: 1 (`requirements.txt`)

**Key Insight**: Per [LangChain 1.0 reference](https://reference.langchain.com/python/langchain/agents/), `create_agent` already returns a `CompiledStateGraph`—no wrapper needed!

---

## Implementation Tasks

### Phase 1: Dependencies

#### Task 1.1: Update Requirements

Add LangGraph CLI to `requirements.txt`:

```
langgraph-cli>=0.1.0
```

**Note**: No need to add `langgraph` package—`create_agent` from `langchain.agents` already uses LangGraph internally and returns a `CompiledStateGraph`.

**Effort**: 5 minutes

---

### Phase 2: Server Configuration

#### Task 2.1: Create LangGraph Configuration

Create `langgraph.json` in the `recipe_creator/` directory:

**File**: `langgraph.json`

```json
{
  "graphs": {
    "recipe_creator": "./agent.py:create_recipe_agent"
  },
  "env": ".env"
}
```

**Configuration**:
- `graphs.recipe_creator`: Points directly to `create_recipe_agent` in `agent.py` (already returns `CompiledStateGraph`)
- `env`: Loads environment variables from `.env` file

**Effort**: 5 minutes

---

### Phase 3: Testing & Verification

#### Task 3.1: Start Server and Verify

1. Install dependencies: `pip install -r requirements.txt`
2. Start server: `langgraph dev`
3. Verify health: `curl http://localhost:2024/health`

**Expected Output**:
```
🚀 LangGraph server running at http://localhost:2024
```

**Effort**: 10 minutes

#### Task 3.2: Connect Agent Chat UI

1. Open https://agentchat.vercel.app
2. Enter deployment URL: `http://localhost:2024`
3. Enter assistant ID: `recipe_creator`
4. Send test message: "How do I make a mojito?"

**Verification**:
- [ ] Connection succeeds
- [ ] Message sends
- [ ] Tool calls visible (web search)
- [ ] Response streams correctly

**Effort**: 15 minutes

---

## Acceptance Criteria Mapping

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| FR-1: Backend Server Exposure | `langgraph dev` serves on port 2024 | Planned |
| FR-2: Agent Chat UI Compatibility | `graph.py` wraps agent for LangGraph | Planned |
| FR-3: Connection Configuration | `langgraph.json` with assistant ID "recipe_creator" | Planned |
| FR-4: Local Development Workflow | Single command `langgraph dev` | Planned |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| `create_agent` graph format issues | Per LangChain docs, returns `CompiledStateGraph`—natively compatible |
| CORS issues | LangGraph dev server includes CORS headers by default |
| Port 2024 in use | Document `PORT` env var for alternative |
| Streaming not working | `CompiledStateGraph` supports streaming natively |

---

## Dependencies

| Dependency | Purpose | Risk Level |
|------------|---------|------------|
| langgraph-cli | Development server | Low |
| Existing agent.py | Agent logic (already returns `CompiledStateGraph`) | None (already working) |
| Agent Chat UI (hosted) | Frontend | Low (external service) |

**Note**: `langgraph` package not needed separately—`create_agent` uses it internally.

---

## Effort Estimate

| Phase | Tasks | Time |
|-------|-------|------|
| Phase 1: Dependencies | 1 | 5 min |
| Phase 2: Configuration | 1 | 5 min |
| Phase 3: Testing | 2 | 25 min |
| **Total** | **4** | **~35 minutes** |

---

## Files to Create/Modify

### New Files

1. `langgraph.json` - Server configuration (points directly to existing agent)

### Modified Files

1. `requirements.txt` - Add langgraph-cli

**Note**: No `graph.py` wrapper needed! `create_agent` already returns a `CompiledStateGraph`.

---

## Next Steps

1. Run `/speckit.tasks` to generate detailed implementation tasks
2. Implement in order: dependencies → graph wrapper → config → test
3. Verify with hosted Agent Chat UI

---

*Implementation plan complete. Minimal changes needed—primarily wrapping existing agent for LangGraph compatibility.*

