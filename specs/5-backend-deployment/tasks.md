# Tasks: Backend Production Deployment (Cloud Run + CI/CD + Auth + Proxy)

**Feature**: 5-backend-deployment  
**Generated**: 2025-12-13  

## User Stories (Derived)

- **[US1] Deploy backend to Cloud Run**: As a developer, I can deploy the LangGraph backend to Cloud Run and get a public `*.run.app` URL.
- **[US2] Automated CI/CD**: As a developer, pushes to `main` automatically build + deploy the backend to Cloud Run.
- **[US3] Secure config + authentication**: As a developer, I can configure required env vars and require `X-Api-Key` auth in production.
- **[US4] Frontend connects in production**: As a user, I can use the deployed Agent Chat UI to connect to the deployed backend without CORS/auth issues.
- **[US5] YouTube transcripts work in production**: As a user, YouTube transcript retrieval works in production via a residential proxy.

## Dependency Graph (Story Order)

`Phase 1/2` → **US3** → **US1** → **US2** → **US4** → **US5**

## Parallel Execution Opportunities

- **[P]** GitHub workflow authoring (`.github/workflows/deploy.yml`) can be done in parallel with **GCP setup** tasks.
- **[P]** Backend code changes for **auth** and **proxy** can be done in parallel with **workflow** authoring.

---

## Phase 1 — Setup (runbook + accounts)

- [ ] T001 Create deployment runbook in `specs/5-backend-deployment/runbook.md` (project IDs, regions, URLs, secrets checklist)
- [ ] T002 Confirm GCP project + billing enabled (record in `specs/5-backend-deployment/runbook.md`)
- [ ] T003 Enable required GCP APIs (record commands + results in `specs/5-backend-deployment/runbook.md`)
- [ ] T004 Create/confirm Artifact Registry repo `recipe-agent` in `specs/5-backend-deployment/runbook.md`
- [ ] T005 Create/confirm service account `github-deployer` + IAM roles in `specs/5-backend-deployment/runbook.md`
- [ ] T006 Create service account key + store as GitHub secret (record rotation date in `specs/5-backend-deployment/runbook.md`)
- [ ] T007 Create residential proxy account + obtain proxy URL (record provider + URL format in `specs/5-backend-deployment/runbook.md`)

## Phase 2 — Foundational (repo + deployment wiring)

- [ ] T008 [P] Add Cloud Run deploy workflow at `.github/workflows/deploy.yml`
- [ ] T009 Add `LANGGRAPH_API_KEY` secret to workflow env injection in `.github/workflows/deploy.yml`
- [ ] T010 Add required GitHub repository secrets (names + where used) in `specs/5-backend-deployment/runbook.md`
- [ ] T011 [P] Add lightweight “deploy smoke test” script notes in `specs/5-backend-deployment/runbook.md` (curl endpoints + expected status codes)

---

## Phase 3 — [US3] Secure config + authentication

**Goal**: Production backend requires API key; secrets are not leaked.

**Independent test criteria**:
- Requests without `X-Api-Key` fail (401/403)
- Requests with `X-Api-Key: $LANGGRAPH_API_KEY` succeed

- [ ] T012 [US3] Add backend auth implementation entrypoint in `recipe_creator/auth.py` (validate `X-Api-Key` against `LANGGRAPH_API_KEY`)
- [ ] T013 [US3] Wire auth into LangGraph serving layer (update `langgraph.json` and/or add server hook module under `recipe_creator/` per LangGraph Python auth docs)
- [ ] T014 [US3] Add `LANGGRAPH_API_KEY` to `.env.example` (or create `env.example` in repo root) documenting required prod auth secret
- [ ] T015 [US3] Add Cloud Run env var `LANGGRAPH_API_KEY` in manual deploy commands in `specs/5-backend-deployment/runbook.md`
- [ ] T016 [US3] Add “auth verification” curl examples in `specs/5-backend-deployment/runbook.md`

---

## Phase 4 — [US1] Deploy backend to Cloud Run

**Goal**: A Cloud Run service is live and returns successful health/info responses.

**Independent test criteria**:
- `GET {CLOUD_RUN_URL}/ok` returns `200`
- `GET {CLOUD_RUN_URL}/info` returns `200` (with valid auth once US3 is applied)

- [ ] T017 [US1] Build container locally with LangGraph CLI and document the command in `specs/5-backend-deployment/runbook.md`
- [ ] T018 [US1] Push a tagged image to Artifact Registry (record image URI in `specs/5-backend-deployment/runbook.md`)
- [ ] T019 [US1] Deploy Cloud Run service `recipe-agent` manually once (record URL + region in `specs/5-backend-deployment/runbook.md`)
- [ ] T020 [US1] Verify Cloud Run logs + request handling (record checks in `specs/5-backend-deployment/runbook.md`)

---

## Phase 5 — [US2] Automated CI/CD

**Goal**: Push to `main` builds and deploys without manual steps.

**Independent test criteria**:
- GitHub Actions workflow completes successfully on push to `main`
- Cloud Run revision updates and serves latest image

- [ ] T021 [US2] Commit + push `.github/workflows/deploy.yml` to `main`
- [ ] T022 [US2] Verify workflow succeeds and record run URL in `specs/5-backend-deployment/runbook.md`
- [ ] T023 [US2] Verify Cloud Run updated revision and record revision ID in `specs/5-backend-deployment/runbook.md`
- [ ] T024 [US2] Add manual rollback procedure notes in `specs/5-backend-deployment/runbook.md`

---

## Phase 6 — [US4] Frontend connects in production

**Goal**: Deployed Agent Chat UI can talk to deployed backend reliably.

**Independent test criteria**:
- UI connects to backend and can send/receive a message
- Tool calls render correctly in UI

- [ ] T025 [US4] Configure Vercel env vars for `agent_chat_frontend` deployment in `agent_chat_frontend/env.example` (document prod values: `NEXT_PUBLIC_API_URL`, `LANGGRAPH_API_URL`, `NEXT_PUBLIC_ASSISTANT_ID`)
- [ ] T026 [US4] Set passthrough auth key in frontend deployment (set `LANGSMITH_API_KEY` == backend `LANGGRAPH_API_KEY`) in `agent_chat_frontend/env.example`
- [ ] T027 [US4] Verify the API passthrough route works in production (`agent_chat_frontend/src/app/api/[..._path]/route.ts`)
- [ ] T028 [US4] Perform end-to-end chat test from deployed UI (record URL + screenshot notes in `specs/5-backend-deployment/runbook.md`)

---

## Phase 7 — [US5] YouTube transcripts work in production (proxy)

**Goal**: YouTube transcript tool works behind Cloud Run using residential proxy.

**Independent test criteria**:
- Known-captioned video returns transcript in production
- Missing transcript returns a clear error message
- Proxy failure returns a graceful error message

- [ ] T029 [P] [US5] Update YouTube tool to support `PROXY_URL` in `recipe_creator/tools/youtube.py`
- [ ] T030 [P] [US5] Add `PROXY_URL` to `.env.example` (or create `env.example`) documenting proxy format for production
- [ ] T031 [US5] Validate YouTube transcript tool locally without proxy (add a short manual test recipe in `specs/5-backend-deployment/runbook.md`)
- [ ] T032 [US5] Validate YouTube transcript tool in production with proxy enabled (record successful video ID in `specs/5-backend-deployment/runbook.md`)

---

## Final Phase — Polish & Cross-cutting

- [ ] T033 [P] Add Cloud Run “health + info + auth” checklist to `specs/5-backend-deployment/quickstart.md`
- [ ] T034 [P] Update `README.md` with production connection guidance (use API passthrough, don’t expose secret in browser) in `README.md`
- [ ] T035 Add a “cost + quotas” monitoring section to `specs/5-backend-deployment/runbook.md`

---

## Suggested MVP

**MVP = US3 + US1 + US2** (land auth + deploy + CI/CD), then **US4**, then **US5**.


