# Data Model: Backend Production Deployment

**Feature**: 5-backend-deployment  
**Date**: December 13, 2025  

## Overview

This document defines the configuration entities for deploying the Recipe Agent backend to Google Cloud Run. These are primarily configuration files rather than runtime data models.

---

## Configuration Entities

### 1. GitHub Actions Workflow

**File**: `.github/workflows/deploy.yml`

The workflow configuration defines the CI/CD pipeline.

**Structure**:

```yaml
name: string                    # Workflow display name
on:                             # Trigger events
  push:
    branches: string[]          # Branch triggers (e.g., [main])
  workflow_dispatch: {}         # Manual trigger option

env:                            # Workflow-level environment variables
  PROJECT_ID: string            # GCP project ID (from secrets)
  REGION: string                # GCP region (us-central1)
  SERVICE_NAME: string          # Cloud Run service name
  REGISTRY: string              # Artifact Registry URL

jobs:
  deploy:
    runs-on: string             # Runner type (ubuntu-latest)
    steps: Step[]               # Build and deploy steps
```

**Required Secrets**:

| Secret | Type | Required | Description |
|--------|------|----------|-------------|
| `GCP_PROJECT_ID` | string | Yes | Google Cloud project ID |
| `GCP_SA_KEY` | JSON string | Yes | Service account credentials |
| `ANTHROPIC_API_KEY` | string | Yes | LLM API key |
| `TAVILY_API_KEY` | string | Yes | Web search API key |
| `DATABASE_URL` | string | Yes | PostgreSQL connection string |
| `LANGGRAPH_API_KEY` | string | Yes | Shared API key required on requests (`X-Api-Key`) |
| `LANGSMITH_API_KEY` | string | No | Observability API key |
| `PROXY_URL` | string | Yes | Residential proxy URL |

---

### 2. Cloud Run Service Configuration

**Managed via**: `gcloud run deploy` flags and GitHub Actions workflow

**Configuration Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `service` | string | `recipe-agent` | Cloud Run service name |
| `region` | string | `us-central1` | GCP region |
| `image` | string | - | Container image URL |
| `port` | integer | `8000` | Container port |
| `memory` | string | `1Gi` | Memory allocation |
| `cpu` | integer | `1` | CPU allocation |
| `timeout` | integer | `300` | Request timeout (seconds) |
| `concurrency` | integer | `10` | Max concurrent requests |
| `min-instances` | integer | `0` | Minimum instances |
| `max-instances` | integer | `3` | Maximum instances |
| `allow-unauthenticated` | boolean | `true` | Public access |

**Runtime Environment Variables**:

| Variable | Source | Description |
|----------|--------|-------------|
| `ANTHROPIC_API_KEY` | GitHub Secret | LLM API key |
| `TAVILY_API_KEY` | GitHub Secret | Web search API key |
| `DATABASE_URL` | GitHub Secret | PostgreSQL connection |
| `LANGGRAPH_API_KEY` | GitHub Secret | Required request auth (`X-Api-Key`) |
| `LANGSMITH_API_KEY` | GitHub Secret | Observability (optional) |
| `LANGSMITH_TRACING` | Hardcoded | Enable tracing |
| `PROXY_URL` | GitHub Secret | YouTube proxy |

---

### 3. Artifact Registry Repository

**Configuration**:

| Property | Value | Description |
|----------|-------|-------------|
| `name` | `recipe-agent` | Repository name |
| `location` | `us-central1` | GCP region |
| `format` | `docker` | Image format |

**Image Path Format**:
```
us-central1-docker.pkg.dev/{PROJECT_ID}/recipe-agent/{SERVICE_NAME}:{TAG}
```

**Tagging Strategy**:
- `git SHA` for each deployment (immutable)
- `latest` not used (avoid ambiguity)

---

### 4. Service Account

**Name**: `github-deployer`

**IAM Roles**:

| Role | Purpose |
|------|---------|
| `roles/run.admin` | Deploy to Cloud Run |
| `roles/artifactregistry.writer` | Push images |
| `roles/iam.serviceAccountUser` | Act as service account |

**Key Management**:
- JSON key stored in GitHub Secrets as `GCP_SA_KEY`
- Key rotated annually (manual process)

---

### 5. LangGraph Configuration

**File**: `langgraph.json` (existing, no changes)

```json
{
  "dependencies": ["..."],
  "graphs": {
    "recipe_creator": "recipe_creator.agent:graph"
  },
  "env": ".env"
}
```

**Container Build**:
- `langgraph build` reads this file
- Creates container exposing port 8000
- Includes all dependencies

---

## Entity Relationships

```
GitHub Actions Workflow
    ├── reads → GitHub Secrets (credentials, API keys)
    ├── uses → Service Account (GCP authentication)
    ├── pushes → Artifact Registry (container images)
    └── deploys → Cloud Run Service

Cloud Run Service
    ├── pulls → Artifact Registry (container image)
    ├── runs → LangGraph Container
    ├── connects → Neon PostgreSQL (database)
    ├── calls → Anthropic/OpenAI (LLM)
    ├── calls → Tavily (web search)
    ├── calls → YouTube API via Proxy
    └── serves → Agent Chat Frontend
```

---

## Configuration Flow

```
Developer pushes to main
    ↓
GitHub Actions triggers
    ↓
Authenticate to GCP (Service Account)
    ↓
Build container (langgraph build)
    ↓
Push to Artifact Registry
    ↓
Deploy to Cloud Run (with env vars from secrets)
    ↓
Cloud Run pulls image, starts container
    ↓
LangGraph server ready on port 8000
    ↓
Frontend connects via *.run.app URL
```

---

## File Locations

| Entity | Location | Format |
|--------|----------|--------|
| GitHub Workflow | `.github/workflows/deploy.yml` | YAML |
| GitHub Secrets | GitHub Settings UI | Key-value |
| LangGraph Config | `langgraph.json` | JSON |
| Python Package | `pyproject.toml` | TOML |
| YouTube Tool | `recipe_creator/tools/youtube.py` | Python |

---

## Validation Rules

**GitHub Secrets**:
- All required secrets must be set before first deployment
- `GCP_SA_KEY` must be valid JSON with `type: "service_account"`
- `DATABASE_URL` must be valid PostgreSQL connection string
- `PROXY_URL` must include authentication (user:pass@host:port)

**Cloud Run**:
- Port must match LangGraph default (8000)
- Memory must be ≥512Mi for agent workload
- Timeout must be ≥60s for LLM calls

**Container Image**:
- Must be built with `langgraph build`
- Must include all dependencies from `langgraph.json`

---

## Notes

- **No new Pydantic models needed** - this is infrastructure configuration
- **Existing models unchanged** - Recipe, Ingredient, etc. remain the same
- **Database schema unchanged** - SavedRecipe table already exists in Neon
- **LangGraph API unchanged** - Frontend compatibility maintained

---

*Data model complete. Configuration entities defined for deployment infrastructure.*

