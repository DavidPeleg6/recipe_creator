# Tasks: Agent Chat UI Frontend

**Feature**: 3-agent-chat-frontend  
**Generated**: December 1, 2025  
**Estimated Effort**: ~35 minutes  

---

## Overview

Connect the existing Recipe Agent backend to LangChain's hosted Agent Chat UI. Since `create_agent` already returns a `CompiledStateGraph`, only configuration changes are needed.

**Key Insight**: Per LangChain 1.0 reference, no wrapper code is required—the existing agent is already LangGraph-compatible.

---

## Phase 1: Setup

**Goal**: Install required dependencies for LangGraph server

### Tasks

- [x] T001 Add langgraph-cli dependency to `recipe_creator/requirements.txt`

**Completion Criteria**:
- `langgraph-cli[inmem]>=0.4.7` is listed in requirements.txt
- `pip install -r requirements.txt` succeeds

---

## Phase 2: Configuration (FR-1, FR-2)

**Goal**: Configure LangGraph server to expose the Recipe Agent

**User Stories Addressed**:
- FR-1: Backend Server Exposure
- FR-2: Agent Chat UI Compatibility

### Tasks

- [x] T002 [P] Create `recipe_creator/langgraph.json` with graph configuration pointing to `agent.py:create_recipe_agent`

**Completion Criteria**:
- `langgraph.json` exists in `recipe_creator/` directory
- Configuration includes `graphs.recipe_creator` pointing to `./agent.py:create_recipe_agent`
- Configuration includes `env` pointing to `.env`

---

## Phase 3: Verification (FR-3, FR-4)

**Goal**: Verify server starts and Agent Chat UI can connect

**User Stories Addressed**:
- FR-3: Connection Configuration
- FR-4: Local Development Workflow

### Tasks

- [x] T003 Start LangGraph server with `langgraph dev` and verify health endpoint at `http://localhost:2024/ok`
- [x] T004 Connect hosted Agent Chat UI (https://agentchat.vercel.app) using deployment URL `http://localhost:2024` and assistant ID `recipe_creator`
- [x] T005 Send test message "How do I make a mojito?" and verify response streams with tool calls visible

**Completion Criteria**:
- Server starts without errors on port 2024
- Health endpoint returns `{"status": "ok"}`
- Agent Chat UI connects successfully
- Messages send and receive correctly
- Tool calls (web search) are visible in UI
- Response streams to completion

---

## Dependencies

```
T001 ─► T002 ─► T003 ─► T004 ─► T005
```

**Dependency Chain**:
1. T001 (dependencies) must complete before T002 (configuration)
2. T002 (configuration) must complete before T003 (server start)
3. T003 (server running) must complete before T004 (UI connection)
4. T004 (connection) must complete before T005 (message test)

---

## Parallel Execution Opportunities

This feature has minimal parallelization due to sequential dependencies. However:

- T001 and documentation updates could run in parallel (if documentation existed)
- Multiple verification tests (T004, T005) could run concurrently once server is up

---

## Files Summary

### New Files (1)

| File | Task | Description |
|------|------|-------------|
| `recipe_creator/langgraph.json` | T002 | LangGraph server configuration |

### Modified Files (1)

| File | Task | Description |
|------|------|-------------|
| `recipe_creator/requirements.txt` | T001 | Add langgraph-cli dependency |

---

## Implementation Strategy

### MVP Scope

All tasks (T001-T005) constitute the MVP. This is a minimal feature with ~35 minutes total effort.

### Incremental Delivery

1. **Increment 1** (T001-T002): Server can start (~10 min)
2. **Increment 2** (T003-T005): Full verification complete (~25 min)

---

## Acceptance Criteria Mapping

| Requirement | Task(s) | Verification |
|-------------|---------|--------------|
| FR-1: Backend Server Exposure | T001, T002, T003 | Server responds to health check |
| FR-2: Agent Chat UI Compatibility | T002, T004 | UI connects successfully |
| FR-3: Connection Configuration | T004 | Connection with documented parameters works |
| FR-4: Local Development Workflow | T003 | Single `langgraph dev` command starts server |

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `pip install -r requirements.txt` | Install dependencies |
| `langgraph dev` | Start LangGraph server |
| `curl http://localhost:2024/health` | Verify server health |
| `PORT=2025 langgraph dev` | Start on alternate port |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 2024 in use | Set `PORT=2025` environment variable |
| CORS errors | LangGraph dev server includes CORS headers by default |
| Module not found | Verify `langgraph.json` path is correct |
| Connection fails | Ensure server is running and firewall allows localhost |

---

*Tasks generated from spec.md, impl-plan.md, data-model.md, contracts/langgraph-server.md, research.md, and quickstart.md*

