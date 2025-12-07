# Implementation Tasks: Recipe Storage

**Feature**: 4-recipe-storage  
**Generated**: December 2, 2025  
**Total Tasks**: 28  
**MVP Scope**: Phases 1-4 (Setup + Foundational + US1 + US2)

---

## Overview

This document provides an actionable, dependency-ordered task list for implementing Recipe Storage. Tasks are organized by user story to enable independent implementation and testing of each increment.

**User Stories** (mapped from Functional Requirements):
- **US1**: Save Recipe with Image Generation (FR-1, FR-2, FR-3, FR-4, FR-5) - *MVP*
- **US2**: Recipe Retrieval & Search (FR-6, FR-7, FR-8) - *MVP*
- **US3**: Recipe Management - Modify & Delete (FR-5 post-save actions)

---

## Phase 1: Setup (Project Initialization)

**Goal**: Add dependencies and create new module directories.

**Independent Test**: `uv pip install -r requirements.txt` succeeds; new imports work.

### Tasks

- [X] T001 Update requirements.txt with sqlalchemy, google-generativeai, google-cloud-storage, Pillow in recipe_creator/requirements.txt
- [X] T002 [P] Create storage/__init__.py with empty exports in recipe_creator/storage/__init__.py
- [X] T003 [P] Create services/__init__.py with empty exports in recipe_creator/services/__init__.py
- [X] T004 [P] Update .env.example with GOOGLE_AI_API_KEY, GCS_BUCKET_NAME, GOOGLE_APPLICATION_CREDENTIALS in recipe_creator/.env.example
- [X] T005 [P] Add recipes.db to .gitignore in recipe_creator/.gitignore

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Implement data models, database setup, and SQL guardrails that all user stories depend on.

**Independent Test**: 
```bash
python -c "from storage.database import init_database; init_database(); print('DB OK')"
python -c "from storage.sql_guardrails import validate_sql; print(validate_sql('DROP TABLE x'))"
```

**Dependencies**: Phase 1 complete

### Tasks

- [X] T006 Extend Recipe model with persistence fields (id, image_url, tags, is_deleted, timestamps) in recipe_creator/models/recipe.py
- [X] T007 Change prep_time and cook_time from timedelta to int (minutes) in recipe_creator/models/recipe.py
- [X] T008 Create SavedRecipeTable SQLAlchemy model in recipe_creator/storage/database.py
- [X] T009 Create get_engine, init_database, get_session functions in recipe_creator/storage/database.py
- [X] T010 [P] Create validate_sql function with forbidden patterns (DROP, TRUNCATE, ALTER, DELETE) in recipe_creator/storage/sql_guardrails.py
- [X] T011 [P] Create inject_soft_delete_filter function for SELECT queries in recipe_creator/storage/sql_guardrails.py
- [X] T012 [P] Create is_read_only helper function in recipe_creator/storage/sql_guardrails.py
- [X] T013 Export database functions from recipe_creator/storage/__init__.py

---

## Phase 3: User Story 1 - Save Recipe with Image Generation [MVP]

**Goal**: User can save recipes with auto-generated images via agent conversation.

**Acceptance Criteria** (from spec.md):
- Agent detects satisfaction and offers to save
- User confirms → recipe is structured, image generated, saved to DB
- Visual confirmation with image URL returned
- Recipe stored with all fields (name, ingredients, instructions, etc.)

**Independent Test**:
1. Run agent with `uv run langgraph dev`
2. Generate a recipe (e.g., "How do I make an Old Fashioned?")
3. Say "This is perfect! Save it"
4. Verify save_recipe tool is called
5. Verify recipe appears in SQLite DB with image_url

**Dependencies**: Phase 2 complete

### Tasks

- [X] T014 [US1] Create image_generation.py with configure_genai and generate_recipe_image functions in recipe_creator/services/image_generation.py
- [X] T015 [US1] Create cloud_storage.py with upload_image and delete_image functions in recipe_creator/services/cloud_storage.py
- [X] T016 [US1] Export services from recipe_creator/services/__init__.py
- [X] T017 [US1] Create save_recipe tool with structured_output validation in recipe_creator/tools/save_recipe.py
- [X] T018 [US1] Implement recipe structuring using llm.with_structured_output(Recipe) in recipe_creator/tools/save_recipe.py
- [X] T019 [US1] Implement image prompt generation with full recipe context in recipe_creator/tools/save_recipe.py
- [X] T020 [US1] Implement GCS upload and database INSERT in recipe_creator/tools/save_recipe.py
- [X] T021 [US1] Create prompts/image_prompt_gen.txt for image generation in recipe_creator/prompts/image_prompt_gen.txt
- [X] T022 [US1] Update config.py with google_ai_api_key and gcs_bucket_name in recipe_creator/config.py

---

## Phase 4: User Story 2 - Recipe Retrieval & Search [MVP]

**Goal**: Agent can search saved recipes and prioritizes them over external sources.

**Acceptance Criteria** (from spec.md):
- Agent searches saved recipes FIRST before web/YouTube
- User can list saved recipes (headers only: name, type)
- User can retrieve full recipe by name
- User can search by ingredient (e.g., "recipes with bourbon")

**Independent Test**:
1. Save a recipe with bourbon (Old Fashioned)
2. Ask "Do I have any recipes with bourbon?"
3. Verify agent queries DB first and finds saved recipe
4. Ask "Show me my saved recipes" - verify headers only

**Dependencies**: Phase 3 complete

### Tasks

- [ ] T023 [US2] Create execute_recipe_sql tool with guardrails integration in recipe_creator/tools/execute_sql.py
- [ ] T024 [US2] Implement query validation using validate_sql in recipe_creator/tools/execute_sql.py
- [ ] T025 [US2] Implement soft delete filter injection for SELECT queries in recipe_creator/tools/execute_sql.py
- [ ] T026 [US2] Export both tools from recipe_creator/tools/__init__.py
- [ ] T027 [US2] Update agent.py to include execute_recipe_sql and save_recipe tools in recipe_creator/agent.py
- [ ] T028 [US2] Update default_prompt.txt with recipe memory priority instructions in recipe_creator/prompts/default_prompt.txt

---

## Phase 5: User Story 3 - Recipe Management (Modify & Delete)

**Goal**: User can modify or delete saved recipes after viewing confirmation.

**Acceptance Criteria** (from spec.md):
- User says "delete this" → soft delete via UPDATE SET is_deleted = true
- User requests changes → agent updates specific fields via SQL
- Deleted recipes don't appear in future searches

**Independent Test**:
1. Save a recipe
2. Say "Actually delete that"
3. Verify UPDATE is_deleted = true executed
4. Ask "Show my recipes" - deleted recipe not shown

**Dependencies**: Phase 4 complete

### Tasks

- [ ] T029 [US3] Add soft delete behavior instructions to default_prompt.txt in recipe_creator/prompts/default_prompt.txt
- [ ] T030 [US3] Add modification instructions (UPDATE with WHERE) to default_prompt.txt in recipe_creator/prompts/default_prompt.txt

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Optional enhancements and final refinements.

**Dependencies**: Phases 3-5 complete

### Tasks

- [ ] T031 [P] Create RecipeCardMessage custom message type for generative UI in recipe_creator/models/ui_messages.py
- [ ] T032 Verify error handling for image generation failures (save without image) in recipe_creator/tools/save_recipe.py

---

## Dependencies Graph

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational: Models + DB + Guardrails)
    │
    ▼
Phase 3 (US1: Save Recipe + Image Gen) ◄── MVP PART 1
    │
    ▼
Phase 4 (US2: Retrieval + Search) ◄── MVP COMPLETE
    │
    ▼
Phase 5 (US3: Modify & Delete)
    │
    ▼
Phase 6 (Polish)
```

---

## Parallel Execution Opportunities

### Within Phase 1 (Setup)
Tasks T002-T005 can all run in parallel after T001 updates requirements.

### Within Phase 2 (Foundational)
- T006-T007 must be sequential (modify same file)
- T008-T009 must be sequential (database.py dependencies)
- T010-T012 can run in parallel (sql_guardrails.py independent functions)
- T013 must be after T008-T009

### Within Phase 3 (US1)
- T014-T015 can run in parallel (independent services)
- T017-T020 must be sequential (same file, building save_recipe)
- T021-T022 can run in parallel with T017-T020

### Within Phase 4 (US2)
- T023-T025 must be sequential (same file)
- T028 can run in parallel with T023-T027

### Phase 6
T031-T032 can run in parallel.

---

## Implementation Strategy

### MVP First (Phases 1-4)
Complete Phases 1-4 to deliver working recipe storage with save and retrieval. This covers the core value proposition: save recipes you love and find them later.

**MVP Deliverables**:
- Extend Recipe model with persistence fields
- SQLite database with SQLAlchemy
- `save_recipe` tool with image generation
- `execute_recipe_sql` tool with guardrails
- Recipe memory search priority
- Soft delete support

### Incremental Delivery
After MVP:
1. **Phase 5**: Recipe modifications and deletions (completes FR-5)
2. **Phase 6**: Generative UI cards (optional enhancement)

### Manual Testing Checkpoints
Test after each phase completion:
- Phase 1: `pip install -r requirements.txt` works
- Phase 2: Database initializes, guardrails block DROP
- Phase 3: `save_recipe` creates DB entry with image_url
- Phase 4: Agent searches DB before web search
- Phase 5: Soft delete works, deleted recipes hidden
- Phase 6: RecipeCardMessage renders in UI (if frontend supports)

---

## Task Count Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | 5 |
| Phase 2 | Foundational | 8 |
| Phase 3 | US1: Save Recipe | 9 |
| Phase 4 | US2: Retrieval & Search | 6 |
| Phase 5 | US3: Modify & Delete | 2 |
| Phase 6 | Polish | 2 |
| **Total** | | **32** |

---

## Notes

- **Tests**: No automated tests (manual testing sufficient for personal use)
- **Image Generation**: Uses Google's Imagen via Gemini API (Nano Banana Pro)
- **Image Storage**: GCS bucket (configured via environment)
- **Database**: SQLite for MVP, PostgreSQL-ready via SQLAlchemy (issue #22)
- **Soft Delete**: All "deletes" are UPDATE SET is_deleted = true
- **Schema in Tool**: Table schema is in `execute_recipe_sql` docstring (LangChain auto-injects)

---

*Tasks are ready for implementation. Start with Phase 1 and proceed sequentially, parallelizing where indicated.*

