"""
Example: Multi-Agent Bridge

Demonstrates A2A routing and AG-UI protocol integration.
"""

import asyncio
from uniskill.bridge import A2ARouter, AGUIBridge, AGUIComponent


async def a2a_example():
    """Demonstrate A2A routing."""
    print("=" * 60)
    print("Agent-to-Agent Routing Example")
    print("=" * 60)

    router = A2ARouter()

    # Register agents
    router.register_agent("nlp-agent", ["text-generation", "summarization", "translation"])
    router.register_agent("vision-agent", ["image-analysis", "ocr", "object-detection"])
    router.register_agent("code-agent", ["code-review", "refactoring", "documentation"])
    router.register_agent("data-agent", ["data-analysis", "visualization", "etl"])

    print("\nRegistered agents:")
    for agent_id in router._agents:
        caps = router.find_capabilities_for_agent(agent_id)
        print(f"  {agent_id}: {', '.join(caps)}")

    # Route tasks
    tasks = [
        ("text-generation", {"prompt": "Write a poem about AI", "max_tokens": 100}),
        ("image-analysis", {"image_url": "https://example.com/photo.jpg"}),
        ("code-review", {"file": "src/main.py", "language": "python"}),
        ("data-analysis", {"query": "SELECT * FROM users", "format": "chart"}),
    ]

    print("\nParallel task execution:")
    results = await router.parallel_execute(tasks)

    for i, (cap, task) in enumerate(tasks):
        print(f"  Task {i+1} ({cap}): {results[i]['status']}")


def agui_example():
    """Demonstrate AG-UI protocol."""
    print("\n" + "=" * 60)
    print("AG-UI Protocol Example")
    print("=" * 60)

    bridge = AGUIBridge()

    # Create various UI components
    chart = bridge.create_component("bar-chart", {
        "data": [{"label": "A", "value": 30}, {"label": "B", "value": 50}, {"label": "C", "value": 20}],
        "title": "Monthly Revenue",
    })

    table = bridge.create_component("data-table", {
        "columns": ["Name", "Role", "Score"],
        "rows": [
            ["Alice", "Engineer", 95],
            ["Bob", "Designer", 88],
            ["Charlie", "Manager", 92],
        ],
    })

    form = bridge.create_component("form", {
        "fields": [
            {"name": "email", "type": "email", "label": "Email"},
            {"name": "name", "type": "text", "label": "Name"},
        ],
        "submit_label": "Save",
    })

    # Render messages
    for component in [chart, table, form]:
        rendered = bridge.render_message(component)
        print(f"\n  Component: {component.component_type}")
        print(f"  Type: {rendered['type']}")

    # State management
    bridge.update_state("current_view", "dashboard")
    bridge.update_state("user_preferences", {"theme": "dark", "language": "en"})

    print(f"\nCurrent state: {bridge._state}")

    # Text delta
    text_msg = bridge.render_message("Processing your request...")
    print(f"\nText message: {text_msg}")


if __name__ == "__main__":
    asyncio.run(a2a_example())
    agui_example()
