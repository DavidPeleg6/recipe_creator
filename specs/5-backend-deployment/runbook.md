# Backend Deployment Runbook (Cloud Run + CI/CD)

This runbook is the **single source of truth** for production deployment details: project IDs, regions, service URL, secrets checklist, and the one-time GCP setup commands.

---

## Deployment Facts (fill these in)

- **GCP Project ID**: `gen-lang-client-0778161380` (note: project **name** is “recipe-agent”)
- **Billing enabled**: `yes` (yes/no + date confirmed)
- **Region**: `us-central1`
- **Artifact Registry repo**: `recipe-agent` (location: `us-central1`)
- **Cloud Run service name**: `recipe-agent`
- **Cloud Run URL**: `REPLACE_ME` (e.g. `https://recipe-agent-xxxxx-uc.a.run.app`)
- **GitHub repo**: `https://github.com/DavidPeleg6/recipe_creator/tree/main/recipe_creator`

---

## Secrets Checklist (do not commit secrets)

### GitHub Actions secrets (Repository Settings → Secrets and variables → Actions)

- `GCP_PROJECT_ID` = **GCP Project ID**
- `GCP_SA_KEY` = **service account JSON key** (entire JSON document)
- `ANTHROPIC_API_KEY`
- `TAVILY_API_KEY`
- `DATABASE_URL`
- `LANGGRAPH_API_KEY` (shared secret used as `X-Api-Key`)
- `LANGSMITH_API_KEY` (optional; only if you use LangSmith)
- `PROXY_URL` (residential proxy, required for YouTube transcripts in Cloud Run)

### Cloud Run runtime env vars

These should be set via GitHub Actions deploy (preferred) or `gcloud run deploy --set-env-vars` (manual):

- `ANTHROPIC_API_KEY`
- `TAVILY_API_KEY`
- `DATABASE_URL`
- `LANGGRAPH_API_KEY`
- `LANGSMITH_API_KEY` (optional)
- `LANGSMITH_TRACING=true` (optional)
- `PROXY_URL` (required for YouTube transcripts in Cloud Run)

---

## Phase 1 — One-time GCP setup (manual)

> All commands below are intended to be run on your machine with `gcloud` installed and authenticated.

### T002 — Confirm project + billing

#### Console (recommended): confirm billing is enabled

1. Open Cloud Console → Billing  
   - `https://console.cloud.google.com/billing`
2. In the left nav, click **My projects**
3. Find **`recipe-agent`** in the table:
   - If it shows a **Billing account** and the status indicates billing is enabled, you’re done.
   - If it shows **No billing account**, you must **link** a billing account to the project (requires permissions like *Project Billing Manager*).

#### CLI (optional): confirm billing via gcloud

> This requires that your current Google account has permission to view billing on the project.

```bash
# Set project
# IMPORTANT: `gcloud config set project` expects the **PROJECT_ID**, not the display name.
# From `gcloud projects list`:
# - PROJECT_ID = gen-lang-client-0778161380
# - NAME       = recipe-agent
gcloud config set project gen-lang-client-0778161380

# Verify
gcloud config get-value project
gcloud projects describe gen-lang-client-0778161380 --format="value(projectNumber)"

# Optional: billing status (may require permissions)
gcloud beta billing projects describe gen-lang-client-0778161380 --format="json(billingEnabled,billingAccountName)"
```

- **Project ID confirmed**: `gen-lang-client-0778161380`
- **Project number confirmed**: `821038791644`
- **Billing enabled confirmed**: `yes` (2025-12-14)
  - Billing is enabled in GCP Console (manual):
  - `https://console.cloud.google.com/billing`

#### If you get “does not have permission” errors

If you see an error like:
- `does not have permission to access projects instance ... (or it may not exist)`

That’s **not a billing confirmation**. It means the **active gcloud account** doesn’t have access to that project (or the project ID is wrong).

To troubleshoot:

```bash
# See which account is active
gcloud auth list

# (If needed) login with the correct Google account that owns the project
gcloud auth login

# (If needed) set the active account explicitly
gcloud config set account YOUR_EMAIL

# Quick check that you can see the project
gcloud projects describe gen-lang-client-0778161380
```

You may also see this warning:
- `Your active project does not match the quota project in your local Application Default Credentials file`

It’s **not billing-related**. It means:
- `gcloud` is using your interactive login, but some tools/SDKs use **Application Default Credentials** (`gcloud auth application-default ...`).
- The “quota project” on those ADC creds is still pointing at a different project, which can cause **quota/billing attribution** warnings (and sometimes API calls to fail if the quota project isn’t allowed).

You can resolve it with:

```bash
gcloud auth application-default set-quota-project gen-lang-client-0778161380
```

### T003 — Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com

# Optional: verify enabled services
gcloud services list --enabled --filter="name:(run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com iam.googleapis.com)"
```

- **Result (paste output)**:
```bash
NAME                             TITLE
artifactregistry.googleapis.com  Artifact Registry API
cloudbuild.googleapis.com        Cloud Build API
iam.googleapis.com               Identity and Access Management (IAM) API
run.googleapis.com               Cloud Run Admin API
```

### T004 — Create/confirm Artifact Registry repo

```bash
# Create (idempotent: if it exists already, gcloud will error; use describe below to check)
gcloud artifacts repositories create recipe-agent \
  --repository-format=docker \
  --location=us-central1 \
  --description="Recipe Agent container images"

# Verify
gcloud artifacts repositories describe recipe-agent --location=us-central1
```

- **Result (paste output)**:
```bash
Encryption: Google-managed key
Repository Size: 0.000MB
createTime: '2025-12-14T15:23:35.817043Z'
description: Recipe Agent container images
format: DOCKER
mode: STANDARD_REPOSITORY
name: projects/gen-lang-client-0778161380/locations/us-central1/repositories/recipe-agent
registryUri: us-central1-docker.pkg.dev/gen-lang-client-0778161380/recipe-agent
satisfiesPzi: true
updateTime: '2025-12-14T15:23:35.817043Z'
vulnerabilityScanningConfig:
  enablementState: SCANNING_DISABLED
  enablementStateReason: API containerscanning.googleapis.com is not enabled.
  lastEnableTime: '2025-12-14T15:23:26.899933406Z'
```

### T005 — Create/confirm service account + IAM roles

```bash
PROJECT_ID=$(gcloud config get-value project)

# Create service account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"

# Grant roles needed for pushing images + deploying Cloud Run
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

- **Service account email**: `github-deployer@gen-lang-client-0778161380.iam.gserviceaccount.com` (this is a **service account**, not your Gmail)
- **IAM binding verification (optional)**:

```bash
gcloud projects get-iam-policy "$PROJECT_ID" \
  --filter="bindings.members:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

### T006 — Create service account key + store as GitHub secret

```bash
PROJECT_ID=$(gcloud config get-value project)

# Create key locally
gcloud iam service-accounts keys create key.json \
  --iam-account="github-deployer@$PROJECT_ID.iam.gserviceaccount.com"

# Print so you can copy-paste into GitHub secret GCP_SA_KEY
cat key.json

# Delete local file immediately after copying
rm key.json
```

- **GitHub Secret created**: `GCP_SA_KEY` ✅/❌ (`yes`)
- **Key rotation policy**:
  - Rotation date: `2026-12-14` (rotate at least annually)

### T007 — Residential proxy account + URL

YouTube transcript access commonly fails from datacenter IPs (including Cloud Run). Use a residential proxy service.

- **Provider**: `bright data` (e.g. Bright Data / Smartproxy / Oxylabs)
- **PROXY_URL format**: `http://USER:PASS@HOST:PORT` (or provider-specific)
- **Important (URL encoding)**: if your USERNAME contains `@` (e.g. an email), encode it as `%40` inside the URL.
  - Example: `http://user%40example.com:PASSWORD@brd.superproxy.io:33335`
  - If your password contains special characters (e.g. `@`, `:`, `/`, `#`), you should URL-encode those too.
- **Stored in GitHub Secret**: `PROXY_URL` ✅/❌ (`yes`)

---

## Smoke test checklist (post-deploy)

Once you have a Cloud Run URL:

```bash
URL="REPLACE_ME"

# Health
curl -i "$URL/ok"

# Info (will require auth once API key auth is enabled)
curl -i -H "X-Api-Key: $LANGGRAPH_API_KEY" "$URL/info"
```

- `/ok` returns 200 ✅/❌
- `/info` returns 200 with auth ✅/❌


