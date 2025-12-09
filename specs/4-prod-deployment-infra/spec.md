# Feature Specification: Production Deployment Infrastructure

**Feature ID**: 4-prod-deployment-infra  
**Created**: December 9, 2025  
**Status**: Draft  

## Overview

### Problem Statement

The Recipe Agent currently runs only in local development mode with SQLite file-based storage. This limits the agent to single-machine use and prevents sharing the agent with others or running it as a persistent service. Users cannot access their saved recipes from different devices, and the agent cannot be made available to external users.

### Solution Summary

Deploy the Recipe Agent to LangSmith Cloud as a hosted LangGraph deployment, replacing the local SQLite database with PostgreSQL on Neon for persistent, cloud-accessible recipe storage. This enables the agent to run as a production service accessible via the Agent Chat UI from anywhere.

### Target Users

- **Primary User**: Recipe Agent developer who wants to make the agent publicly accessible
- **Secondary User**: End users who want to access the Recipe Agent and their saved recipes from any device

## Functional Requirements

### FR-1: Cloud Database Migration (Coding Agent Scope)

The recipe storage system shall use PostgreSQL (Neon) exclusively, with all SQLite code and dependencies removed.

**Acceptance Criteria**:
- All SQLite code, configuration, and dependencies are removed from the codebase
- SQLite migration script is removed (not needed)
- New recipes are saved to PostgreSQL database
- Recipe queries return results from PostgreSQL database
- Database connection is secure (encrypted connection)
- Connection failures are handled gracefully with user-friendly error messages
- Separate PostgreSQL databases are supported for development and production environments (via connection string configuration)

### FR-2: LangSmith Deployment (Manual - Developer)

The Recipe Agent shall be deployed as a hosted service on LangSmith Cloud.

**Acceptance Criteria**:
- Agent is accessible via a public LangSmith deployment URL
- Agent responds to chat requests from the hosted Agent Chat UI
- All existing tools (web search, YouTube, recipe storage) function correctly when deployed
- Agent maintains conversation context within sessions
- Deployment can be updated when code changes are made

### FR-3: Environment Configuration (Manual - Developer)

The deployment shall support secure environment variable management.

**Acceptance Criteria**:
- API keys (Anthropic/OpenAI, Tavily) are securely stored, not in code
- Database connection string is configured securely
- Environment variables can be updated without redeploying code
- Local development continues to work with local `.env` file

### FR-4: Production Monitoring (Manual - Developer)

The deployed agent shall provide visibility into its operation.

**Acceptance Criteria**:
- Chat sessions are logged and viewable in LangSmith
- Tool calls and responses are traceable
- Errors are captured and reportable
- Usage metrics are accessible (conversations, tool calls)

## User Scenarios & Testing

### Scenario 1: Deploying the Agent

**Given** a developer has configured LangSmith credentials  
**When** they run the deployment command  
**Then** the agent is deployed to LangSmith and a deployment URL is provided.

### Scenario 2: Accessing Deployed Agent

**Given** the agent is deployed to LangSmith  
**When** a user opens Agent Chat UI and enters the deployment URL  
**Then** they can connect and start chatting with the Recipe Agent.

### Scenario 3: Saving a Recipe (Cloud Storage)

**Given** a user is chatting with the deployed agent  
**When** they ask to save a recipe  
**Then** the recipe is saved to PostgreSQL and retrievable in future sessions.

### Scenario 4: Retrieving Saved Recipes

**Given** a user has previously saved recipes via the deployed agent  
**When** they ask "What recipes have I saved?"  
**Then** the agent queries PostgreSQL and returns their saved recipes.

### Scenario 5: Viewing Agent Activity

**Given** users have been chatting with the deployed agent  
**When** the developer views LangSmith dashboard  
**Then** they see conversation logs, tool calls, and any errors.

## Success Criteria

| Criterion | Target | Measurement Method |
|-----------|--------|-------------------|
| Deployment Accessibility | Agent reachable via public URL | Connect from Agent Chat UI |
| Recipe Persistence | Recipes saved survive server restarts | Save recipe, restart, retrieve |
| Response Time | Agent responds within 10 seconds | Timed conversation request |
| SQLite Removal | No SQLite code or dependencies remain | Code review, dependency check |
| Uptime | Agent available 99% of time | LangSmith availability metrics |
| Tool Functionality | All 4 tools work in production | Test each tool via deployed agent |

## Key Entities

### Deployment Configuration
- LangSmith organization/project
- Deployment name/identifier
- Environment variables (API keys, database URL)

### Database Connection
- `DATABASE_URL` environment variable (full PostgreSQL connection string from Neon)
- Connection pool settings (SQLAlchemy defaults)

### Monitoring Data
- Conversation logs
- Tool invocation traces
- Error reports

## Assumptions

1. LangSmith Cloud supports deploying LangGraph agents
2. Neon PostgreSQL free tier provides sufficient resources for initial deployment
3. Existing SQLAlchemy async code is compatible with asyncpg (PostgreSQL async driver)
4. LangSmith provides secure environment variable storage
5. No significant code changes required beyond configuration for deployment
6. User has or will create accounts on LangSmith and Neon

## Out of Scope

- Custom domain configuration
- User authentication/authorization (multi-user support)
- Auto-scaling configuration
- Cost optimization strategies
- Backup and disaster recovery procedures
- CI/CD pipeline automation
- Load balancing across multiple instances

## Technical Constraints

*Note: These are user-specified implementation preferences.*

- **Deployment Platform**: LangSmith Cloud (LangGraph deployment)
- **Database**: PostgreSQL on Neon (cloud-hosted) - PostgreSQL-only, no SQLite support
- **Environment Strategy**: Separate PostgreSQL databases for development and production

## Clarifications

### Session 2025-12-09

- Q: Should code support dual-mode (SQLite local, PostgreSQL prod) or PostgreSQL-only? → A: PostgreSQL-only everywhere, with separate databases for development and production branches.
- Q: Should SQLite code be removed or kept (migration script, rollback)? → A: Complete removal of all SQLite code and dependencies, including migration script (not needed).
- Q: How should PostgreSQL connection be configured? → A: Single `DATABASE_URL` environment variable with full connection string.

## Dependencies

- Recipe Agent backend (from spec 1-recipe-agent-backend)
- Agent Chat UI integration (from spec 3-agent-chat-frontend)
- LangSmith account with deployment capabilities
- Neon account with PostgreSQL database provisioned
- SQLAlchemy async PostgreSQL support (asyncpg driver)

---

*This specification defines WHAT is needed to deploy the Recipe Agent to production. Implementation details will be addressed in the technical planning phase.*

