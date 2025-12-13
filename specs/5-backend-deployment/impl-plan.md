# Implementation Plan: Backend Production Deployment

**Feature**: 5-backend-deployment  
**Date**: December 13, 2025  
**Status**: Ready for Implementation  

---

## Overview

Deploy the Recipe Agent backend to Google Cloud Run with GitHub Actions CI/CD. Integrate residential proxy for YouTube transcript access. Enable the deployed Agent Chat frontend to connect to the backend.

---

## Technical Stack

| Component | Technology | Version/Details |
|-----------|------------|-----------------|
| Container Runtime | Google Cloud Run | Managed |
| Container Registry | Artifact Registry | us-central1 |
| Container Build | LangGraph CLI | `langgraph build` |
| CI/CD | GitHub Actions | v4 actions |
| GCP Auth | Workload Identity / SA Key | v2 auth action |
| Backend Auth | API key header | Require `X-Api-Key`, validate against `LANGGRAPH_API_KEY` |
| YouTube Proxy | Residential Proxy Service | Bright Data/Smartproxy |
| Database | Neon PostgreSQL | Already configured |

---

## Project Structure (New Files)

```
recipe_creator/
├── .github/
│   └── workflows/
│       └── deploy.yml           # GitHub Actions workflow
├── recipe_creator/
│   └── tools/
│       └── youtube.py           # Modified: proxy support
├── langgraph.json               # Existing: no changes needed
├── pyproject.toml               # Existing: no changes needed
└── specs/5-backend-deployment/
    ├── spec.md
    ├── research.md
    ├── impl-plan.md             # This file
    ├── data-model.md
    └── quickstart.md
```

---

## Implementation Tasks

### Phase 1: GCP Setup (Manual, One-Time)

#### Task 1.1: Select GCP Project (use existing `recipe-agent`)

```bash
# Use existing project
gcloud config set project recipe-agent

# (Optional) Verify
gcloud config get-value project

# Enable billing (required for Cloud Run)
# Done via GCP Console: https://console.cloud.google.com/billing
```

#### Task 1.2: Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com
```

#### Task 1.3: Create Artifact Registry Repository

```bash
gcloud artifacts repositories create recipe-agent \
  --repository-format=docker \
  --location=us-central1 \
  --description="Recipe Agent container images"
```

#### Task 1.4: Create Service Account for CI/CD

```bash
# Create service account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"

# Grant permissions
PROJECT_ID=$(gcloud config get-value project)

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create JSON key (store securely!)
gcloud iam service-accounts keys create key.json \
  --iam-account=github-deployer@$PROJECT_ID.iam.gserviceaccount.com

# IMPORTANT: Add key.json contents to GitHub Secrets as GCP_SA_KEY
# Then delete the local file: rm key.json
```

---

### Phase 2: GitHub Actions Workflow

#### Task 2.1: Create Workflow File

**File**: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
  workflow_dispatch:  # Manual trigger option

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1
  SERVICE_NAME: recipe-agent
  REGISTRY: us-central1-docker.pkg.dev

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
      
      - name: Configure Docker for Artifact Registry
        run: gcloud auth configure-docker ${{ env.REGISTRY }} --quiet
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install LangGraph CLI
        run: pip install langgraph-cli
      
      - name: Build container image
        run: |
          langgraph build -t ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/recipe-agent/${{ env.SERVICE_NAME }}:${{ github.sha }}
      
      - name: Push to Artifact Registry
        run: |
          docker push ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/recipe-agent/${{ env.SERVICE_NAME }}:${{ github.sha }}
      
      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: ${{ env.SERVICE_NAME }}
          region: ${{ env.REGION }}
          image: ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/recipe-agent/${{ env.SERVICE_NAME }}:${{ github.sha }}
          env_vars: |
            ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}
            TAVILY_API_KEY=${{ secrets.TAVILY_API_KEY }}
            DATABASE_URL=${{ secrets.DATABASE_URL }}
            LANGGRAPH_API_KEY=${{ secrets.LANGGRAPH_API_KEY }}
            LANGSMITH_API_KEY=${{ secrets.LANGSMITH_API_KEY }}
            LANGSMITH_TRACING=true
            PROXY_URL=${{ secrets.PROXY_URL }}
          flags: |
            --port=8000
            --memory=1Gi
            --cpu=1
            --timeout=300
            --concurrency=10
            --min-instances=0
            --max-instances=3
            --allow-unauthenticated
      
      - name: Show deployment URL
        run: |
          URL=$(gcloud run services describe ${{ env.SERVICE_NAME }} --region=${{ env.REGION }} --format='value(status.url)')
          echo "🚀 Deployed to: $URL"
          echo "DEPLOYMENT_URL=$URL" >> $GITHUB_OUTPUT
```

#### Task 2.2: Add GitHub Secrets

Add these secrets to GitHub repository settings (`Settings > Secrets and variables > Actions`):

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud project ID | `recipe-agent-prod` |
| `GCP_SA_KEY` | Service account JSON key | `{"type": "service_account", ...}` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |
| `TAVILY_API_KEY` | Tavily API key | `tvly-...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `LANGGRAPH_API_KEY` | Shared API key for backend auth (`X-Api-Key`) | `some-long-random-secret` |
| `LANGSMITH_API_KEY` | LangSmith API key (optional) | `lsv2-...` |
| `PROXY_URL` | Residential proxy URL | `http://user:pass@proxy.com:port` |

---

### Phase 3: YouTube Proxy Integration

#### Task 3.1: Update YouTube Tool for Proxy Support

**File**: `recipe_creator/tools/youtube.py`

```python
"""YouTube transcript tool with residential proxy support."""

import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


def get_youtube_transcript(video_url_or_id: str) -> str:
    """Get the transcript from a YouTube video to extract recipe information.
    
    Use this tool when a user wants to get a recipe from a specific YouTube video,
    or when you need to analyze cooking tutorial content.
    
    Args:
        video_url_or_id: YouTube video URL (any format) or video ID
        
    Returns:
        Full transcript text from the video, or error message if unavailable
    """
    video_id = extract_video_id(video_url_or_id)
    
    try:
        # Get proxy URL from environment (set in Cloud Run, empty locally)
        proxy_url = os.getenv("PROXY_URL")
        
        if proxy_url:
            # Production: Use residential proxy to bypass datacenter IP blocking
            transcript = _get_transcript_with_proxy(video_id, proxy_url)
        else:
            # Local development: Direct access (works from residential IPs)
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        full_text = " ".join([entry["text"] for entry in transcript])
        return f"Transcript for video {video_id}:\n\n{full_text}"
        
    except TranscriptsDisabled:
        return f"Transcripts are disabled for video {video_id}"
    except NoTranscriptFound:
        return f"No transcript available for video {video_id}"
    except Exception as e:
        error_msg = str(e)
        if "blocked" in error_msg.lower() or "403" in error_msg:
            return f"YouTube access blocked. Try using web search for recipe information instead."
        return f"Error retrieving transcript: {error_msg}"


def _get_transcript_with_proxy(video_id: str, proxy_url: str) -> list[dict]:
    """Retrieve transcript using residential proxy."""
    import httpx
    
    # Configure proxy for requests
    proxies = {"http://": proxy_url, "https://": proxy_url}
    
    # youtube-transcript-api uses requests internally
    # We need to configure it to use our proxy
    import requests
    
    # Create a session with proxy
    session = requests.Session()
    session.proxies = {"http": proxy_url, "https": proxy_url}
    
    # Monkey-patch the API to use our session (temporary workaround)
    # The library doesn't have native proxy support
    original_get = requests.get
    
    def proxied_get(*args, **kwargs):
        kwargs['proxies'] = {"http": proxy_url, "https": proxy_url}
        return original_get(*args, **kwargs)
    
    try:
        requests.get = proxied_get
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    finally:
        requests.get = original_get


def extract_video_id(url_or_id: str) -> str:
    """Extract YouTube video ID from URL or return as-is if already an ID."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([^&\s]+)',
        r'(?:youtu\.be\/)([^\?\s]+)',
        r'(?:youtube\.com\/embed\/)([^\?\s]+)',
        r'(?:youtube\.com\/shorts\/)([^\?\s]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id  # Assume it's already a video ID
```

---

#### Task 3.2: Enforce API Key Authentication on Deployed Backend

**Goal**: Require `X-Api-Key` on production requests and validate it against `LANGGRAPH_API_KEY`.

**Why**: The Agent Chat UI already sends `X-Api-Key` when an API key is configured. This prevents unauthenticated access to your Cloud Run URL even if Cloud Run is set to `--allow-unauthenticated`.

**Implementation note**: Implement this using LangGraph’s Python authentication hooks (custom auth) so it applies to **all routes**, including streaming endpoints.

---

### Phase 4: Initial Deployment (Manual Test)

#### Task 4.1: Test Local Container Build

```bash
# Install LangGraph CLI if not installed
pip install langgraph-cli

# Build container locally
langgraph build -t recipe-agent:test

# Test locally (optional)
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e TAVILY_API_KEY=$TAVILY_API_KEY \
  -e DATABASE_URL=$DATABASE_URL \
  recipe-agent:test
```

#### Task 4.2: Manual First Deployment

```bash
# Set variables
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
SERVICE_NAME=recipe-agent
IMAGE=us-central1-docker.pkg.dev/$PROJECT_ID/recipe-agent/$SERVICE_NAME:v1

# Build and push
langgraph build -t $IMAGE
docker push $IMAGE

# Deploy
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --region $REGION \
  --platform managed \
  --port 8000 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --allow-unauthenticated \
  --set-env-vars "ANTHROPIC_API_KEY=...,TAVILY_API_KEY=...,DATABASE_URL=..."
```

#### Task 4.3: Verify Deployment

```bash
# Get deployment URL
URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo "Backend URL: $URL"

# Test health endpoint
curl $URL/ok

# Test from frontend
# 1. Open Agent Chat UI at Vercel URL
# 2. Enter backend URL in settings
# 3. Send test message: "How do I make a mojito?"
```

---

### Phase 5: CI/CD Verification

#### Task 5.1: Test Automatic Deployment

```bash
# Make a small change and push
git add .
git commit -m "test: verify CI/CD pipeline"
git push origin main

# Watch GitHub Actions
# Go to: https://github.com/YOUR_ORG/recipe_creator/actions
```

#### Task 5.2: Verify YouTube Proxy

```bash
# From deployed backend (via frontend or direct API)
# Share a YouTube cooking video URL
# Verify transcript is retrieved successfully
```

---

## Acceptance Criteria Mapping

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| FR-1: Cloud Run Deployment | `deploy.yml` workflow + Cloud Run | Planned |
| FR-2: Frontend Integration | Public Cloud Run URL + CORS defaults | Planned |
| FR-3: Environment Configuration | GitHub Secrets → Cloud Run env vars | Planned |
| FR-4: YouTube Proxy | `youtube.py` with PROXY_URL | Planned |
| FR-5: GitHub Actions CI/CD | `.github/workflows/deploy.yml` | Planned |
| Backend Authentication | Require `X-Api-Key` == `LANGGRAPH_API_KEY` | Planned |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Cold start latency | Acceptable for 10-20 users; min-instances=0 for cost |
| Proxy service failure | Graceful error message, suggest web search alternative |
| GCP quota limits | Default quotas sufficient for low traffic |
| GitHub Actions minutes | Free for public repos, 2000 min/month for private |
| Secret exposure | All secrets in GitHub Secrets, never in code |

---

## Cost Breakdown

| Service | Estimated Monthly Cost |
|---------|----------------------|
| Cloud Run | $0-5 (free tier covers most) |
| Artifact Registry | $0.10 (minimal storage) |
| Residential Proxy | $0.01-0.10 (per-request, low volume) |
| **Total** | **< $10/month** |

---

## Testing Strategy

Manual testing is sufficient for personal use:

1. **Deployment Test**: Push to main, verify workflow succeeds
2. **Health Check Test**: `curl $URL/ok` returns 200
3. **Frontend Test**: Connect Agent Chat UI, send test message
4. **Tool Test**: Request recipe, verify web search works
5. **YouTube Test**: Share video URL, verify transcript retrieval
6. **Database Test**: Save a recipe, verify persistence

---

## Rollback Strategy

Manual rollback using Cloud Run revision history:

```bash
# List revisions
gcloud run revisions list --service=$SERVICE_NAME --region=$REGION

# Rollback to previous revision
gcloud run services update-traffic $SERVICE_NAME \
  --region=$REGION \
  --to-revisions=REVISION_NAME=100
```

---

## Next Steps

1. Run `/speckit.tasks` to generate detailed task list
2. Execute Phase 1 (GCP Setup) manually
3. Create GitHub workflow file
4. Update YouTube tool for proxy support
5. Push to main to trigger first deployment
6. Test end-to-end from Agent Chat UI

---

*Implementation plan complete. Ready for task breakdown.*

