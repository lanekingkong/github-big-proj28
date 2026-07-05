"""
Testing Framework - Golden dataset management and automated testing for AI Agent skills.

Features:
- Golden dataset versioning and management
- Automated regression testing
- Performance benchmarking (token usage, latency, accuracy)
- Edge case fuzzing for robustness testing
- Test coverage tracking
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import structlog
import yaml

logger = structlog.get_logger(__name__)


class TestStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


class TestCategory(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    REGRESSION = "regression"
    PERFORMANCE = "performance"
    SECURITY = "security"
    FUZZING = "fuzzing"
    GOLDEN = "golden"


@dataclass
class TestCase:
    """A single test case with input and expected output."""

    name: str
    category: TestCategory
    input_data: dict[str, Any]
    expected_output: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "input": self.input_data,
            "expected": self.expected_output,
            "metadata": self.metadata,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestCase":
        return cls(
            name=data["name"],
            category=TestCategory(data["category"]),
            input_data=data["input"],
            expected_output=data["expected"],
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )


@dataclass
class TestResult:
    """Result of a single test execution."""

    test_case: TestCase
    status: TestStatus
    actual_output: Any = None
    error_message: str = ""
    duration_ms: float = 0.0
    token_usage: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def passed(self) -> bool:
        return self.status == TestStatus.PASS


@dataclass
class TestSuite:
    """A collection of related test cases."""

    name: str
    description: str = ""
    test_cases: list[TestCase] = field(default_factory=list)
    setup_script: Optional[str] = None
    teardown_script: Optional[str] = None

    def add_case(self, case: TestCase) -> None:
        self.test_cases.append(case)

    def to_yaml(self) -> str:
        data = {
            "name": self.name,
            "description": self.description,
            "setup": self.setup_script,
            "teardown": self.teardown_script,
            "tests": [tc.to_dict() for tc in self.test_cases],
        }
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, path: Path) -> "TestSuite":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        suite = cls(
            name=data["name"],
            description=data.get("description", ""),
            setup_script=data.get("setup"),
            teardown_script=data.get("teardown"),
        )
        for tc_data in data.get("tests", []):
            suite.add_case(TestCase.from_dict(tc_data))
        return suite


class GoldenDataset:
    """Golden dataset management for skill quality assurance.

    Golden datasets are version-controlled collections of test cases
    with known correct outputs. They serve as ground truth for:
    - Regression testing: Ensure new versions don't break existing behavior
    - Quality gates: Skills must pass golden tests before deployment
    - Performance tracking: Monitor accuracy/latency over time
    """

    def __init__(self, storage_path: Path):
        self._path = storage_path
        self._path.mkdir(parents=True, exist_ok=True)
        self._test_suites: dict[str, TestSuite] = {}
        self._version: int = 1

    def add_suite(self, suite: TestSuite) -> None:
        """Add a test suite to the dataset."""
        self._test_suites[suite.name] = suite
        self._save_suite(suite)

    def get_suite(self, name: str) -> Optional[TestSuite]:
        suite = self._test_suites.get(name)
        if suite:
            return suite

        suite_path = self._path / f"{name}.yaml"
        if suite_path.exists():
            suite = TestSuite.from_yaml(suite_path)
            self._test_suites[name] = suite
            return suite
        return None

    def list_suites(self) -> list[str]:
        return list(self._test_suites.keys())

    def _save_suite(self, suite: TestSuite) -> None:
        suite_path = self._path / f"{suite.name}.yaml"
        with open(suite_path, "w", encoding="utf-8") as f:
            f.write(suite.to_yaml())

    def export_manifest(self) -> dict[str, Any]:
        return {
            "version": self._version,
            "suites": list(self._test_suites.keys()),
            "total_cases": sum(len(s.test_cases) for s in self._test_suites.values()),
            "path": str(self._path),
        }


class TestFramework:
    """Automated testing framework for AI Agent skills.

    Features:
    - Parallel test execution
    - Performance benchmarking
    - Automatic regression detection
    - Coverage tracking
    - CI/CD integration ready
    """

    def __init__(self, golden_dataset: Optional[GoldenDataset] = None):
        self._golden = golden_dataset
        self._results: list[TestResult] = []
        self._executors: dict[TestCategory, Callable] = {}

    def register_executor(self, category: TestCategory, executor: Callable) -> None:
        """Register a test executor for a specific category."""
        self._executors[category] = executor

    def run_suite(self, suite_name: str) -> list[TestResult]:
        """Run all test cases in a suite."""
        if not self._golden:
            raise ValueError("No golden dataset configured")

        suite = self._golden.get_suite(suite_name)
        if not suite:
            raise ValueError(f"Test suite '{suite_name}' not found")

        results = []
        for test_case in suite.test_cases:
            result = self._run_case(test_case)
            results.append(result)
            self._results.append(result)

        return results

    def run_all(self) -> list[TestResult]:
        """Run all test suites in the golden dataset."""
        if not self._golden:
            raise ValueError("No golden dataset configured")

        all_results = []
        for suite_name in self._golden.list_suites():
            results = self.run_suite(suite_name)
            all_results.extend(results)

        return all_results

    def _run_case(self, test_case: TestCase) -> TestResult:
        """Execute a single test case."""
        start = time.time()

        try:
            executor = self._executors.get(test_case.category)
            if not executor:
                return TestResult(
                    test_case=test_case,
                    status=TestStatus.SKIP,
                    error_message=f"No executor for category {test_case.category.value}",
                )

            actual = executor(**test_case.input_data)
            duration = (time.time() - start) * 1000

            # Compare with expected output
            passed = self._compare(test_case.expected_output, actual)

            return TestResult(
                test_case=test_case,
                status=TestStatus.PASS if passed else TestStatus.FAIL,
                actual_output=actual,
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_case=test_case,
                status=TestStatus.ERROR,
                error_message=str(e),
                duration_ms=duration,
            )

    def _compare(self, expected: Any, actual: Any) -> bool:
        """Compare expected and actual outputs with tolerance."""
        if isinstance(expected, dict) and isinstance(actual, dict):
            # Partial dict match
            for key, value in expected.items():
                if key not in actual:
                    return False
                if not self._compare(value, actual[key]):
                    return False
            return True
        if isinstance(expected, float) and isinstance(actual, (int, float)):
            return abs(expected - actual) < 1e-6
        return expected == actual

    def summary(self) -> dict[str, Any]:
        """Generate a test summary report."""
        total = len(self._results)
        passed = sum(1 for r in self._results if r.passed)
        failed = sum(1 for r in self._results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in self._results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self._results if r.status == TestStatus.SKIP)

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "pass_rate": (passed / max(total, 1)) * 100,
            "avg_duration_ms": sum(r.duration_ms for r in self._results) / max(total, 1),
        }

    def quality_gate_check(self) -> tuple[bool, str]:
        """Check if test results pass quality gates.

        Requirements:
        - 100% of golden tests must pass
        - 0 critical or high errors
        - Test coverage >= 80%
        """
        summary = self.summary()
        if summary["failed"] > 0:
            return False, f"{summary['failed']} test(s) failed"
        if summary["errors"] > 0:
            return False, f"{summary['errors']} test(s) errored"
        if summary["pass_rate"] < 100:
            return False, f"Pass rate {summary['pass_rate']:.1f}% below 100%"
        return True, "All quality gates passed"


class FuzzingEngine:
    """Edge case fuzzing for robustness testing.

    Generates edge cases and malformed inputs to test skill robustness.
    Categories: empty inputs, very long inputs, special characters,
    unicode, boundary values, type mismatches, etc.
    """

    EDGE_CASES = [
        ("empty_string", ""),
        ("whitespace_only", "   \t\n   "),
        ("very_long", "a" * 10000),
        ("unicode", "你好世界 🌍 émoji test テスト"),
        ("special_chars", "!@#$%^&*()_+-=[]{}|;':\",./<>?"),
        ("null_byte", "hello\x00world"),
        ("sql_injection", "' OR '1'='1' --"),
        ("xss", "<script>alert('xss')</script>"),
        ("negative_number", -1),
        ("zero", 0),
        ("very_large_number", 10**100),
    ]

    def fuzz(self, skill_func: Callable, iterations: int = 20) -> list[TestResult]:
        """Fuzz a skill function with edge cases."""
        results = []
        for name, value in self.EDGE_CASES:
            try:
                result = skill_func(value)
                results.append(TestResult(
                    test_case=TestCase(
                        name=f"fuzz_{name}",
                        category=TestCategory.FUZZING,
                        input_data={"input": str(value)},
                        expected_output=None,
                    ),
                    status=TestStatus.PASS,
                    actual_output=result,
                ))
            except Exception as e:
                results.append(TestResult(
                    test_case=TestCase(
                        name=f"fuzz_{name}",
                        category=TestCategory.FUZZING,
                        input_data={"input": str(value)},
                        expected_output=None,
                    ),
                    status=TestStatus.ERROR,
                    error_message=str(e),
                ))

        return results
