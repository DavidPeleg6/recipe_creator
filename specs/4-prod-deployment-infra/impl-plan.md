# Implementation Plan: FR-1 Cloud Database Migration

**Feature**: 4-prod-deployment-infra  
**Scope**: FR-1 only (coding agent tasks)  
**Plan Length**: Super short, implementation-focused  

---

## Goal

Move the Recipe Agent to PostgreSQL (Neon) exclusively, removing all SQLite code, configuration, and dependencies while supporting distinct dev/prod databases via `DATABASE_URL`.

---

## Plan (Super Short)

1) **Configuration & Settings**
   - Replace SQLite config with `DATABASE_URL` (required for all environments).
   - Default to SSL-required connection strings (Neon defaults).
   - Keep dev/prod separation via different `DATABASE_URL` values.

2) **Dependencies & Engines**
   - Remove `aiosqlite` usage and dependency.
   - Ensure `sqlalchemy` uses async PostgreSQL driver (`psycopg[binary]` already present).
   - Drop any SQLite-specific engine creation paths.

3) **Storage Layer Updates**
   - Update `storage/database.py` to build async engine from `DATABASE_URL`.
   - Remove SQLite path logic and file-based initialization.
   - Confirm `init_db()` runs against PostgreSQL.

4) **Tools & Recipes**
   - Verify `recipe_storage` (save/query) uses the updated session factory.
   - Remove or archive the `migrate_sqlite_to_postgres.py` script as no migration is needed.

5) **Docs & Env**
   - Update README/setup instructions for PostgreSQL-only.
   - Document required env vars: `DATABASE_URL` (dev), `DATABASE_URL` (prod).

6) **Testing & Verification**
   - Run migrations/create tables via `init_db()` against a dev PostgreSQL instance.
   - Save + fetch recipe smoke test (dev DB).
   - Dependency check: ensure no SQLite modules remain.

---

## Risks & Mitigations (Concise)

| Risk | Mitigation |
|------|------------|
| Missing SSL params for Neon | Rely on Neon-provided `DATABASE_URL` (includes SSL) |
| Stale SQLite imports remain | Grep for `sqlite`/`aiosqlite` and remove |
| Dev DB misconfiguration | Provide sample `.env` with dev `DATABASE_URL` |

---

## Acceptance Trace (FR-1)

| Acceptance Item | Plan Step |
|-----------------|-----------|
| Remove SQLite code/deps | Steps 2, 3, 4 |
| PostgreSQL-only storage | Steps 1, 3 |
| Dev/Prod DB separation | Step 1 |
| Secure connection | Step 1 (SSL via Neon URL) |
| Graceful failures | Step 6 (verify error handling paths) |
| Save/query via PostgreSQL | Step 6 (smoke test) |

---

## Notes

- Manual developer tasks for FR-2/FR-3/FR-4 are out of scope for this plan.  
- `setup-plan.sh` script not present; plan created manually using existing spec.

