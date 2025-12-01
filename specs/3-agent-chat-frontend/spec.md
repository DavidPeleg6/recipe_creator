# Feature Specification: Agent Chat UI Frontend

**Feature ID**: 3-agent-chat-frontend  
**Created**: December 1, 2025  
**Status**: Draft  

## Overview

### Problem Statement

The Recipe Agent backend currently only has a CLI interface for interaction. While functional for development, users need a more intuitive, visual interface for recipe discovery. Setting up a custom frontend from scratch would be time-consuming and unnecessary.

### Solution Summary

Connect the existing Recipe Agent backend to LangChain's hosted Agent Chat UI (Vercel app). This provides an immediate, polished chat interface without building custom frontend code. The work focuses on ensuring backend compatibility and establishing the connection.

### Target Users

- **Primary User**: Home cook/mixologist who prefers a visual interface over CLI
- **Use Context**: Accessing the Recipe Agent through a browser while cooking or preparing drinks

## Functional Requirements

### FR-1: Backend Server Exposure

The Recipe Agent backend shall run as an HTTP server accessible to the hosted Agent Chat UI.

**Acceptance Criteria**:
- Backend starts as an HTTP server (not just CLI)
- Server listens on a configurable port
- Server is accessible from a web browser
- Health/status endpoint confirms server is running

### FR-2: Agent Chat UI Compatibility

The backend shall expose endpoints compatible with LangChain's Agent Chat UI protocol.

**Acceptance Criteria**:
- Backend implements the required API contract for Agent Chat UI
- Agent responses stream correctly to the UI
- Tool calls (web search, YouTube) are properly formatted for UI visualization
- Message history is maintained within sessions

### FR-3: Connection Configuration

Users shall be able to connect the hosted Agent Chat UI to their local backend.

**Acceptance Criteria**:
- Clear documentation of required connection parameters (Graph ID, deployment URL)
- Local server URL can be entered in the hosted UI
- Connection succeeds and chat functionality works
- Error messages are clear if connection fails

### FR-4: Local Development Workflow

The setup shall support a simple local development workflow.

**Acceptance Criteria**:
- Single command starts the backend server
- Clear instructions for opening the hosted Agent Chat UI
- Steps to configure the connection are documented
- Total setup time under 5 minutes

## User Scenarios & Testing

### Scenario 1: Starting the Backend Server

**Given** a user has the Recipe Agent code  
**When** they run the server start command  
**Then** the backend starts and displays the URL/port it's listening on.

### Scenario 2: Connecting via Hosted UI

**Given** the backend server is running locally  
**When** the user visits the hosted Agent Chat UI and enters their local server URL  
**Then** the UI connects successfully and shows the chat interface ready for input.

### Scenario 3: Sending a Recipe Request

**Given** the UI is connected to the local backend  
**When** the user types "How do I make an Old Fashioned?" and sends it  
**Then** the response streams back with the recipe, and any tool calls (web search) are visible in the UI.

### Scenario 4: Connection Failure

**Given** the backend server is not running  
**When** the user tries to connect from the hosted UI  
**Then** a clear error message indicates the server is unavailable.

## Success Criteria

| Criterion | Target | Measurement Method |
|-----------|--------|-------------------|
| Server Startup | Backend starts as HTTP server | Server responds to health check |
| UI Connection | Hosted UI connects to local backend | Successful handshake, chat ready |
| Message Round-trip | User sends message, receives response | Complete conversation flow |
| Tool Visibility | Tool calls appear in UI | Visual confirmation of web search/YouTube indicators |
| Setup Time | Under 5 minutes from start to first chat | Timed walkthrough |

## Key Entities

### Server Configuration
- Port number
- Host binding
- Graph/agent identifier

### Connection Parameters
- Deployment URL (local server address)
- Graph ID (agent identifier)

## Assumptions

1. LangChain's hosted Agent Chat UI (Vercel app) remains freely accessible
2. The `create_agent` pattern used in backend is compatible with Agent Chat UI
3. Backend can be extended to run as HTTP server without major refactoring
4. User has a modern web browser
5. Local network allows connections between browser and local server

## Out of Scope

- Custom frontend development (using hosted UI)
- Frontend styling or theming (handled by hosted app)
- User authentication
- Persistent conversation storage
- Production deployment
- Running Agent Chat UI locally (using hosted version)

## Technical Constraints

*Note: These are user-specified implementation preferences.*

- **Frontend**: LangChain's hosted Agent Chat UI (https://agentchat.vercel.app)
- **Backend**: Must expose LangGraph-compatible server endpoints
- **Protocol Reference**: Backend-frontend handshake must follow the protocol defined in https://github.com/langchain-ai/agent-chat-ui
- **Documentation**: https://docs.langchain.com/oss/python/langchain/ui

### Connection Protocol

Per the [agent-chat-ui repository](https://github.com/langchain-ai/agent-chat-ui), the backend must support:

- **Environment Variables**: `NEXT_PUBLIC_API_URL` (backend URL) and `NEXT_PUBLIC_ASSISTANT_ID` (graph/agent ID)
- **Default Local Setup**: Backend listens on `http://localhost:2024` with assistant ID `recipe_creator`
- **LangGraph Server**: Backend must run as a LangGraph server or compatible endpoint

## Dependencies

- Recipe Agent backend (from spec 1-recipe-agent-backend)
- LangChain hosted Agent Chat UI availability (https://agentchat.vercel.app)
- LangGraph server or compatible serving layer
- Agent Chat UI protocol compatibility (https://github.com/langchain-ai/agent-chat-ui)

---

*This specification defines WHAT is needed to connect the Recipe Agent to the hosted Agent Chat UI. Implementation details will be addressed in the technical planning phase.*
