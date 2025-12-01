# Data Model: Agent Chat UI Frontend

**Feature**: 3-agent-chat-frontend  
**Date**: December 1, 2025  

---

## Overview

This feature primarily involves configuration and server setup rather than new data entities. The data model focuses on configuration structures needed to connect the backend to Agent Chat UI.

---

## Entities

### LangGraphConfig

Configuration for the LangGraph server defined in `langgraph.json`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| graphs | object | Yes | Map of graph names to module paths |
| env | string | No | Path to environment file |
| dependencies | array | No | Additional Python packages |

**Example**:
```json
{
  "graphs": {
    "recipe_creator": "./agent.py:create_recipe_agent"
  },
  "env": ".env"
}
```

---

### GraphState

State object passed through the LangGraph graph (extends existing message pattern).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| messages | array[Message] | Yes | Conversation history |

**Notes**:
- Uses LangChain message types (HumanMessage, AIMessage)
- Compatible with existing `main.py` message handling

---

### ServerConfig

Environment-based configuration for the LangGraph server.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| HOST | string | "0.0.0.0" | Server bind address |
| PORT | integer | 2024 | Server port |

---

## Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Chat UI (Hosted)                   │
│                  https://agentchat.vercel.app               │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/Streaming
                      │ (LangGraph Protocol)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph Server                          │
│                   localhost:2024                            │
├─────────────────────────────────────────────────────────────┤
│  langgraph.json ──► graph.py ──► agent.py                  │
│                         │            │                      │
│                    GraphState    create_agent()             │
│                         │            │                      │
│                         └────────────┘                      │
│                              │                              │
│                        tools/                               │
│                   ┌──────────┴──────────┐                   │
│              web_search.py      youtube.py                  │
└─────────────────────────────────────────────────────────────┘
```

---

## State Transitions

### Connection Flow

```
1. [Disconnected] ──(user enters URL)──► [Connecting]
2. [Connecting] ──(handshake success)──► [Connected]
3. [Connecting] ──(handshake fail)──► [Error]
4. [Connected] ──(send message)──► [Processing]
5. [Processing] ──(response complete)──► [Connected]
```

**Note**: State is managed by Agent Chat UI, not the backend.

---

## Validation Rules

### langgraph.json
- `graphs` must contain at least one entry
- Graph module path must be valid Python import path
- Graph must export a valid LangGraph graph object

### Server
- PORT must be between 1024-65535
- PORT 2024 recommended for Agent Chat UI compatibility

---

*Data model complete. Minimal new entities—primarily configuration structures.*

