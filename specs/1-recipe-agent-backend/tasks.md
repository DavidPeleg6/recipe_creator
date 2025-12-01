# Implementation Tasks: Recipe Agent Backend

**Feature**: 1-recipe-agent-backend  
**Generated**: December 1, 2025  
**Total Tasks**: 26  
**MVP Scope**: Phases 1-3 (Setup + Foundational + US1)

---

## Overview

This document provides an actionable, dependency-ordered task list for implementing the Recipe Agent Backend. Tasks are organized by user story to enable independent implementation and testing of each increment.

**User Stories** (mapped from Functional Requirements):
- **US1**: Core Agent with Web Search (FR-1, FR-3, FR-7) - *MVP*
- **US2**: YouTube Recipe Extraction (FR-2)
- **US3**: Conversational Interaction (FR-4)
- **US4**: Agent Configuration & Customization (FR-5)
- **US5**: Observability Integration (FR-6)

---

## Phase 1: Setup (Project Initialization)

**Goal**: Initialize Python project with all dependencies and directory structure.

**Independent Test**: `pip install -r requirements.txt` succeeds without errors.

### Tasks

- [X] T001 Create project directory structure per implementation plan
- [X] T002 [P] Create requirements.txt with all dependencies in recipe_creator/requirements.txt
- [X] T003 [P] Create .env.example template with all environment variables in recipe_creator/.env.example
- [X] T004 [P] Create models/__init__.py with empty exports in recipe_creator/models/__init__.py
- [X] T005 [P] Create tools/__init__.py with empty exports in recipe_creator/tools/__init__.py
- [X] T006 [P] Create prompts/ directory and default.txt placeholder in recipe_creator/prompts/default.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Implement core data models and configuration that all user stories depend on.

**Independent Test**: `python -c "from models import Recipe, Ingredient, RecipeType; from config import config; print(config.model)"` succeeds.

**Dependencies**: Phase 1 complete

### Tasks

- [X] T007 Create RecipeType enum in recipe_creator/models/recipe.py
- [X] T008 Create Ingredient model in recipe_creator/models/recipe.py
- [X] T009 Create Recipe model in recipe_creator/models/recipe.py
- [X] T010 [P] Export all models from recipe_creator/models/__init__.py
- [X] T011 Create Config class with Pydantic validation in recipe_creator/config.py
- [X] T012 Add system_prompt property to load from prompt file in recipe_creator/config.py

---

## Phase 3: User Story 1 - Core Agent with Web Search [MVP]

**Goal**: Working CLI agent that can search the web and generate recipes via natural conversation.

**Acceptance Criteria**:
- User can start agent with `python main.py`
- User can ask "How do I make an Old Fashioned?" and receive a recipe
- User can type "quit" or "exit" to stop the agent

**Independent Test**: 
1. Run `python main.py`
2. Ask "How do I make a mojito?"
3. Verify recipe response with ingredients and instructions
4. Type "quit" to exit cleanly

**Dependencies**: Phase 2 complete

### Tasks

- [X] T013 [US1] Create web_search tool function using Tavily in recipe_creator/tools/web_search.py
- [X] T014 [US1] Export web_search from recipe_creator/tools/__init__.py
- [X] T015 [US1] Create system prompt content in recipe_creator/prompts/default.txt
- [X] T016 [US1] Create create_recipe_agent factory function in recipe_creator/agent.py
- [X] T017 [US1] Create main CLI loop with rich formatting in recipe_creator/main.py
- [X] T018 [US1] Add conversation history tracking using LangChain message types in recipe_creator/main.py

---

## Phase 4: User Story 2 - YouTube Recipe Extraction

**Goal**: Agent can extract recipes from YouTube video transcripts.

**Acceptance Criteria**:
- User can provide a YouTube URL and get recipe extracted from video
- Agent handles videos without transcripts gracefully

**Independent Test**:
1. Run `python main.py`
2. Ask "Get the recipe from https://www.youtube.com/watch?v=dQw4w9WgXcQ" (or valid cooking video)
3. Verify agent attempts to retrieve transcript and responds appropriately

**Dependencies**: Phase 3 complete

### Tasks

- [X] T019 [US2] Create extract_video_id helper function in recipe_creator/tools/youtube.py
- [X] T020 [US2] Create get_youtube_transcript tool function in recipe_creator/tools/youtube.py
- [X] T021 [US2] Export get_youtube_transcript from recipe_creator/tools/__init__.py
- [X] T022 [US2] Add YouTube tool to agent in recipe_creator/agent.py

---

## Phase 5: User Story 4 - Agent Configuration & Customization

**Goal**: User can customize agent behavior via prompt files and model selection.

**Acceptance Criteria**:
- User can switch models via RECIPE_AGENT_MODEL env var
- User can use custom prompt files via RECIPE_AGENT_PROMPT_FILE env var
- Creating a new prompt file changes agent personality

**Independent Test**:
1. Create `prompts/healthy.txt` with health-focused prompt
2. Set `RECIPE_AGENT_PROMPT_FILE=prompts/healthy.txt` in .env
3. Run agent and verify health-focused responses

**Dependencies**: Phase 3 complete (can be done in parallel with Phase 4)

### Tasks

- [X] T023 [P] [US4] Create healthy.txt prompt variant in recipe_creator/prompts/healthy.txt
- [X] T024 [US4] Verify model switching works with both Anthropic and OpenAI in recipe_creator/config.py

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Final refinements and documentation.

**Dependencies**: Phases 3-5 complete

### Tasks

- [X] T025 Verify all error handling paths work correctly in recipe_creator/tools/youtube.py
- [X] T026 Update startup banner to show loaded configuration in recipe_creator/main.py

---

## Dependencies Graph

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational)
    │
    ▼
Phase 3 (US1: Core Agent + Web Search) ◄── MVP COMPLETE
    │
    ├─────────────┬─────────────┐
    ▼             ▼             │
Phase 4       Phase 5           │
(US2: YouTube) (US3: Config)    │
    │             │             │
    └─────────────┴─────────────┘
                  │
                  ▼
           Phase 6 (Polish)
```

---

## Parallel Execution Opportunities

### Within Phase 1 (Setup)
Tasks T002-T006 can all run in parallel after T001 creates directory structure.

### Within Phase 2 (Foundational)
- T007-T009 must be sequential (Recipe depends on Ingredient depends on RecipeType)
- T010 can run after T009
- T011-T012 can run in parallel with T007-T010

### Within Phase 3 (US1)
- T013-T015 can run in parallel
- T016 depends on T013-T015
- T017-T018 depend on T016

### Phases 4 and 5
These entire phases can run in parallel after Phase 3 completes.

---

## Implementation Strategy

### MVP First (Phases 1-3)
Complete Phases 1-3 to deliver a working recipe agent with web search. This covers the core value proposition: ask for a recipe, get a recipe.

**MVP Deliverables**:
- Working CLI interface
- Web search for recipes via Tavily
- Recipe generation with proper formatting
- Conversation history for follow-up questions

### Incremental Delivery
After MVP:
1. **Phase 4**: Add YouTube capability (expands content sources)
2. **Phase 5**: Add configuration flexibility (enables customization)
3. **Phase 6**: Polish and refinements

### Manual Testing Checkpoints
Test after each phase completion:
- Phase 1: `pip install -r requirements.txt` works
- Phase 2: Models import successfully
- Phase 3: Full agent conversation works (MVP!)
- Phase 4: YouTube transcript extraction works
- Phase 5: Custom prompts load correctly
- Phase 6: Error scenarios handled gracefully

---

## Task Count Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | 6 |
| Phase 2 | Foundational | 6 |
| Phase 3 | US1: Core Agent + Web Search | 6 |
| Phase 4 | US2: YouTube | 4 |
| Phase 5 | US3: Configuration | 2 |
| Phase 6 | Polish | 2 |
| **Total** | | **26** |

---

## Notes

- **Tests**: No automated tests included per spec (manual testing sufficient for personal use)
- **Observability**: LangSmith integration is via environment variables only (no code tasks needed beyond .env.example)
- **FR-4 (Conversational)**: Built into core agent via message history tracking in Phase 3
- **FR-6 (Observability)**: Covered by LangSmith env vars in .env.example (T003)

---

*Tasks are ready for implementation. Start with Phase 1 and proceed sequentially, parallelizing where indicated.*
