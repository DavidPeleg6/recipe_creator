# Tasks: 4-prod-deployment-infra (FR-1 only)

Scope: Coding agent tasks cover only **FR-1: Cloud Database Migration** (PostgreSQL-only, remove SQLite). FR-2/FR-3/FR-4 are manual developer work.

---

## Phase 1: Setup

- [x] T001 Update PostgreSQL-only setup instructions and `DATABASE_URL` env guidance in `/Users/david/Desktop/hackathons/recipe_creator/README.md`

## Phase 2: Foundational (Blocking)

- [x] T002 Remove SQLite dependency (`aiosqlite`) from `/Users/david/Desktop/hackathons/recipe_creator/recipe_creator/requirements.txt`
- [x] T003 Replace SQLite config fields with required `DATABASE_URL` in `/Users/david/Desktop/hackathons/recipe_creator/recipe_creator/config.py`
- [x] T004 Remove SQLite migration/utility script no longer needed at `/Users/david/Desktop/hackathons/recipe_creator/recipe_creator/scripts/migrate_sqlite_to_postgres.py`

## Phase 3: User Story US1 (FR-1 Cloud Database Migration)

- [x] T005 [US1] Rework async engine/session to use `DATABASE_URL` (asyncpg) in `/Users/david/Desktop/hackathons/recipe_creator/recipe_creator/storage/database.py`
- [x] T006 [P] [US1] Remove residual SQLite imports/mentions across codebase (grep and clean) in `/Users/david/Desktop/hackathons/recipe_creator/recipe_creator`
- [ ] T007 [US1] Verify save/query flow hits PostgreSQL: run `init_db()` then save+fetch smoke test against dev DB (script or REPL)

## Final Phase: Polish

- [x] T008 Ensure docs align with PostgreSQL-only posture (cross-check README and comments) in `/Users/david/Desktop/hackathons/recipe_creator/README.md`

---

## Dependencies / Order
- Complete Phase 2 before Phase 3 (engine depends on config/deps cleanup).
- US1 (Phase 3) is the MVP increment.

## Parallel Opportunities
- T002 and T004 can run in parallel (different files, independent).
- T006 can run in parallel with T005 once config changes are staged.

## MVP Scope
- Finish Phase 3 (US1) to deliver PostgreSQL-only storage with SQLite fully removed.

