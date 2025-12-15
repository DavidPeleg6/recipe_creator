     1|# Backend Deployment Runbook (Cloud Run + CI/CD)
     2|
     3|This runbook is the **single source of truth** for production deployment details: project IDs, regions, service URL, secrets checklist, and the one-time GCP setup commands.
     4|
     5|---
     6|
     7|## Deployment Facts (fill these in)
     8|
     9|- **GCP Project ID**: `gen-lang-client-0778161380` (note: project **name** is “recipe-agent”)
    10|- **Billing enabled**: `yes` (yes/no + date confirmed)
    11|- **Region**: `us-central1`
    12|- **Artifact Registry repo**: `recipe-agent` (location: `us-central1`)
    13|- **Cloud Run service name**: `recipe-agent`
    14|- **Cloud Run URL**: `REPLACE_ME` (e.g. `https://recipe-agent-xxxxx-uc.a.run.app`)
    15|- **GitHub repo**: `https://github.com/DavidPeleg6/recipe_creator/tree/main/recipe_creator`
    16|
    17|---
    18|
    19|## Secrets Checklist (do not commit secrets)
    20|
    21|### GitHub Actions secrets (Repository Settings → Secrets and variables → Actions)
    22|
    23|- `GCP_PROJECT_ID` = **GCP Project ID**
    24|- `GCP_SA_KEY` = **service account JSON key** (entire JSON document)
    25|- `ANTHROPIC_API_KEY`
    26|- `TAVILY_API_KEY`
    27|- `DATABASE_URL`
    28|- `LANGGRAPH_API_KEY` (shared secret used as `X-Api-Key`)
    29|- `LANGSMITH_API_KEY` (optional; only if you use LangSmith)
    30|- `PROXY_URL` (residential proxy, required for YouTube transcripts in Cloud Run)
    31|
    32|#### Where each secret is used
    33|
    34|| Secret | Used in | Purpose |
    35||---|---|---|
    36|| `GCP_PROJECT_ID` | `.github/workflows/deploy.yml` (`env.PROJECT_ID`) | Selects the Artifact Registry image path + target GCP project |
    37|| `GCP_SA_KEY` | `.github/workflows/deploy.yml` (`google-github-actions/auth@v2`) | Authenticates GitHub Actions to GCP |
    38|| `ANTHROPIC_API_KEY` | `.github/workflows/deploy.yml` → Cloud Run `env_vars` | LLM provider key used by the backend |
    39|| `TAVILY_API_KEY` | `.github/workflows/deploy.yml` → Cloud Run `env_vars` | Web search tool key |
    40|| `DATABASE_URL` | `.github/workflows/deploy.yml` → Cloud Run `env_vars` | Neon Postgres connection string |
    41|| `LANGGRAPH_API_KEY` | `.github/workflows/deploy.yml` → Cloud Run `env_vars` | Backend API key (validated against `X-Api-Key` in Phase 3) |
    42|| `LANGSMITH_API_KEY` | `.github/workflows/deploy.yml` → Cloud Run `env_vars` | Optional tracing/observability |
    43|| `PROXY_URL` | `.github/workflows/deploy.yml` → Cloud Run `env_vars` | Residential proxy used by the YouTube transcript tool |
    44|
    45|### Cloud Run runtime env vars
    46|
    47|These should be set via GitHub Actions deploy (preferred) or `gcloud run deploy --set-env-vars` (manual):
    48|
    49|- `ANTHROPIC_API_KEY`
    50|- `TAVILY_API_KEY`
    51|- `DATABASE_URL`
    52|- `LANGGRAPH_API_KEY`
    53|- `LANGSMITH_API_KEY` (optional)
    54|- `LANGSMITH_TRACING=true` (optional)
    55|- `PROXY_URL` (required for YouTube transcripts in Cloud Run)
    56|
    57|---
    58|
    59|## Manual Deployment Command (Reference)
    60|
    61|To deploy manually (e.g. for testing), use the following command structure. Ensure `LANGGRAPH_API_KEY` is set.
    62|
    63|```bash
    64|# Assumes image is already built and pushed to Artifact Registry
    65|IMAGE="us-central1-docker.pkg.dev/gen-lang-client-0778161380/recipe-agent/recipe-agent:latest"
    66|
    67|gcloud run deploy recipe-agent \
    68|  --image "$IMAGE" \
    69|  --region us-central1 \
    70|  --allow-unauthenticated \
    71|  --set-env-vars="LANGGRAPH_API_KEY=your-secret-key,ANTHROPIC_API_KEY=...,TAVILY_API_KEY=...,DATABASE_URL=...,PROXY_URL=..."
    72|```
    73|
    74|Note: `--allow-unauthenticated` makes the Cloud Run URL public, but the application code (`recipe_creator/auth.py`) enforces the `X-Api-Key` requirement.
    75|
    76|---
    77|
    78|## Phase 1 — One-time GCP setup (manual)
    79|
    80|> All commands below are intended to be run on your machine with `gcloud` installed and authenticated.
