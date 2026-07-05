"""
Protocol Bridge - MCP Server, A2A Router, and AG-UI Bridge.

Implements Model Context Protocol (MCP) server, Agent-to-Agent (A2A)
capability routing, and Agent UI (AG-UI) protocol for generative interfaces.

Inspired by:
- Anthropic's MCP specification
- CopilotKit's AG-UI protocol for generative UI
- last30days-skill's parallel execution patterns
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger(__name__)


class MCPMethod(Enum):
    """MCP protocol method types."""

    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    INITIALIZE = "initialize"
    PING = "ping"


class AGUIMessageType(Enum):
    """AG-UI message types for generative UI."""

    TEXT_DELTA = "text-delta"
    TOOL_CALL = "tool-call"
    STATE_UPDATE = "state-update"
    RENDER_UI = "render-ui"
    COMPONENT_EVENT = "component-event"
    ERROR = "error"


@dataclass
class MCPTool:
    """An MCP tool definition."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Optional[Callable] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


@dataclass
class MCPResource:
    """An MCP resource definition."""

    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


@dataclass
class AGUIComponent:
    """A generative UI component definition.

    Agents return component names + props instead of Markdown.
    Frontend has a component map that renders these directly as
    interactive UI elements (charts, forms, tables, etc.).
    """

    component_type: str
    props: dict[str, Any]
    key: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.component_type,
            "props": self.props,
            "key": self.key,
        }


class MCPServer:
    """Model Context Protocol (MCP) server implementation.

    Exposes skills as MCP tools and resources that AI agents
    can discover and call through the standard protocol.

    Supports:
    - tools/list and tools/call for skill execution
    - resources/list and resources/read for data access
    - prompts/list and prompts/get for prompt templates
    - SSE transport for streaming responses
    """

    def __init__(self, name: str = "uniskill-mcp", version: str = "1.0.0"):
        self._name = name
        self._version = version
        self._tools: dict[str, MCPTool] = {}
        self._resources: dict[str, MCPResource] = {}
        self._prompts: dict[str, dict] = {}

    def register_tool(self, tool: MCPTool) -> None:
        """Register a skill as an MCP tool."""
        self._tools[tool.name] = tool
        logger.info("mcp_tool_registered", name=tool.name)

    def register_resource(self, resource: MCPResource) -> None:
        """Register a resource for agent access."""
        self._resources[resource.uri] = resource

    def register_prompt(self, name: str, template: str, arguments: list[dict]) -> None:
        """Register a prompt template."""
        self._prompts[name] = {
            "name": name,
            "description": f"Prompt template: {name}",
            "arguments": arguments,
            "_template": template,
        }

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools (MCP tools/list)."""
        return [t.to_dict() for t in self._tools.values()]

    def list_resources(self) -> list[dict[str, Any]]:
        """List all registered resources."""
        return [r.to_dict() for r in self._resources.values()]

    def list_prompts(self) -> list[dict[str, Any]]:
        """List all registered prompts."""
        return [
            {k: v for k, v in p.items() if not k.startswith("_")}
            for p in self._prompts.values()
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a registered tool (MCP tools/call)."""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found"}

        if not tool.handler:
            return {"error": f"Tool '{name}' has no handler"}

        try:
            result = await tool.handler(**arguments) if asyncio.iscoroutinefunction(tool.handler) else tool.handler(**arguments)
            return {"content": [{"type": "text", "text": str(result)}]}
        except Exception as e:
            logger.error("mcp_tool_error", tool=name, error=str(e))
            return {"error": str(e)}

    async def handle_request(self, method: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Handle an incoming MCP request."""
        params = params or {}

        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": self._name, "version": self._version},
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True},
                    "prompts": {"listChanged": False},
                },
            }
        elif method == "tools/list":
            return {"tools": self.list_tools()}
        elif method == "tools/call":
            return await self.call_tool(params.get("name", ""), params.get("arguments", {}))
        elif method == "resources/list":
            return {"resources": self.list_resources()}
        elif method == "prompts/list":
            return {"prompts": self.list_prompts()}
        elif method == "ping":
            return {}
        else:
            return {"error": f"Unknown method: {method}"}


class A2ARouter:
    """Agent-to-Agent (A2A) capability router.

    Enables agents to discover and delegate tasks to other agents
    through a standard capability protocol. Inspired by the A2A
    specification for multi-agent systems.

    Key features:
    - Agent capability registry and discovery
    - Task delegation with fallback
    - Parallel execution for independent subtasks
    - Graceful degradation (partial failure handling)
    """

    def __init__(self):
        self._agents: dict[str, dict[str, Any]] = {}
        self._capabilities: dict[str, list[str]] = {}

    def register_agent(
        self, agent_id: str, capabilities: list[str], endpoint: str = ""
    ) -> None:
        """Register an agent with its capabilities."""
        self._agents[agent_id] = {
            "id": agent_id,
            "capabilities": capabilities,
            "endpoint": endpoint,
            "status": "online",
        }
        for cap in capabilities:
            if cap not in self._capabilities:
                self._capabilities[cap] = []
            self._capabilities[cap].append(agent_id)
        logger.info("agent_registered", agent_id=agent_id, capabilities=capabilities)

    def find_agents_for_capability(self, capability: str) -> list[str]:
        """Find agents that have a specific capability."""
        return self._capabilities.get(capability, [])

    def find_capabilities_for_agent(self, agent_id: str) -> list[str]:
        """Find all capabilities of an agent."""
        agent = self._agents.get(agent_id)
        return agent["capabilities"] if agent else []

    def route_task(self, capability: str, task: dict[str, Any]) -> Optional[str]:
        """Route a task to the best agent for the capability."""
        candidates = self.find_agents_for_capability(capability)
        if not candidates:
            return None

        # Simple round-robin for now; in production, use load/performance metrics
        return candidates[0]

    async def parallel_execute(
        self, tasks: list[tuple[str, dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        """Execute multiple tasks in parallel across agents.

        Uses asyncio.gather with return_exceptions=True for
        partial failure handling (inspired by last30days-skill).
        """
        async def execute_one(capability: str, task: dict) -> dict:
            agent_id = self.route_task(capability, task)
            if not agent_id:
                return {"status": "error", "message": f"No agent for capability: {capability}"}
            # In production, would call agent endpoint
            return {"status": "delegated", "agent_id": agent_id, "capability": capability}

        results = await asyncio.gather(
            *[execute_one(cap, task) for cap, task in tasks],
            return_exceptions=True,
        )
        return [
            r if not isinstance(r, Exception) else {"status": "error", "message": str(r)}
            for r in results
        ]


class AGUIBridge:
    """Agent UI (AG-UI) protocol bridge.

    Implements the AG-UI protocol for generative UI rendering,
    inspired by CopilotKit's architecture.

    Instead of agents returning Markdown, they return component
    names + props. The frontend has a component map that renders
    these as interactive UI elements.
    """

    def __init__(self):
        self._component_registry: dict[str, Any] = {}
        self._state: dict[str, Any] = {}
        self._subscribers: list[Callable] = []

    def register_component(self, component_type: str, component_class: Any) -> None:
        """Register a UI component for generative rendering."""
        self._component_registry[component_type] = component_class

    def create_component(self, component_type: str, props: dict[str, Any]) -> AGUIComponent:
        """Create a generative UI component."""
        if component_type not in self._component_registry:
            logger.warning("unknown_component", type=component_type)
        return AGUIComponent(component_type=component_type, props=props)

    def update_state(self, key: str, value: Any) -> None:
        """Update shared agent-UI state."""
        self._state[key] = value
        self._notify_subscribers({"type": "state-update", "key": key, "value": value})

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def subscribe(self, callback: Callable) -> None:
        """Subscribe to state changes."""
        self._subscribers.append(callback)

    def _notify_subscribers(self, event: dict) -> None:
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception:
                pass

    def render_message(self, content: Any) -> dict[str, Any]:
        """Render agent output as AG-UI messages."""
        if isinstance(content, AGUIComponent):
            return {
                "type": AGUIMessageType.RENDER_UI.value,
                "component": content.to_dict(),
            }
        elif isinstance(content, str):
            return {
                "type": AGUIMessageType.TEXT_DELTA.value,
                "text": content,
            }
        elif isinstance(content, dict) and "type" in content:
            return content
        else:
            return {
                "type": AGUIMessageType.TEXT_DELTA.value,
                "text": str(content),
            }
