# Research: Backend Production Deployment

**Feature**: 5-backend-deployment  
**Date**: December 13, 2025  

## Executive Summary

This document captures research findings for deploying the Recipe Agent backend to Google Cloud Run with GitHub Actions CI/CD and residential proxy integration for YouTube transcripts.

---

## 1. LangGraph CLI Docker Deployment

### Decision: Use `langgraph build` to create container image

**Rationale**: The LangGraph CLI provides a `build` command that creates a production-ready Docker image from `langgraph.json`. This is the official method for containerizing LangGraph applications.

**Command**:

```bash
langgraph build -t recipe-agent:latest
```

**What It Does**:
- Reads `langgraph.json` for dependencies and graph definition
- Creates a Docker image with all dependencies
- Exposes the LangGraph server on port 8000
- Includes health check endpoints

**Container Behavior**:
- Runs `langgraph serve` internally
- Exposes `/` for graph interactions
- Exposes `/ok` for health checks
- Environment variables passed at runtime

**Alternatives Considered**:
- Custom Dockerfile - More maintenance, less standardized
- LangSmith Platform - $40/month, too expensive for 10-20 users

**Reference**: https://langchain-ai.github.io/langgraph/concepts/deployment_options/

---

## 2. Google Cloud Run Deployment

### Decision: Deploy containerized LangGraph agent to Cloud Run

**Rationale**: Cloud Run is a serverless container platform with pay-per-use pricing. For low-traffic usage (10-20 users), costs stay under $10/month. Supports custom Docker images and environment variable configuration.

**Key Configuration**:

| Setting | Value | Reason |
|---------|-------|--------|
| Port | 8000 | LangGraph default |
| Memory | 512Mi - 1Gi | Agent + LLM client overhead |
| CPU | 1 | Sufficient for single-user requests |
| Concurrency | 10 | Multiple users, limited by LLM rate limits |
| Min instances | 0 | Cost optimization (cold start acceptable) |
| Max instances | 3 | Cost cap |
| Timeout | 300s | Long agent conversations |

**Required Environment Variables**:
```bash
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
DATABASE_URL=postgresql://...
LANGSMITH_API_KEY=lsv2-... (optional)
LANGSMITH_TRACING=true (optional)
PROXY_URL=http://... (for YouTube)
```

**Deployment Command**:
```bash
gcloud run deploy recipe-agent \
  --image gcr.io/PROJECT_ID/recipe-agent:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars "..."
```

**Cost Estimate**:
- Cloud Run: ~$0-5/month for 10-20 users (free tier covers most)
- Artifact Registry: ~$0.10/GB storage
- Network egress: ~$0.12/GB (minimal for API responses)

**Alternatives Considered**:
- Cloud Functions - Not suitable for container images
- GKE - Overkill, higher operational overhead
- AWS Lambda - Similar, but GCP preferred per user constraints

---

## 3. Google Artifact Registry

### Decision: Store container images in Artifact Registry

**Rationale**: Artifact Registry is the recommended image registry for GCP, replacing Container Registry. Integrates seamlessly with Cloud Run and GitHub Actions.

**Setup**:
```bash
# Create repository
gcloud artifacts repositories create recipe-agent \
  --repository-format=docker \
  --location=us-central1 \
  --description="Recipe Agent container images"

# Full image path
us-central1-docker.pkg.dev/PROJECT_ID/recipe-agent/recipe-agent:latest
```

**Authentication for CI/CD**:
- Use Workload Identity Federation (recommended) or Service Account JSON key
- GitHub Actions authenticates using `google-github-actions/auth`

---

## 4. GitHub Actions CI/CD

### Decision: Workflow triggered on push/merge to main

**Rationale**: GitHub Actions provides free CI/CD for public repos and 2000 minutes/month for private repos. Direct integration with GCP via official actions.

**Workflow Structure**:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write  # For Workload Identity

    steps:
      - uses: actions/checkout@v4
      
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/.../providers/github
          service_account: deployer@PROJECT_ID.iam.gserviceaccount.com
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
      
      - name: Configure Docker
        run: gcloud auth configure-docker us-central1-docker.pkg.dev
      
      - name: Install LangGraph CLI
        run: pip install langgraph-cli
      
      - name: Build container
        run: langgraph build -t us-central1-docker.pkg.dev/PROJECT_ID/recipe-agent/recipe-agent:${{ github.sha }}
      
      - name: Push to Artifact Registry
        run: docker push us-central1-docker.pkg.dev/PROJECT_ID/recipe-agent/recipe-agent:${{ github.sha }}
      
      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: recipe-agent
          region: us-central1
          image: us-central1-docker.pkg.dev/PROJECT_ID/recipe-agent/recipe-agent:${{ github.sha }}
```

**Required GitHub Secrets**:
| Secret | Description |
|--------|-------------|
| GCP_PROJECT_ID | Google Cloud project ID |
| GCP_SA_KEY | Service account JSON (if not using Workload Identity) |
| ANTHROPIC_API_KEY | LLM API key |
| TAVILY_API_KEY | Web search API key |
| DATABASE_URL | PostgreSQL connection string |
| PROXY_URL | Residential proxy URL |

**Alternatives Considered**:
- Cloud Build - GCP-native but adds complexity
- GitLab CI - User prefers GitHub
- Manual deployment - Error-prone, no automation

---

## 5. Residential Proxy for YouTube Transcripts

### Decision: Use residential proxy service (Bright Data, Smartproxy, or similar)

**Rationale**: YouTube blocks datacenter IPs (AWS, Azure, GCP) for transcript API access. Residential proxy services route requests through residential IP addresses, bypassing these restrictions.

**Integration Pattern**:

```python
# In youtube.py tool
import os
import httpx

def get_youtube_transcript(video_url_or_id: str) -> str:
    """Get transcript with proxy support for production."""
    proxy_url = os.getenv("PROXY_URL")
    
    if proxy_url:
        # Use proxy for transcript API
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._http_client import make_requests_session
        
        # Custom session with proxy
        proxies = {"http": proxy_url, "https": proxy_url}
        # ... configure transcript API to use proxy
    else:
        # Local development without proxy
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
```

**Proxy Service Options**:

| Service | Pricing | Notes |
|---------|---------|-------|
| Bright Data | $0.60/GB | Most reliable, best for production |
| Smartproxy | $0.50/GB | Good alternative |
| Oxylabs | $0.60/GB | Enterprise-grade |

**Estimated Cost**:
- YouTube transcript requests: ~10-50KB per request
- 100 requests/month: ~5MB = $0.003/month (negligible)

**Environment Variable**:
```bash
PROXY_URL=http://user:pass@proxy.service.com:port
```

**Fallback Strategy**:
- If proxy fails, return error message: "YouTube transcripts temporarily unavailable"
- Log error for debugging
- Agent can still use web search as alternative

---

## 6. Frontend Integration

### Decision: Deployed frontend connects via backend URL

**Rationale**: The Agent Chat UI (already deployed on Vercel) accepts a backend URL. Cloud Run provides a stable `*.run.app` URL.

**Connection Flow**:
1. User opens Agent Chat UI at Vercel URL
2. User enters Cloud Run backend URL: `https://recipe-agent-xxxxx.run.app`
3. Frontend connects to backend for LangGraph streaming
4. No CORS issues (Cloud Run defaults allow all origins)

**Frontend Configuration**:
- Backend URL entered in UI settings
- API key entered in UI (if required)
- Connection persists in browser storage

---

## 6.1 Authentication Layer (Production)

### Decision: Require `X-Api-Key` header on the deployed backend

**Rationale**: The Agent Chat UI already supports sending an API key and uses the `X-Api-Key` header when `apiKey` is provided. This is the simplest production gate (no OAuth/JWT) while preventing the backend URL from being fully public.

**How the frontend sends it**:
- When an API key is configured in the UI, requests include `X-Api-Key: <value>` (e.g. `GET /info`, streaming runs).

**How we will configure it**:
- **Backend (Cloud Run)**: set `LANGGRAPH_API_KEY` (shared secret).
- **Frontend (Agent Chat UI API passthrough / Vercel)**: the passthrough package uses `LANGSMITH_API_KEY` to inject `X-Api-Key` into requests. For our Cloud Run deployment, set `LANGSMITH_API_KEY` equal to the backend’s `LANGGRAPH_API_KEY` (it does not need to be an actual LangSmith key unless you’re using LangGraph Cloud).

**Alternatives Considered**:
- Cloud Run IAM (hard to integrate with a browser-based client)
- Full custom auth (OAuth/JWT) (more complexity than needed for 10–20 users)

---

## 7. Environment Variable Management

### Decision: Cloud Run environment variables + GitHub Secrets

**Rationale**: Sensitive values stored in GitHub Secrets, passed to Cloud Run at deployment time.

**Variable Categories**:

| Category | Variables | Storage |
|----------|-----------|---------|
| LLM Keys | ANTHROPIC_API_KEY, OPENAI_API_KEY | GitHub Secrets → Cloud Run env |
| Search | TAVILY_API_KEY | GitHub Secrets → Cloud Run env |
| Database | DATABASE_URL | GitHub Secrets → Cloud Run env |
| Authentication | LANGGRAPH_API_KEY | GitHub Secrets → Cloud Run env |
| Observability | LANGSMITH_API_KEY, LANGSMITH_TRACING | GitHub Secrets → Cloud Run env |
| Proxy | PROXY_URL | GitHub Secrets → Cloud Run env |

**Local Development**:
- Continue using `.env` file
- No changes to local workflow

---

## 8. Health Checks and Monitoring

### Decision: Use LangGraph built-in health endpoint + Cloud Run monitoring

**Rationale**: LangGraph exposes `/ok` health check endpoint. Cloud Run provides built-in monitoring dashboards.

**Health Check Configuration**:
```yaml
# Cloud Run automatically uses startup/liveness probes
# LangGraph /ok endpoint returns 200 when ready
```

**Monitoring Available**:
- Cloud Run dashboard: Request count, latency, errors
- Cloud Logging: Application logs
- LangSmith (optional): Agent traces, tool calls

---

## Dependencies Summary

**GCP Services**:
- Cloud Run (serverless containers)
- Artifact Registry (Docker images)
- Cloud Logging (logs)

**GitHub**:
- GitHub Actions (CI/CD)
- GitHub Secrets (sensitive values)

**External Services**:
- Residential proxy service (YouTube access)
- Neon PostgreSQL (database, already configured)
- LangSmith (optional observability)

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| How to containerize LangGraph? | `langgraph build` CLI command |
| Which GCP region? | us-central1 (low latency, good pricing) |
| Backend authentication method? | Require `X-Api-Key` header; validate against `LANGGRAPH_API_KEY` |
| How to handle YouTube blocking? | Residential proxy service |
| CORS configuration? | Cloud Run defaults allow all origins |

---

*Research complete. Ready for implementation planning.*

