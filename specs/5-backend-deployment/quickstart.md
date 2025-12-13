# Quickstart: Backend Production Deployment

Deploy the Recipe Agent backend to Google Cloud Run in 30 minutes.

---

## Prerequisites

- Google Cloud account with billing enabled
- GitHub repository with Actions enabled
- Admin access to repository settings (for secrets)
- Residential proxy service account (Bright Data, Smartproxy, etc.)
- API keys: Anthropic, Tavily, LangSmith (optional)
- Database URL from Neon PostgreSQL

---

## Quick Setup

### 1. GCP Setup (10 minutes)

```bash
# Install gcloud CLI if needed
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set project (existing)
gcloud config set project recipe-agent

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# Create Artifact Registry repository
gcloud artifacts repositories create recipe-agent \
  --repository-format=docker \
  --location=us-central1

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

# Create key (copy contents, then delete file!)
gcloud iam service-accounts keys create key.json \
  --iam-account=github-deployer@$PROJECT_ID.iam.gserviceaccount.com
cat key.json  # Copy this for GitHub Secrets
rm key.json   # Delete after copying!
```

### 2. GitHub Secrets (5 minutes)

Go to: `Repository Settings > Secrets and variables > Actions`

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_SA_KEY` | Contents of key.json (entire JSON) |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `TAVILY_API_KEY` | Your Tavily API key |
| `DATABASE_URL` | PostgreSQL connection string from Neon |
| `LANGGRAPH_API_KEY` | Shared API key for backend auth (sent as `X-Api-Key`) |
| `LANGSMITH_API_KEY` | LangSmith API key (optional) |
| `PROXY_URL` | Residential proxy URL (e.g., `http://user:pass@proxy.com:port`) |

### 3. Create Workflow File (5 minutes)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1
  SERVICE_NAME: recipe-agent
  REGISTRY: us-central1-docker.pkg.dev

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - uses: google-github-actions/setup-gcloud@v2
      
      - run: gcloud auth configure-docker ${{ env.REGISTRY }} --quiet
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - run: pip install langgraph-cli
      
      - run: |
          langgraph build -t ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/recipe-agent/${{ env.SERVICE_NAME }}:${{ github.sha }}
      
      - run: |
          docker push ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/recipe-agent/${{ env.SERVICE_NAME }}:${{ github.sha }}
      
      - uses: google-github-actions/deploy-cloudrun@v2
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
```

### 4. Deploy (5 minutes)

```bash
# Commit and push
git add .github/workflows/deploy.yml
git commit -m "Add Cloud Run deployment workflow"
git push origin main
```

Watch the deployment at: `https://github.com/YOUR_ORG/recipe_creator/actions`

### 5. Get Deployment URL

After successful deployment:

```bash
# Get URL from GCP
gcloud run services describe recipe-agent \
  --region=us-central1 \
  --format='value(status.url)'
```

Or check the GitHub Actions log for "Deployed to: https://..."

---

## Connect Frontend

1. Open Agent Chat UI at your Vercel URL
2. Click settings/configuration
3. Enter the Cloud Run URL (e.g., `https://recipe-agent-xxxxx-uc.a.run.app`)
4. Enter your API key: set it to the same value as `LANGGRAPH_API_KEY` (it will be sent as `X-Api-Key`)
5. Start chatting!

---

## Verify Deployment

```bash
# Health check
curl https://YOUR_CLOUD_RUN_URL/ok

# Should return: {"status": "ok"}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Workflow fails at authentication | Check GCP_SA_KEY is complete JSON, not truncated |
| Container build fails | Ensure langgraph.json is valid |
| Deployment succeeds but 502 errors | Check Cloud Run logs: `gcloud logs read --service=recipe-agent` |
| YouTube transcripts fail | Verify PROXY_URL is correct and proxy service is active |
| Frontend can't connect | Verify URL is correct, check browser console for CORS errors |

---

## Cost Monitoring

Check your spending:
- GCP Console: https://console.cloud.google.com/billing
- Cloud Run: https://console.cloud.google.com/run

Expected: < $10/month for 10-20 users

---

## Rollback

If something breaks:

```bash
# List revisions
gcloud run revisions list --service=recipe-agent --region=us-central1

# Rollback to previous
gcloud run services update-traffic recipe-agent \
  --region=us-central1 \
  --to-revisions=PREVIOUS_REVISION=100
```

---

*Happy deploying! 🚀*

