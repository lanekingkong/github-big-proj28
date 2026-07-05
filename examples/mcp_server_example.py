"""
Example: Using UniSkill with MCP Server

This example demonstrates:
1. Creating a simple skill
2. Registering it as an MCP tool
3. Calling it through the MCP protocol
"""

import asyncio
from uniskill.bridge import MCPServer, MCPTool
from uniskill.core import UniSkillEngine, SkillMetadata, SkillLifecycleState


def weather_skill(city: str = "Beijing", units: str = "metric") -> dict:
    """Get weather for a city. (Simulated)"""
    return {
        "city": city,
        "temperature": 22,
        "units": units,
        "condition": "sunny",
        "humidity": 45,
    }


async def main():
    """Run the MCP server example."""
    # Create engine and register skill
    engine = UniSkillEngine()
    skill = SkillMetadata(
        name="weather",
        version="1.0.0",
        description="Get weather information for any city",
        author="example",
        entry_point="weather_skill",
        lifecycle_state=SkillLifecycleState.SHIP,
        tags=["weather", "utility"],
    )
    engine.register_skill(skill)

    # Create MCP server
    server = MCPServer(name="example-server", version="1.0.0")

    # Register skill as MCP tool
    tool = MCPTool(
        name="get_weather",
        description="Get current weather for a city",
        input_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "units": {"type": "string", "enum": ["metric", "imperial"]},
            },
        },
        handler=weather_skill,
    )
    server.register_tool(tool)

    # List available tools
    print("Available MCP tools:")
    for tool in server.list_tools():
        print(f"  - {tool['name']}: {tool['description']}")

    # Call tool via MCP
    result = await server.call_tool("get_weather", {"city": "Shanghai"})
    print(f"\nWeather result: {result}")

    # Check engine health
    health = engine.health_check()
    print(f"\nEngine status: {health}")


if __name__ == "__main__":
    asyncio.run(main())
