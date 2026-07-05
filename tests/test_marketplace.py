"""Tests for UniSkill marketplace module."""

import pytest
from uniskill.marketplace import (
    SemVer,
    SkillPackage,
    SkillRegistry,
    SkillDiscovery,
)


class TestSemVer:
    """Test semantic version parsing."""

    def test_parse_simple(self):
        v = SemVer.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert str(v) == "1.2.3"

    def test_parse_prerelease(self):
        v = SemVer.parse("2.0.0-alpha.1")
        assert v.prerelease == "alpha.1"

    def test_parse_build(self):
        v = SemVer.parse("1.0.0+build.123")
        assert v.build == "build.123"

    def test_invalid_semver(self):
        with pytest.raises(ValueError):
            SemVer.parse("not-a-version")

    def test_comparison(self):
        v1 = SemVer.parse("1.0.0")
        v2 = SemVer.parse("2.0.0")
        v3 = SemVer.parse("1.0.1")
        v4 = SemVer.parse("2.0.0-alpha")

        assert v2 > v1
        assert v3 > v1
        assert v2 > v4  # Release > prerelease


class TestSkillRegistry:
    """Test skill registry operations."""

    def test_publish_and_get(self, tmp_path):
        registry = SkillRegistry(storage_path=tmp_path)
        pkg = SkillPackage(
            name="test-pkg",
            version=SemVer.parse("1.0.0"),
            description="A test package",
            author="test-author",
            entry_point="skill.yaml",
        )

        assert registry.publish(pkg)
        retrieved = registry.get("test-pkg")
        assert retrieved is not None
        assert retrieved.name == "test-pkg"
        assert str(retrieved.version) == "1.0.0"

    def test_duplicate_version_rejected(self, tmp_path):
        registry = SkillRegistry(storage_path=tmp_path)
        pkg = SkillPackage(
            name="test-pkg",
            version=SemVer.parse("1.0.0"),
            description="A test package",
            author="test-author",
            entry_point="skill.yaml",
        )

        assert registry.publish(pkg)
        assert not registry.publish(pkg)  # Duplicate

    def test_latest_version(self, tmp_path):
        registry = SkillRegistry(storage_path=tmp_path)
        pkg1 = SkillPackage(name="test-pkg", version=SemVer.parse("1.0.0"), description="v1", author="test", entry_point="skill.yaml")
        pkg2 = SkillPackage(name="test-pkg", version=SemVer.parse("2.0.0"), description="v2", author="test", entry_point="skill.yaml")

        registry.publish(pkg1)
        registry.publish(pkg2)

        latest = registry.get("test-pkg", "latest")
        assert str(latest.version) == "2.0.0"

    def test_search(self, tmp_path):
        registry = SkillRegistry(storage_path=tmp_path)
        pkg1 = SkillPackage(name="data-processor", version=SemVer.parse("1.0.0"), description="Process data files", author="test", entry_point="skill.yaml", tags=["data", "etl"])
        pkg2 = SkillPackage(name="image-viewer", version=SemVer.parse("1.0.0"), description="View images", author="test", entry_point="skill.yaml", tags=["image"])

        registry.publish(pkg1)
        registry.publish(pkg2)

        results = registry.search("data")
        assert len(results) == 1
        assert results[0].name == "data-processor"

        results = registry.search("nonexistent")
        assert len(results) == 0

    def test_dependency_resolution(self, tmp_path):
        registry = SkillRegistry(storage_path=tmp_path)
        pkg1 = SkillPackage(name="app", version=SemVer.parse("1.0.0"), description="Main app", author="test", entry_point="skill.yaml", dependencies={"lib-a": "1.0.0"})
        pkg2 = SkillPackage(name="lib-a", version=SemVer.parse("1.0.0"), description="Library A", author="test", entry_point="skill.yaml", dependencies={"lib-b": "1.0.0"})
        pkg3 = SkillPackage(name="lib-b", version=SemVer.parse("1.0.0"), description="Library B", author="test", entry_point="skill.yaml")

        registry.publish(pkg1)
        registry.publish(pkg2)
        registry.publish(pkg3)

        deps = registry.resolve_dependencies("app")
        assert "app" in deps
        assert "lib-a" in deps
        assert "lib-b" in deps


class TestSkillDiscovery:
    """Test skill discovery engine."""

    def test_semantic_search(self, tmp_path):
        registry = SkillRegistry(storage_path=tmp_path)
        pkg1 = SkillPackage(name="weather-skill", version=SemVer.parse("1.0.0"), description="Get weather forecasts", author="test", entry_point="skill.yaml", tags=["weather", "api"])
        pkg2 = SkillPackage(name="stock-skill", version=SemVer.parse("1.0.0"), description="Track stock prices", author="test", entry_point="skill.yaml", tags=["finance", "api"])

        registry.publish(pkg1)
        registry.publish(pkg2)

        discovery = SkillDiscovery(registry)
        results = discovery.semantic_search("weather forecast temperature")

        assert len(results) > 0
        assert results[0][0].name == "weather-skill"
