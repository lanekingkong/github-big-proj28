"""Tests for protocol bridge."""

import pytest
from uniskill.bridge import (
    MCPServer,
    MCPTool,
    MCPResource,
    A2ARouter,
    AGUIBridge,
    AGUIComponent,
)


class TestMCPServer:
    """Test MCP server."""

    def test_list_tools(self):
        server = MCPServer()
        tool = MCPTool(name="test_tool", description="A test tool", input_schema={"type": "object"})
        server.register_tool(tool)

        tools = server.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

    def test_initialize_handshake(self):
        server = MCPServer(name="test-server", version="2.0.0")
        import asyncio
        result = asyncio.run(server.handle_request("initialize"))

        assert result["serverInfo"]["name"] == "test-server"
        assert result["serverInfo"]["version"] == "2.0.0"
        assert "tools" in result["capabilities"]

    def test_ping(self):
        server = MCPServer()
        import asyncio
        result = asyncio.run(server.handle_request("ping"))
        assert result == {}

    def test_unknown_method(self):
        server = MCPServer()
        import asyncio
        result = asyncio.run(server.handle_request("unknown/method"))
        assert "error" in result

    def test_list_resources(self):
        server = MCPServer()
        resource = MCPResource(uri="file:///test.txt", name="Test File")
        server.register_resource(resource)

        resources = server.list_resources()
        assert len(resources) == 1
        assert resources[0]["uri"] == "file:///test.txt"

    def test_call_tool_not_found(self):
        server = MCPServer()
        import asyncio
        result = asyncio.run(server.call_tool("nonexistent", {}))
        assert "error" in result


class TestA2ARouter:
    """Test A2A router."""

    def test_register_agent(self):
        router = A2ARouter()
        router.register_agent("agent-1", ["text-generation", "summarization"])

        agents = router.find_agents_for_capability("text-generation")
        assert "agent-1" in agents

    def test_find_capabilities(self):
        router = A2ARouter()
        router.register_agent("agent-1", ["code-review", "refactoring"])

        caps = router.find_capabilities_for_agent("agent-1")
        assert "code-review" in caps
        assert "refactoring" in caps

    def test_route_task(self):
        router = A2ARouter()
        router.register_agent("agent-1", ["nlp"])

        agent = router.route_task("nlp", {"text": "hello"})
        assert agent == "agent-1"

    def test_no_agent_for_capability(self):
        router = A2ARouter()
        agent = router.route_task("nonexistent", {})
        assert agent is None


class TestAGUIBridge:
    """Test AG-UI bridge."""

    def test_create_component(self):
        bridge = AGUIBridge()
        component = bridge.create_component("chart", {"data": [1, 2, 3]})

        assert isinstance(component, AGUIComponent)
        assert component.component_type == "chart"
        assert component.props == {"data": [1, 2, 3]}

    def test_state_management(self):
        bridge = AGUIBridge()
        bridge.update_state("user_id", "12345")

        assert bridge.get_state("user_id") == "12345"
        assert bridge.get_state("nonexistent", "default") == "default"

    def test_render_text(self):
        bridge = AGUIBridge()
        result = bridge.render_message("Hello world")
        assert result["type"] == "text-delta"
        assert result["text"] == "Hello world"

    def test_render_component(self):
        bridge = AGUIBridge()
        component = AGUIComponent(component_type="table", props={"rows": [1, 2, 3]})
        result = bridge.render_message(component)

        assert result["type"] == "render-ui"
        assert result["component"]["type"] == "table"
