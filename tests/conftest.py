"""Pytest configuration for UniSkill tests.

Provides shared fixtures and test configuration.
"""

import tempfile
from pathlib import Path

import pytest

from uniskill.core import UniSkillEngine, EngineConfig, SkillMetadata, SkillLifecycleState


@pytest.fixture
def engine():
    """Create a fresh UniSkill engine for testing."""
    return UniSkillEngine()


@pytest.fixture
def configured_engine():
    """Create an engine with custom config."""
    config = EngineConfig(
        marketplace_enabled=True,
        context_compression_enabled=True,
        default_max_tokens=4096,
    )
    return UniSkillEngine(config=config)


@pytest.fixture
def sample_skill():
    """Create a sample skill metadata."""
    return SkillMetadata(
        name="test-skill",
        version="1.0.0",
        description="A test skill for unit testing",
        author="test",
        entry_point="skill.py",
        lifecycle_state=SkillLifecycleState.INIT,
        tags=["test"],
        compatible_agents=["gpt-4", "claude-3"],
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def temp_skill_dir(temp_dir):
    """Create a temporary skill directory with sample files."""
    skill_dir = temp_dir / "test-skill"
    skill_dir.mkdir()

    (skill_dir / "skill.yaml").write_text("""
name: test-skill
version: 1.0.0
description: Test skill
entry_point: skill.py
""")

    (skill_dir / "skill.py").write_text("""
def execute(data: dict) -> dict:
    return {"status": "ok"}
""")

    return skill_dir
