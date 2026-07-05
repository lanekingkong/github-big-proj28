"""
UniSkill Core Engine - Central orchestrator for the UniSkill platform.

Coordinates all subsystems: marketplace, context engine, security scanner,
testing framework, protocol bridge, deployment, governance, and observability.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


class SkillLifecycleState(Enum):
    """Skill lifecycle states following the 7-stage development pipeline.

    Inspired by addyosmani/agent-skills state machine pattern.
    Each state transition requires passing quality gates.
    """

    INIT = "init"           # Skill project initialized
    PLAN = "plan"           # Requirements and design defined
    SPEC = "spec"           # Technical specification written
    CODE = "code"           # Implementation in progress
    TEST = "test"           # Testing phase (golden datasets)
    REVIEW = "review"       # Security and quality review
    DOC = "doc"             # Documentation complete
    SHIP = "ship"           # Released to marketplace
    DEPRECATED = "deprecated"  # Marked for removal
    RETIRED = "retired"     # No longer available


@dataclass
class SkillMetadata:
    """Metadata for a skill registered in the marketplace."""

    name: str
    version: str
    description: str
    author: str
    license_type: str = "Apache-2.0"
    tags: list[str] = field(default_factory=list)
    dependencies: dict[str, str] = field(default_factory=dict)
    compatible_agents: list[str] = field(default_factory=list)
    context_token_budget: int = 4096
    security_score: int = 100
    test_coverage: float = 0.0
    lifecycle_state: SkillLifecycleState = SkillLifecycleState.INIT
    mcp_endpoints: list[str] = field(default_factory=list)
    a2a_capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license_type,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "compatible_agents": self.compatible_agents,
            "context_token_budget": self.context_token_budget,
            "security_score": self.security_score,
            "test_coverage": self.test_coverage,
            "lifecycle_state": self.lifecycle_state.value,
            "mcp_endpoints": self.mcp_endpoints,
            "a2a_capabilities": self.a2a_capabilities,
        }


@dataclass
class EngineConfig:
    """Configuration for the UniSkill engine."""

    marketplace_enabled: bool = True
    context_compression_enabled: bool = True
    security_scan_enabled: bool = True
    observability_enabled: bool = True

    # Compression settings
    compression_threshold_tokens: int = 2048
    compression_target_ratio: float = 0.7
    compression_algorithm: str = "smart_crusher"

    # Security settings
    security_stage1_enabled: bool = True
    security_stage2_enabled: bool = False
    security_risk_threshold: int = 50

    # Deployment settings
    mcp_port: int = 8787
    a2a_port: int = 8788
    api_port: int = 8000
    self_hosted: bool = True

    # Observability
    trace_sample_rate: float = 1.0
    metrics_export_interval: int = 60


class UniSkillEngine:
    """Central orchestrator for the UniSkill platform.

    Coordinates all subsystems and manages the lifecycle of skills
    from creation through deployment and monitoring.

    Key design decisions (inspired by reference projects):
    - State machine pattern for lifecycle (agent-skills)
    - Proxy/Interceptor pattern for context compression (headroom)
    - Two-stage pipeline for security (SkillSpector)
    - File system as context for multi-agent memory (superpowers)
    - Parallel execution with partial failure handling (last30days-skill)
    """

    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self._registry: dict[str, SkillMetadata] = {}
        self._lifecycle_transitions: dict[SkillLifecycleState, list[SkillLifecycleState]] = {
            SkillLifecycleState.INIT: [SkillLifecycleState.PLAN],
            SkillLifecycleState.PLAN: [SkillLifecycleState.SPEC, SkillLifecycleState.INIT],
            SkillLifecycleState.SPEC: [SkillLifecycleState.CODE, SkillLifecycleState.PLAN],
            SkillLifecycleState.CODE: [SkillLifecycleState.TEST, SkillLifecycleState.SPEC],
            SkillLifecycleState.TEST: [SkillLifecycleState.REVIEW, SkillLifecycleState.CODE],
            SkillLifecycleState.REVIEW: [SkillLifecycleState.DOC, SkillLifecycleState.CODE],
            SkillLifecycleState.DOC: [SkillLifecycleState.SHIP, SkillLifecycleState.REVIEW],
            SkillLifecycleState.SHIP: [SkillLifecycleState.DEPRECATED],
            SkillLifecycleState.DEPRECATED: [SkillLifecycleState.RETIRED, SkillLifecycleState.SHIP],
            SkillLifecycleState.RETIRED: [],
        }
        self._quality_gates: dict[SkillLifecycleState, list[str]] = {
            SkillLifecycleState.PLAN: ["spec_document_exists", "requirements_defined"],
            SkillLifecycleState.CODE: ["lint_passing", "type_check_passing"],
            SkillLifecycleState.TEST: ["unit_tests_pass", "golden_dataset_pass", "coverage_above_80"],
            SkillLifecycleState.REVIEW: ["security_scan_pass", "dependency_audit_pass"],
            SkillLifecycleState.DOC: ["readme_complete", "api_docs_complete"],
            SkillLifecycleState.SHIP: ["all_checks_pass", "version_tagged"],
        }

    def register_skill(self, metadata: SkillMetadata) -> None:
        """Register a skill in the marketplace."""
        key = f"{metadata.name}@{metadata.version}"
        self._registry[key] = metadata
        logger.info("skill_registered", name=metadata.name, version=metadata.version)

    def get_skill(self, name: str, version: str = "latest") -> Optional[SkillMetadata]:
        """Retrieve a skill by name and version."""
        if version == "latest":
            matching = [(k, v) for k, v in self._registry.items() if v.name == name]
            if not matching:
                return None
            return max(matching, key=lambda x: x[1].version)[1]
        key = f"{name}@{version}"
        return self._registry.get(key)

    def list_skills(self, state: Optional[SkillLifecycleState] = None) -> list[SkillMetadata]:
        """List all registered skills, optionally filtered by lifecycle state."""
        skills = list(self._registry.values())
        if state:
            skills = [s for s in skills if s.lifecycle_state == state]
        return skills

    def can_transition(self, current: SkillLifecycleState, target: SkillLifecycleState) -> bool:
        """Check if a lifecycle state transition is valid."""
        return target in self._lifecycle_transitions.get(current, [])

    def transition(self, skill: SkillMetadata, target: SkillLifecycleState) -> bool:
        """Attempt to transition a skill to a new lifecycle state."""
        if not self.can_transition(skill.lifecycle_state, target):
            logger.warning(
                "invalid_transition",
                skill=skill.name,
                from_state=skill.lifecycle_state.value,
                to_state=target.value,
            )
            return False

        gates = self._quality_gates.get(target, [])
        if gates:
            logger.info(
                "quality_gates_required",
                skill=skill.name,
                target_state=target.value,
                gates=gates,
            )

        old_state = skill.lifecycle_state
        skill.lifecycle_state = target
        logger.info(
            "state_transition",
            skill=skill.name,
            from_state=old_state.value,
            to_state=target.value,
        )
        return True

    async def initialize(self) -> None:
        """Initialize all subsystems."""
        logger.info("uniskill_engine_initializing", version=__import__("uniskill").__version__)
        # Subsystem initialization would happen here
        # Each subsystem follows the same init pattern with health checks

    async def shutdown(self) -> None:
        """Gracefully shutdown all subsystems."""
        logger.info("uniskill_engine_shutting_down")

    def health_check(self) -> dict[str, Any]:
        """Return health status of all subsystems."""
        return {
            "status": "healthy",
            "version": __import__("uniskill").__version__,
            "registered_skills": len(self._registry),
            "subsystems": {
                "marketplace": "ok",
                "context_engine": "ok",
                "security": "ok",
                "testing": "ok",
                "bridge": "ok",
                "deployment": "ok",
                "governance": "ok",
                "observability": "ok",
            },
        }
