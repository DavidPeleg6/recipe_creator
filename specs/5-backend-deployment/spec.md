# Feature Specification: Backend Production Deployment

**Feature ID**: 5-backend-deployment  
**Created**: December 11, 2025  
**Status**: Draft  

## Overview

### Problem Statement

The Recipe Agent backend is currently only accessible locally during development. The previously deployed chat frontend (Agent Chat UI on Vercel) requires a publicly accessible backend URL to function. Additionally, the YouTube transcript service is geo-restricted and requires VPN access to work reliably. Without automated deployment pipelines, manual deployments create friction and risk inconsistent production states.

### Solution Summary

Deploy the Recipe Agent backend to Google Cloud Run as a containerized service and obtain a public deployment URL that the existing Agent Chat frontend can connect to. Configure the deployment environment to ensure YouTube transcript functionality works (via VPN or proxy to bypass datacenter IP restrictions). Implement GitHub Actions CI/CD to automatically redeploy the backend whenever code is pushed or merged to the main branch.

### Target Users

- **Primary User**: Recipe Agent developer who needs to make the backend accessible to the deployed frontend
- **Secondary User**: End users accessing the Recipe Agent through the deployed Agent Chat UI

## Functional Requirements

### FR-1: Google Cloud Run Deployment

The Recipe Agent backend shall be deployed to Google Cloud Run as a containerized service.

**Acceptance Criteria**:
- Agent is deployed to Google Cloud Run successfully
- A public deployment URL is generated and accessible
- Deployment URL follows Cloud Run URL format (*.run.app)
- Agent responds to requests from external clients
- All existing tools (web search, YouTube, recipe storage) function in the deployed environment
- Container image is built and stored in Google Container Registry or Artifact Registry

### FR-2: Frontend Integration

The deployed backend shall be compatible with the existing Agent Chat frontend.

**Acceptance Criteria**:
- The deployment URL can be entered in the deployed Agent Chat UI
- Chat messages sent from the frontend reach the backend
- Backend responses stream correctly to the frontend
- Tool calls are displayed properly in the frontend UI
- Conversation context is maintained within sessions
- No CORS or connectivity issues between frontend and backend
- Backend requires an API key for production requests via `X-Api-Key` header

### FR-3: Environment Configuration

The deployment shall have all required environment variables properly configured.

**Acceptance Criteria**:
- API keys (Anthropic/OpenAI, Tavily) are securely configured in Cloud Run environment
- Database connection string (PostgreSQL/Neon) is configured
- LangSmith API key configured for tracing/observability (optional)
- LangGraph server API key configured for request authentication (`LANGGRAPH_API_KEY`, required)
- Environment variables are not exposed in code or logs
- Local development continues to work with local `.env` file

### FR-4: YouTube Transcript Service Availability

The YouTube transcript tool shall function correctly in the production environment despite datacenter IP restrictions.

**Acceptance Criteria**:
- YouTube transcript requests succeed for videos with available transcripts
- Error messages are returned appropriately for videos without transcripts
- Residential proxy service (Bright Data, Smartproxy, or similar) configured to bypass datacenter IP blocking
- Service degradation is handled gracefully if YouTube access is temporarily unavailable

### FR-5: GitHub Actions CI/CD Pipeline

The repository shall have automated deployment configured via GitHub Actions.

**Acceptance Criteria**:
- GitHub Actions workflow triggers on push to main branch
- GitHub Actions workflow triggers on merge to main branch (pull request merge)
- Workflow builds container image and deploys to Google Cloud Run
- Deployment succeeds without manual intervention
- Workflow provides clear success/failure feedback
- Deployment secrets (GCP credentials) are stored securely in GitHub repository settings

## User Scenarios & Testing

### Scenario 1: Initial Backend Deployment

**Given** a developer has configured Google Cloud credentials  
**When** they manually trigger deployment or push to main  
**Then** the backend is deployed to Cloud Run and a public URL is provided.

### Scenario 2: Frontend Connects to Deployed Backend

**Given** the backend is deployed to Google Cloud Run  
**When** a user opens the deployed Agent Chat UI and enters the backend URL  
**Then** the connection succeeds and the chat interface is ready for use.

### Scenario 3: End-to-End Recipe Request

**Given** the frontend is connected to the deployed backend  
**When** a user asks "How do I make a margarita?"  
**Then** the backend processes the request, calls relevant tools, and streams the response back to the frontend.

### Scenario 4: YouTube Transcript Retrieval

**Given** the backend is deployed with VPN/network configuration  
**When** a user shares a YouTube cooking video URL  
**Then** the backend retrieves the transcript and uses it to extract recipe information.

### Scenario 5: Automatic Redeployment on Code Push

**Given** the GitHub Actions workflow is configured  
**When** a developer pushes code changes to the main branch  
**Then** the workflow automatically deploys the updated backend without manual intervention.

### Scenario 6: Pull Request Merge Triggers Deployment

**Given** the GitHub Actions workflow is configured  
**When** a pull request is merged to the main branch  
**Then** the workflow automatically deploys the updated backend.

## Success Criteria

| Criterion | Target | Measurement Method |
|-----------|--------|-------------------|
| Deployment Accessible | Backend reachable via public URL | HTTP request to deployment URL succeeds |
| Frontend Compatibility | Chat UI connects and functions | Complete conversation from deployed frontend |
| YouTube Tool Works | Transcripts retrieved successfully | Request transcript for known video with captions |
| CI/CD Functional | Auto-deploy on push/merge to main | Push to main triggers successful deployment |
| Response Time | Agent responds within 15 seconds | Timed request from frontend |
| Deployment Reliability | 95% uptime | Cloud Run monitoring dashboard |
| Cost Efficiency | Monthly cost under $10 for low traffic | GCP billing dashboard |

## Key Entities

### Deployment Configuration
- Google Cloud project
- Cloud Run service name/identifier
- Container image repository (Artifact Registry)
- Public deployment URL (*.run.app)
- Environment variables (API keys, database URL)
- Authentication key (`LANGGRAPH_API_KEY`) required for production access

### GitHub Actions Workflow
- Workflow file (`.github/workflows/deploy.yml`)
- Trigger events (push, pull_request merged to main)
- GCP service account credentials (JSON key or Workload Identity)
- GitHub repository secrets

### Network Configuration
- Residential proxy service (Bright Data, Smartproxy, or similar) for YouTube transcript API access
- Proxy credentials configured as environment variables

## Assumptions

1. The Recipe Agent can be containerized and served as an HTTP service (compatible with Cloud Run)
2. The existing PostgreSQL database (Neon) from spec 4-prod-deployment-infra is configured and accessible
3. GitHub repository is hosted on GitHub.com with Actions enabled
4. Developer has admin access to GitHub repository settings for secrets
5. Developer has a Google Cloud account with billing enabled
6. A residential proxy service (Bright Data, Smartproxy, or similar) is available and can be integrated with the YouTube transcript tool
7. The deployed Agent Chat frontend is already accessible at its Vercel URL
8. Cloud Run free tier or minimal usage keeps costs under $10/month for 10-20 users

## Out of Scope

- Frontend deployment (already deployed per spec 3-agent-chat-frontend)
- Database migration or setup (handled in spec 4-prod-deployment-infra)
- Custom domain configuration for the backend
- Advanced auto-scaling configuration beyond Cloud Run defaults
- Monitoring and alerting setup beyond Cloud Run defaults
- Rollback automation (manual rollback acceptable initially)
- Multi-environment deployments (staging, production) - single production deployment only

## Technical Constraints

*Note: These are user-specified implementation preferences.*

- **Deployment Platform**: Google Cloud Run (chosen over LangSmith due to cost - $40/month vs pay-per-use)
- **CI/CD Platform**: GitHub Actions
- **Trigger Events**: Push to main branch, pull request merge to main
- **YouTube Access**: Residential proxy service (Bright Data, Smartproxy, or similar) to bypass datacenter IP restrictions (YouTube blocks AWS/Azure/GCP IPs)
- **Frontend**: Existing deployed Agent Chat UI (expects LangGraph-compatible backend URL)
- **Authentication**: Require `X-Api-Key` header on requests to deployed backend; shared secret stored as `LANGGRAPH_API_KEY`
- **Cost Target**: Under $10/month for low-traffic usage (10-20 users)

## Dependencies

- Recipe Agent backend (from spec 1-recipe-agent-backend)
- PostgreSQL database on Neon (from spec 4-prod-deployment-infra)
- Agent Chat frontend deployment (from spec 3-agent-chat-frontend)
- Google Cloud account with billing enabled
- GitHub repository with Actions enabled
- Residential proxy service account (Bright Data, Smartproxy, or similar) for YouTube transcript API access

## Clarifications

### Session 2025-12-11

- Q: Which deployment platform should be used? → A: Google Cloud Run (LangSmith costs $40/month, too expensive for 10-20 users)
- Q: What causes YouTube transcript service to fail? → A: Datacenter IPs (AWS/Azure/GCP) are blocked by YouTube; need VPN/proxy to use residential IPs

### Session 2025-12-13

- Q: What approach should be used for YouTube transcript access in production? → A: Residential proxy service (Bright Data, Smartproxy, or similar)

---

*This specification defines WHAT is needed to deploy the backend and establish CI/CD. Implementation details will be addressed in the technical planning phase.*

