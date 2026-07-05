"""
Example: Security Scanning Pipeline

Demonstrates how UniSkill scans skills for security vulnerabilities
before deployment.
"""

from pathlib import Path
from uniskill.security import SecurityScanner
from uniskill.governance import GovernanceCenter, User, Permission, PIIRedactor


def scan_skill_example():
    """Scan a skill directory for vulnerabilities."""
    print("=" * 60)
    print("Security Scan Example")
    print("=" * 60)

    scanner = SecurityScanner()

    # Scan a directory
    scan_path = Path(__file__).parent
    result = scanner.scan_directory(scan_path)

    print(f"\nScanned: {result.skill_name}")
    print(f"Files: {result.total_files}")
    print(f"Risk Score: {result.risk_score}/100")
    print(f"Risk Level: {result.risk_level}")

    if result.vulnerabilities:
        print(f"\nFound {len(result.vulnerabilities)} vulnerabilities:")
        for v in result.vulnerabilities:
            print(f"  [{v.severity.value.upper()}] {v.rule_id}: {v.description[:80]}")
            print(f"       File: {v.file_path}:{v.line_number}")

    if result.passed:
        print("\nPASSED: No critical/high severity issues found.")
    else:
        print("\nFAILED: Critical or high severity issues detected!")


def pii_redaction_example():
    """Demonstrate PII redaction."""
    print("\n" + "=" * 60)
    print("PII Redaction Example")
    print("=" * 60)

    redactor = PIIRedactor()
    sample_text = """
    Customer: John Smith (john.smith@company.com)
    Phone: +1 (555) 123-4567
    SSN: 123-45-6789
    Card: 4111-1111-1111-1111
    API Key: api_key="sk-proj-abc123def456"
    AWS Key: AKIAIOSFODNN7EXAMPLE
    """

    redacted, mapping = redactor.redact(sample_text)
    print(f"\nOriginal text:")
    print(sample_text)
    print(f"\nRedacted text:")
    print(redacted)
    print(f"\nRedacted PII types: {list(mapping.keys())}")


def governance_example():
    """Demonstrate enterprise governance."""
    print("\n" + "=" * 60)
    print("Governance Example")
    print("=" * 60)

    gc = GovernanceCenter()

    # Create users
    admin = User(
        user_id="admin1",
        username="admin",
        permissions=[Permission.SKILL_ADMIN, Permission.SKILL_DEPLOY, Permission.SKILL_EXECUTE],
        department="Engineering",
    )

    developer = User(
        user_id="dev1",
        username="developer",
        permissions=[Permission.SKILL_READ, Permission.SKILL_WRITE, Permission.SKILL_EXECUTE],
        department="Engineering",
    )

    gc.create_user(admin)
    gc.create_user(developer)

    # Check permissions
    print(f"\nAdmin can deploy: {gc.check_permission('admin1', Permission.SKILL_DEPLOY)}")
    print(f"Developer can deploy: {gc.check_permission('dev1', Permission.SKILL_DEPLOY)}")

    # Audit trail
    trail = gc.get_audit_trail(5)
    print(f"\nRecent audit entries ({len(trail)}):")
    for entry in trail:
        print(f"  [{entry['timestamp']}] {entry['user']}: {entry['action']}")


if __name__ == "__main__":
    scan_skill_example()
    pii_redaction_example()
    governance_example()
