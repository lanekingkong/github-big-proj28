"""
Protocol Definitions - MCP, A2A, AG-UI Protocol Schemas and Utilities.

Standard protocol types and validation for multi-agent communication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class MCPVersion(Enum):
    V1_0 = "2024-11-05"


class TransportType(Enum):
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


@dataclass
class MCPInitializeRequest:
    """MCP initialize request."""
    protocolVersion: str = "2024-11-05"
    capabilities: dict[str, Any] = field(default_factory=dict)
    clientInfo: dict[str, str] = field(default_factory=dict)


@dataclass
class MCPInitializeResponse:
    """MCP initialize response."""
    protocolVersion: str = "2024-11-05"
    serverInfo: dict[str, str] = field(default_factory=dict)
    capabilities: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPToolDefinition:
    """MCP tool definition schema."""
    name: str
    description: str = ""
    inputSchema: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPResourceDefinition:
    """MCP resource definition schema."""
    uri: str
    name: str
    description: str = ""
    mimeType: str = "text/plain"


@dataclass
class MCPPromptDefinition:
    """MCP prompt definition schema."""
    name: str
    description: str = ""
    arguments: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class A2AMessage:
    """Agent-to-Agent message format."""
    message_id: str
    sender_id: str
    receiver_id: str
    content: dict[str, Any]
    correlation_id: Optional[str] = None
    timestamp: str = ""


@dataclass
class A2ATaskRequest:
    """A2A task delegation request."""
    task_id: str
    capability: str
    payload: dict[str, Any]
    priority: int = 5
    deadline_ms: int = 30000


@dataclass
class A2ATaskResponse:
    """A2A task delegation response."""
    task_id: str
    status: str
    result: Any = None
    error: str = ""
    agent_id: str = ""


@dataclass
class AGUIMessage:
    """AG-UI protocol message."""
    messageId: str
    type: str
    delta: str = ""
    component: dict[str, Any] = field(default_factory=dict)
    state_update: dict[str, Any] = field(default_factory=dict)
    error: str = ""
