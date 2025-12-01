# API Contract: LangGraph Server Endpoints

**Feature**: 3-agent-chat-frontend  
**Date**: December 1, 2025  

---

## Overview

The LangGraph server exposes endpoints automatically when running `langgraph dev`. These endpoints follow the LangGraph protocol expected by Agent Chat UI.

**Note**: These endpoints are provided by LangGraph, not implemented manually. This document serves as reference for understanding the communication protocol.

---

## Base URL

```
http://localhost:2024
```

---

## Endpoints

### Health Check

```
GET /health
```

**Response**: `200 OK`
```json
{
  "status": "ok"
}
```

---

### List Assistants

```
GET /assistants
```

**Response**: `200 OK`
```json
{
  "assistants": [
    {
      "assistant_id": "recipe_creator",
      "graph_id": "recipe_creator",
      "config": {},
      "metadata": {}
    }
  ]
}
```

---

### Create Thread

```
POST /threads
```

**Request Body**:
```json
{
  "metadata": {}
}
```

**Response**: `201 Created`
```json
{
  "thread_id": "uuid-string",
  "created_at": "2025-12-01T00:00:00Z",
  "metadata": {}
}
```

---

### Run Agent (Streaming)

```
POST /threads/{thread_id}/runs/stream
```

**Request Body**:
```json
{
  "assistant_id": "recipe_creator",
  "input": {
    "messages": [
      {
        "role": "user",
        "content": "How do I make an Old Fashioned?"
      }
    ]
  },
  "stream_mode": ["events"]
}
```

**Response**: `200 OK` (Server-Sent Events)
```
event: metadata
data: {"run_id": "uuid"}

event: on_chat_model_stream
data: {"content": "To make an Old Fashioned"}

event: on_tool_start
data: {"name": "web_search", "input": {"query": "Old Fashioned cocktail recipe"}}

event: on_tool_end
data: {"name": "web_search", "output": "...search results..."}

event: on_chat_model_stream
data: {"content": ", you'll need..."}

event: end
data: {}
```

---

### Get Thread State

```
GET /threads/{thread_id}/state
```

**Response**: `200 OK`
```json
{
  "values": {
    "messages": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
  },
  "next": [],
  "config": {}
}
```

---

## Event Types (Streaming)

| Event | Description |
|-------|-------------|
| `metadata` | Run metadata including run_id |
| `on_chat_model_stream` | Streaming LLM response tokens |
| `on_tool_start` | Tool invocation started |
| `on_tool_end` | Tool invocation completed |
| `on_chain_start` | Chain/graph node started |
| `on_chain_end` | Chain/graph node completed |
| `end` | Stream complete |

---

## Agent Chat UI Connection

When using the hosted Agent Chat UI:

1. User enters `http://localhost:2024` as deployment URL
2. User enters `agent` as assistant ID
3. UI creates a thread via `POST /threads`
4. UI streams messages via `POST /threads/{id}/runs/stream`
5. UI renders tool calls from `on_tool_start`/`on_tool_end` events

---

## CORS Headers

LangGraph dev server includes CORS headers by default:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

This allows the hosted Agent Chat UI (different origin) to connect to localhost.

---

*Contract documented for reference. Endpoints provided automatically by LangGraph server.*

