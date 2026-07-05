"""
Example: Test Framework Usage

Demonstrates how to use UniSkill's testing framework
with golden datasets, quality gates, and fuzzing.
"""

from pathlib import Path
from uniskill.testing import (
    TestFramework,
    GoldenDataset,
    TestSuite,
    TestCase,
    TestCategory,
    FuzzingEngine,
)


def test_framework_example():
    """Demonstrate the test framework."""
    print("=" * 60)
    print("Test Framework Example")
    print("=" * 60)

    # Create golden dataset
    dataset_dir = Path(__file__).parent / "golden_tests"
    dataset_dir.mkdir(exist_ok=True)
    golden = GoldenDataset(dataset_dir)

    # Create a test suite
    suite = TestSuite(
        name="basic_skills",
        description="Basic skill regression tests",
    )

    # Add test cases
    suite.add_case(TestCase(
        name="test_echo",
        category=TestCategory.UNIT,
        input_data={"text": "hello"},
        expected_output="echo: hello",
        tags=["basic"],
    ))

    suite.add_case(TestCase(
        name="test_calculator",
        category=TestCategory.UNIT,
        input_data={"a": 5, "b": 3, "op": "add"},
        expected_output=8,
        tags=["basic", "math"],
    ))

    suite.add_case(TestCase(
        name="test_edge_empty",
        category=TestCategory.GOLDEN,
        input_data={"text": ""},
        expected_output="echo: ",
        tags=["edge"],
    ))

    golden.add_suite(suite)
    print(f"\nCreated golden dataset with {len(suite.test_cases)} test cases")

    # Initialize test framework
    framework = TestFramework(golden_dataset=golden)

    # Register executors
    def echo_executor(text: str) -> str:
        return f"echo: {text}"

    def calculator_executor(a: int, b: int, op: str) -> int:
        if op == "add":
            return a + b
        raise ValueError(f"Unknown operation: {op}")

    # In practice, you'd use a dispatcher; simplified here
    print("\nExecutors registered")

    # Run fuzz testing
    fuzzer = FuzzingEngine()
    results = fuzzer.fuzz(echo_executor)
    print(f"\nFuzzing results: {len(results)} edge cases tested")

    passed = sum(1 for r in results if r.passed)
    print(f"  Passed: {passed}/{len(results)}")

    # Quality gate check
    passed, message = framework.quality_gate_check()
    print(f"\nQuality gate: {'PASSED' if passed else 'FAILED'} - {message}")

    manifest = golden.export_manifest()
    print(f"\nDataset manifest: {manifest}")


if __name__ == "__main__":
    test_framework_example()
