# Implementation Tasks: Save Recipes

**Feature**: 1-save-recipes  
**Date**: December 7, 2025  
**Status**: Ready for Implementation  

---

## Overview

Implement persistent recipe storage with 2 tools: `save_recipe` (with HITL approval) and `explore_recipes_db` (SQL queries).

**Key Design Decisions**:
- 2 tools only (no separate list/get/delete tools)
- Direct SQLAlchemy (no repository pattern)
- explore_recipes_db enables SELECT + UPDATE (soft delete via `is_deleted = 1`)
- HumanInTheLoopMiddleware handles approval UI (no frontend changes)

---

## Phase 1: Setup

**Goal**: Initialize project structure and dependencies.

- [x] T001 Add `sqlalchemy>=2.0` and `aiosqlite` to requirements.txt
- [ ] T002 Run `pip install -r requirements.txt`  *(blocked: pip is externally managed; use venv or --break-system-packages)*
- [x] T003 Create `data/` directory for SQLite database
- [x] T004 Create `storage/` package with `__init__.py`

**Done when**: Dependencies installed, directories exist.

---

## Phase 2: Database Layer

**Goal**: Set up SQLAlchemy models and database connection.

- [x] T005 [P] Add `database_path` and `database_url` properties to config.py
- [x] T006 [P] Create `SavedRecipeDB` SQLAlchemy model in models/saved_recipe.py
- [x] T007 Create async engine and `AsyncSessionLocal` in storage/database.py
- [x] T008 Create `init_db()` function in storage/database.py
- [x] T009 Export `SavedRecipeDB` from models/__init__.py

**Done when**:
```bash
python -c "from storage.database import init_db; import asyncio; asyncio.run(init_db())"
sqlite3 data/recipes.db ".schema saved_recipes"
```

---

## Phase 3: Storage Tools

**Goal**: Implement both tools so we can test saves immediately.

### save_recipe tool

- [x] T010 Create `save_recipe` async function signature in tools/recipe_storage.py
- [x] T011 Implement validation (name required, recipe_type in ['cocktail','food','dessert'])
- [x] T012 Implement INSERT using `SavedRecipeDB` and `AsyncSessionLocal`
- [x] T013 Return success message with recipe name

### explore_recipes_db tool

- [x] T014 [P] Create `BLOCKED_SQL` patterns list in tools/recipe_storage.py
- [x] T015 [P] Create `explore_recipes_db` async function signature
- [x] T016 Implement query validation (must start with SELECT or UPDATE)
- [x] T017 Implement blocked pattern regex check
- [x] T018 Implement SELECT execution with table formatting (cap 50 rows)
- [x] T019 Implement UPDATE execution with row count response

### Exports

- [x] T020 Export both tools from tools/__init__.py

**Done when** (test without agent):
```python
# In Python REPL
import asyncio
from tools.recipe_storage import save_recipe, explore_recipes_db

# Test save
asyncio.run(save_recipe("Test Recipe", "cocktail", [{"name":"gin","quantity":"2","unit":"oz"}], ["Mix"]))

# Test query
asyncio.run(explore_recipes_db("SELECT name FROM saved_recipes WHERE is_deleted = 0"))
```

---

## Phase 4: Agent Integration

**Goal**: Wire tools into agent with HITL middleware.

- [x] T021 Import `HumanInTheLoopMiddleware` and `MemorySaver` in agent.py
- [x] T022 Create `hitl_middleware` with `interrupt_on={"save_recipe": True}`
- [x] T023 Add `save_recipe` and `explore_recipes_db` to tools list
- [x] T024 Add `middleware=[hitl_middleware]` to `create_agent` call
- [x] T025 Add `checkpointer=MemorySaver()` to `create_agent` call

**Done when**:
1. Start agent: `langgraph dev --no-browser --port 2024`
2. Connect Agent Chat UI
3. Say "save a test recipe called Mojito"
4. UI shows approval prompt → Approve
5. Say "show my saved recipes"
6. Agent queries and shows Mojito

---

## Phase 5: Prompt Engineering

**Goal**: Add satisfaction detection to system prompt.

- [x] T026 Add Recipe Saving section to prompts/default_prompt.txt with satisfaction signals, save offer examples, and SQL query patterns. also update to make the model create meaningful tags according to flavor profile, etc. make absolutely sure that the system prompt doesnt become too long.

**Done when**: Agent offers to save after user says "This is perfect!" or "I'm making this tonight"

---

## Phase 6: Polish

**Goal**: Documentation and final validation.

- [x] T027 [P] Add docstrings with examples to both tools
- [x] T028 [P] Add schema comments to storage/database.py
- [ ] T029 Test complete flow: generate recipe → express satisfaction → save → list → soft delete
- [ ] T030 Verify hard DELETE is blocked by guardrails

**Done when**: End-to-end user journey works smoothly.

---

## Dependency Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Database)
    ↓
Phase 3 (Tools) ──→ Phase 4 (Agent) ──→ Phase 5 (Prompt) ──→ Phase 6 (Polish)
```

All phases are sequential. No parallel phases (each depends on previous).

---

## Parallel Tasks Within Phases

| Phase | Parallel Tasks |
|-------|----------------|
| Phase 2 | T005 ⚡ T006 (config + model) |
| Phase 3 | T014 ⚡ T015 (blocked patterns + function sig) |
| Phase 6 | T027 ⚡ T028 (docstrings + schema comments) |

---

## Task Statistics

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1 | 4 | Setup |
| Phase 2 | 5 | Database layer |
| Phase 3 | 11 | Both tools |
| Phase 4 | 5 | Agent integration |
| Phase 5 | 1 | Prompt update |
| Phase 6 | 4 | Polish |
| **Total** | **30** | |

---

## MVP

**Minimum**: Phase 1-4 (25 tasks)

Delivers:
- ✅ save_recipe with HITL approval
- ✅ explore_recipes_db for queries
- ✅ End-to-end save and retrieve

**Add Phase 5** for smarter UX (agent offers to save proactively)

---

*30 tasks total. Each phase has clear "done when" criteria.*
