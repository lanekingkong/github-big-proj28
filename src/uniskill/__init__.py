"""
UniSkill - Universal Agent Capability Mesh
Enterprise AI Agent Skill Factory & Production Platform
"""

__version__ = "1.0.0"
__author__ = "lanekingkong"
__license__ = "Apache-2.0"

from uniskill.core import UniSkillEngine
from uniskill.marketplace import SkillRegistry, SkillDiscovery
from uniskill.context_engine import ContextManager, CompressorFactory
from uniskill.security import SecurityScanner, TaintTracker
from uniskill.testing import TestFramework, GoldenDataset
from uniskill.bridge import MCPServer, A2ARouter, AGUIBridge
from uniskill.deployment import DeploymentEngine
from uniskill.governance import GovernanceCenter, AuditTrail
from uniskill.observability import ObservabilityPipeline, MetricsCollector

__all__ = [
    "UniSkillEngine",
    "SkillRegistry",
    "SkillDiscovery",
    "ContextManager",
    "CompressorFactory",
    "SecurityScanner",
    "TaintTracker",
    "TestFramework",
    "GoldenDataset",
    "MCPServer",
    "A2ARouter",
    "AGUIBridge",
    "DeploymentEngine",
    "GovernanceCenter",
    "AuditTrail",
    "ObservabilityPipeline",
    "MetricsCollector",
]
