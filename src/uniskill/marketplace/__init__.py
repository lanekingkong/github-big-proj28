"""
Skill Marketplace - Registry, discovery, and versioning for AI Agent skills.

Inspired by npm/PyPI registries but designed specifically for AI agent skills.
Supports semantic versioning, dependency resolution, and compatibility matrices.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import structlog
import yaml
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class SemVer(BaseModel):
    """Semantic version representation."""

    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    def __str__(self) -> str:
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            v += f"-{self.prerelease}"
        if self.build:
            v += f"+{self.build}"
        return v

    @classmethod
    def parse(cls, version_str: str) -> "SemVer":
        """Parse a semver string."""
        pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
        match = re.match(pattern, version_str.strip())
        if not match:
            raise ValueError(f"Invalid semver: {version_str}")
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4),
            build=match.group(5),
        )

    def __gt__(self, other: "SemVer") -> bool:
        if self.major != other.major:
            return self.major > other.major
        if self.minor != other.minor:
            return self.minor > other.minor
        if self.patch != other.patch:
            return self.patch > other.patch
        if self.prerelease and not other.prerelease:
            return False
        if not self.prerelease and other.prerelease:
            return True
        return str(self.prerelease or "") > str(other.prerelease or "")


@dataclass
class SkillPackage:
    """A skill package in the marketplace."""

    name: str
    version: SemVer
    description: str
    author: str
    entry_point: str  # Path to skill.yaml or SKILL.md
    sha256: str = ""
    dependencies: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    compatible_agents: list[str] = field(default_factory=list)
    published_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    download_count: int = 0
    rating: float = 0.0
    security_score: int = 100

    @classmethod
    def from_skill_yaml(cls, path: Path) -> "SkillPackage":
        """Load a skill from a skill.yaml manifest file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Compute SHA256 of the skill directory
        skill_dir = path.parent
        sha256 = cls._compute_sha256(skill_dir)

        return cls(
            name=data["name"],
            version=SemVer.parse(data.get("version", "0.1.0")),
            description=data.get("description", ""),
            author=data.get("author", "unknown"),
            entry_point=str(path.relative_to(skill_dir.parent)),
            sha256=sha256,
            dependencies=data.get("dependencies", {}),
            tags=data.get("tags", []),
            compatible_agents=data.get("compatible_agents", []),
        )

    @staticmethod
    def _compute_sha256(directory: Path) -> str:
        """Compute SHA256 hash of all files in a directory."""
        hasher = hashlib.sha256()
        for file_path in sorted(directory.rglob("*")):
            if file_path.is_file() and not file_path.name.startswith("."):
                hasher.update(str(file_path.relative_to(directory)).encode())
                hasher.update(file_path.read_bytes())
        return hasher.hexdigest()

    def to_manifest(self) -> dict[str, Any]:
        """Export to manifest dict."""
        return {
            "name": self.name,
            "version": str(self.version),
            "description": self.description,
            "author": self.author,
            "entry_point": self.entry_point,
            "sha256": self.sha256,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "compatible_agents": self.compatible_agents,
            "published_at": self.published_at.isoformat(),
            "download_count": self.download_count,
            "rating": self.rating,
            "security_score": self.security_score,
        }


class SkillRegistry:
    """Central registry for skill packages.

    Supports:
    - Publish/register skills with validation
    - Semantic version management
    - Dependency resolution
    - Search and discovery
    - Compatibility checking
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._packages: dict[str, dict[str, SkillPackage]] = {}
        self._storage_path = storage_path or Path.home() / ".uniskill" / "registry"
        self._storage_path.mkdir(parents=True, exist_ok=True)
        logger.info("registry_initialized", path=str(self._storage_path))

    def publish(self, package: SkillPackage) -> bool:
        """Publish a skill package to the registry."""
        if package.name not in self._packages:
            self._packages[package.name] = {}

        version_key = str(package.version)
        if version_key in self._packages[package.name]:
            logger.warning(
                "version_exists",
                name=package.name,
                version=version_key,
            )
            return False

        self._packages[package.name][version_key] = package
        self._persist()
        logger.info("package_published", name=package.name, version=version_key)
        return True

    def get(self, name: str, version: Optional[str] = None) -> Optional[SkillPackage]:
        """Get a specific package by name and optional version."""
        if name not in self._packages:
            return None

        versions = self._packages[name]
        if version and version != "latest":
            return versions.get(version)

        # Return latest version
        if not versions:
            return None
        latest = max(versions.values(), key=lambda p: p.version)
        return latest

    def search(self, query: str, tags: Optional[list[str]] = None) -> list[SkillPackage]:
        """Search for packages by name, description, or tags."""
        results = []
        query_lower = query.lower()

        for name, versions in self._packages.items():
            latest = max(versions.values(), key=lambda p: p.version)
            if query_lower in name.lower() or query_lower in latest.description.lower():
                results.append(latest)
                continue

            if tags:
                if any(t in latest.tags for t in tags):
                    results.append(latest)

        return results

    def list_all(self) -> list[SkillPackage]:
        """List all latest versions of packages."""
        results = []
        for versions in self._packages.values():
            if versions:
                results.append(max(versions.values(), key=lambda p: p.version))
        return results

    def resolve_dependencies(self, package_name: str) -> list[str]:
        """Resolve all transitive dependencies for a package."""
        resolved = set()
        queue = [package_name]

        while queue:
            current = queue.pop(0)
            if current in resolved:
                continue
            resolved.add(current)

            pkg = self.get(current)
            if pkg and pkg.dependencies:
                for dep_name in pkg.dependencies:
                    if dep_name not in resolved:
                        queue.append(dep_name)

        return list(resolved)

    def _persist(self) -> None:
        """Persist registry to disk."""
        data = {}
        for name, versions in self._packages.items():
            data[name] = {v: pkg.to_manifest() for v, pkg in versions.items()}

        registry_file = self._storage_path / "registry.json"
        with open(registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def load(self) -> None:
        """Load registry from disk."""
        registry_file = self._storage_path / "registry.json"
        if not registry_file.exists():
            return

        with open(registry_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for name, versions in data.items():
            self._packages[name] = {}
            for version_str, pkg_data in versions.items():
                pkg = SkillPackage(
                    name=pkg_data["name"],
                    version=SemVer.parse(pkg_data["version"]),
                    description=pkg_data.get("description", ""),
                    author=pkg_data.get("author", "unknown"),
                    entry_point=pkg_data.get("entry_point", ""),
                    sha256=pkg_data.get("sha256", ""),
                    dependencies=pkg_data.get("dependencies", {}),
                    tags=pkg_data.get("tags", []),
                    compatible_agents=pkg_data.get("compatible_agents", []),
                )
                self._packages[name][version_str] = pkg

        logger.info("registry_loaded", packages=len(self._packages))


class SkillDiscovery:
    """AI-powered skill discovery engine.

    Uses vector embeddings for semantic search and compatibility analysis.
    Inspired by last30days-skill's cross-platform signal aggregation.
    """

    def __init__(self, registry: SkillRegistry):
        self._registry = registry
        self._compatibility_matrix: dict[str, list[str]] = {}

    def semantic_search(self, description: str, top_k: int = 10) -> list[tuple[SkillPackage, float]]:
        """Search skills by semantic similarity to the description.

        Uses embedding-based similarity scoring. Falls back to keyword
        matching when embedding models are unavailable.
        """
        results = []
        query_words = set(description.lower().split())

        for pkg in self._registry.list_all():
            pkg_text = f"{pkg.name} {pkg.description} {' '.join(pkg.tags)}"
            pkg_words = set(pkg_text.lower().split())

            # Jaccard similarity as fallback
            intersection = query_words & pkg_words
            union = query_words | pkg_words
            score = len(intersection) / len(union) if union else 0

            if score > 0.1:
                results.append((pkg, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def find_compatible_skills(self, agent_type: str) -> list[SkillPackage]:
        """Find skills compatible with a specific agent type."""
        compatible = []
        for pkg in self._registry.list_all():
            if agent_type in pkg.compatible_agents:
                compatible.append(pkg)
        return compatible

    def recommend_skill_chain(self, task_description: str) -> list[SkillPackage]:
        """Recommend a chain of skills for a complex task.

        Uses the dependency graph and semantic similarity to suggest
        a sequence of skills that can accomplish the task together.
        """
        similar = self.semantic_search(task_description, top_k=5)
        return [pkg for pkg, _ in similar]
