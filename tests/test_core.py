"""Tests for UniSkill core engine."""

import pytest
from uniskill.core import (
    UniSkillEngine,
    EngineConfig,
    SkillMetadata,
    SkillLifecycleState,
)


class TestSkillLifecycle:
    """Test skill lifecycle state machine."""

    def test_valid_transitions(self):
        engine = UniSkillEngine()
        skill = SkillMetadata(name="test-skill", version="1.0.0")

        # INIT → PLAN
        assert engine.can_transition(SkillLifecycleState.INIT, SkillLifecycleState.PLAN)
        assert engine.transition(skill, SkillLifecycleState.PLAN)
        assert skill.lifecycle_state == SkillLifecycleState.PLAN

    def test_invalid_transition(self):
        engine = UniSkillEngine()
        skill = SkillMetadata(name="test-skill", version="1.0.0")

        # Cannot jump from INIT to SHIP
        assert not engine.can_transition(SkillLifecycleState.INIT, SkillLifecycleState.SHIP)
        assert not engine.transition(skill, SkillLifecycleState.SHIP)
        assert skill.lifecycle_state == SkillLifecycleState.INIT

    def test_full_lifecycle_flow(self):
        engine = UniSkillEngine()
        skill = SkillMetadata(name="test-skill", version="1.0.0")

        flow = [
            SkillLifecycleState.PLAN,
            SkillLifecycleState.SPEC,
            SkillLifecycleState.CODE,
            SkillLifecycleState.TEST,
            SkillLifecycleState.REVIEW,
            SkillLifecycleState.DOC,
            SkillLifecycleState.SHIP,
        ]

        for state in flow:
            assert engine.transition(skill, state)
            assert skill.lifecycle_state == state

    def test_deprecated_to_retired(self):
        engine = UniSkillEngine()
        skill = SkillMetadata(
            name="test-skill",
            version="1.0.0",
            lifecycle_state=SkillLifecycleState.SHIP,
        )

        assert engine.transition(skill, SkillLifecycleState.DEPRECATED)
        assert engine.transition(skill, SkillLifecycleState.RETIRED)
        assert skill.lifecycle_state == SkillLifecycleState.RETIRED


class TestEngineCore:
    """Test core engine functionality."""

    def test_register_skill(self):
        engine = UniSkillEngine()
        skill = SkillMetadata(name="my-skill", version="1.0.0", description="Test skill")
        engine.register_skill(skill)

        assert engine.get_skill("my-skill") is not None
        assert engine.get_skill("my-skill", "1.0.0") is not None
        assert engine.get_skill("nonexistent") is None

    def test_list_skills_by_state(self):
        engine = UniSkillEngine()
        skill1 = SkillMetadata(name="s1", version="1.0.0", lifecycle_state=SkillLifecycleState.SHIP)
        skill2 = SkillMetadata(name="s2", version="1.0.0", lifecycle_state=SkillLifecycleState.INIT)

        engine.register_skill(skill1)
        engine.register_skill(skill2)

        shipped = engine.list_skills(state=SkillLifecycleState.SHIP)
        assert len(shipped) == 1
        assert shipped[0].name == "s1"


class TestEngineConfig:
    """Test engine configuration."""

    def test_default_config(self):
        config = EngineConfig()
        assert config.marketplace_enabled
        assert config.context_compression_enabled
        assert config.compression_algorithm == "smart_crusher"
        assert config.mcp_port == 8787
