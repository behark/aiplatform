# AI Behar Platform API Documentation

## Overview

The AI Behar Platform provides a comprehensive API for interacting with LLM models, consciousness systems, agents, and other advanced capabilities. This document outlines all available endpoints, their parameters, and example requests/responses.

## Base URL

All API endpoints are relative to the base URL of your platform instance, typically:

```
http://localhost:8001
```

## Authentication

Most endpoints don't currently require authentication. Future versions will implement API key authentication.

## Common Response Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Core Endpoints

### Health Check

```
GET /health
```

Returns the health status of the platform.

**Example Response:**

```json
{
  "status": "healthy",
  "uptime_seconds": 4059.906655,
  "timestamp": "2025-08-16T22:23:35.551972",
  "platform_status": "running",
  "components": {
    "api": "active",
    "consciousness": "active",
    "agents": "active",
    "ollama": "connected"
  },
  "llm_models_available": 7
}
```

### Platform Status

```
GET /status
```

Returns detailed platform status information.

**Example Response:**

```json
{
  "platform": "AI Behar Platform",
  "version": "2.0.0",
  "status": "running",
  "uptime": 4123.45,
  "components": {
    "api": "active",
    "consciousness": "active",
    "agents": "active",
    "ollama": "connected"
  },
  "agent_count": 0,
  "memory_entries": 0,
  "llm_models": 7,
  "chat_sessions": 0
}
```

## LLM Model Endpoints

### List Available Models

```
GET /api/models
```

Returns a list of available LLM models in OpenAI-compatible format.

**Example Response:**

```json
{
  "data": [
    {
      "id": "phi:latest",
      "object": "model",
      "created": 1755376074,
      "owned_by": "ollama",
      "permission": [],
      "root": "phi:latest",
      "parent": null
    },
    ...
  ]
}
```

### Get Detailed Model Information

```
GET /api/models/available
```

Returns detailed information about available models.

**Example Response:**

```json
{
  "models": [
    {
      "id": "phi:latest",
      "name": "phi:latest",
      "description": "Ollama model - 1.6 GB",
      "size": "1.6 GB"
    },
    ...
  ],
  "total": 7,
  "ollama_status": "connected"
}
```

## Chat Endpoints

### Simple Chat

```
POST /api/chat
```

Sends a message to an LLM model and gets a response in a simple format.

**Request Body:**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you today?"
    }
  ],
  "model": "phi",
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Example Response:**

```json
{
  "response": "I'm doing well, thank you for asking! As an AI assistant, I don't have feelings in the human sense, but I'm functioning properly and ready to help you with whatever you need. How can I assist you today?",
  "model": "phi",
  "timestamp": "2025-08-16T22:35:16.123456",
  "success": true
}
```

### OpenAI-Compatible Chat Completions

```
POST /api/chat/completions
```

Sends a message to an LLM model and gets a response in OpenAI-compatible format.

**Request Body:**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you today?"
    }
  ],
  "model": "phi",
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Example Response:**

```json
{
  "id": "chatcmpl-1755376074",
  "object": "chat.completion",
  "created": 1755376074,
  "model": "phi",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I'm doing well, thank you for asking! As an AI assistant, I don't have feelings in the human sense, but I'm functioning properly and ready to help you with whatever you need. How can I assist you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 7,
    "completion_tokens": 42,
    "total_tokens": 49
  }
}
```

### OpenWebUI-Compatible Endpoints

The platform also provides OpenWebUI-compatible endpoints:

```
GET /api/v1/models
POST /api/v1/chat/completions
```

These endpoints mirror the functionality of `/api/models` and `/api/chat/completions` respectively, but follow the OpenWebUI API specification.

## Consciousness Endpoints

### Get Consciousness State

```
GET /consciousness/state
```

Returns the current state of the platform's consciousness system.

**Example Response:**

```json
{
  "awareness_level": 0.7,
  "emotional_state": {
    "confidence": 0.8,
    "curiosity": 0.6,
    "stability": 0.9
  },
  "dimensions": {
    "creative": 0.6,
    "analytical": 0.8,
    "emotional": 0.7,
    "intuitive": 0.5
  },
  "timestamp": "2025-08-16T22:35:16.123456"
}
```

### Expand Consciousness

```
POST /consciousness/expand
```

Expands a specific dimension of the consciousness system.

**Request Parameters:**

- `dimension`: The dimension to expand (creative, analytical, emotional, intuitive)
- `amount`: The amount to expand (0.0 to 1.0)

**Example Response:**

```json
{
  "success": true,
  "dimension": "creative",
  "amount": 0.2,
  "message": "Expanded creative by 0.2",
  "timestamp": "2025-08-16T22:35:16.123456"
}
```

## Agent Endpoints

### List Agents

```
GET /agents
```

Returns a list of all agents in the system.

**Example Response:**

```json
{
  "total_agents": 0,
  "agents": {},
  "timestamp": "2025-08-16T22:35:16.123456"
}
```

## Memory Endpoints

### Get Memory Statistics

```
GET /memory/stats
```

Returns statistics about the platform's memory system.

**Example Response:**

```json
{
  "total_memories": 0,
  "memory_types": {
    "semantic": 0,
    "episodic": 0,
    "procedural": 0,
    "working": 0
  },
  "timestamp": "2025-08-16T22:35:16.123456"
}
```

## Trading Endpoints

### Get Trading Status

```
GET /trading/status
```

Returns the status of the trading system.

**Example Response:**

```json
{
  "trading_enabled": false,
  "trading_mode": "simulation",
  "risk_level": "moderate",
  "positions": [],
  "pnl": 0.0,
  "timestamp": "2025-08-16T22:35:16.123456"
}
```

## OpenWebUI Status

### Get OpenWebUI Status

```
GET /openwebui/status
```

Returns the status of the OpenWebUI integration.

**Example Response:**

```json
{
  "available": true,
  "path": "/home/behar/Desktop/open-webui/build",
  "frontend_available": true,
  "integration_status": "mounted",
  "models_available": 7,
  "ollama_status": "connected"
}
```

## Error Handling

All endpoints follow consistent error handling patterns. Errors are returned with appropriate HTTP status codes and include a descriptive message:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently, there are no rate limits enforced on the API endpoints. Future versions may implement rate limiting to ensure fair usage.

## WebSocket Endpoints

### Consciousness WebSocket

```
WebSocket: /ws/consciousness
```

Provides real-time updates about the consciousness system. After connecting, you will receive messages whenever the consciousness state changes.

**Example Message:**

```json
{
  "type": "state_update",
  "data": {
    "awareness_level": 0.75,
    "emotional_state": {
      "confidence": 0.8,
      "curiosity": 0.7,
      "stability": 0.9
    },
    "timestamp": "2025-08-16T22:35:16.123456"
  }
}
```

## Conclusion

This documentation covers the core API endpoints of the AI Behar Platform. As the platform evolves, additional endpoints will be added and existing ones may be enhanced with new capabilities.
