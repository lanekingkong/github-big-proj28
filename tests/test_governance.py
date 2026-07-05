"""Test for governance module."""

import pytest
from uniskill.governance import (
    GovernanceCenter,
    User,
    Permission,
    RiskLevel,
    PIIRedactor,
    ApprovalRequest,
)


class TestPIIRedactor:
    """Test PII redaction."""

    def test_redact_email(self):
        redactor = PIIRedactor()
        text = "Contact me at john.doe@example.com for details."
        redacted, mapping = redactor.redact(text)

        assert "john.doe@example.com" not in redacted
        assert "[EMAIL]" in redacted
        assert "email" in mapping

    def test_redact_phone(self):
        redactor = PIIRedactor()
        text = "Call me at 555-123-4567 or 123.456.7890"
        redacted, _ = redactor.redact(text)

        assert "555-123-4567" not in redacted
        assert "[PHONE]" in redacted

    def test_redact_credit_card(self):
        redactor = PIIRedactor()
        text = "Card number: 4111-1111-1111-1111"
        redacted, _ = redactor.redact(text)

        assert "4111-1111-1111-1111" not in redacted
        assert "[CREDIT_CARD]" in redacted

    def test_redact_github_token(self):
        redactor = PIIRedactor()
        text = "Token is ghp_abc123def456ghi789jkl012"
        redacted, _ = redactor.redact(text)

        assert "ghp_" not in redacted.lower().replace("[github_token]", "").lower()

    def test_no_pii_text_preserved(self):
        redactor = PIIRedactor()
        text = "The weather is nice today."
        redacted, mapping = redactor.redact(text)

        assert redacted == text
        assert len(mapping) == 0


class TestGovernanceCenter:
    """Test governance center."""

    def test_create_user(self, tmp_path):
        gc = GovernanceCenter(storage_path=tmp_path)
        user = User(user_id="u1", username="alice", permissions=[Permission.SKILL_READ])
        gc.create_user(user)

        retrieved = gc.get_user("u1")
        assert retrieved is not None
        assert retrieved.username == "alice"

    def test_permission_check(self, tmp_path):
        gc = GovernanceCenter(storage_path=tmp_path)
        user = User(user_id="u1", username="alice", permissions=[Permission.SKILL_READ])
        gc.create_user(user)

        assert gc.check_permission("u1", Permission.SKILL_READ)
        assert not gc.check_permission("u1", Permission.SKILL_DELETE)

    def test_grant_permission(self, tmp_path):
        gc = GovernanceCenter(storage_path=tmp_path)
        user = User(user_id="u1", username="alice")
        gc.create_user(user)
        gc.grant_permission("u1", Permission.SKILL_EXECUTE)

        assert gc.check_permission("u1", Permission.SKILL_EXECUTE)

    def test_audit_trail(self, tmp_path):
        gc = GovernanceCenter(storage_path=tmp_path)
        gc._audit("test_action", "u1", {"detail": "value"})

        trail = gc.get_audit_trail()
        assert len(trail) > 0
        assert trail[-1]["action"] == "test_action"

    def test_audit_integrity(self, tmp_path):
        gc = GovernanceCenter(storage_path=tmp_path)
        gc._audit("action1", "u1")
        gc._audit("action2", "u1")

        assert gc.verify_audit_integrity()

    def test_approval_workflow(self, tmp_path):
        gc = GovernanceCenter(storage_path=tmp_path)
        req = gc.request_approval("u1", "delete_skill", "skill-x", RiskLevel.HIGH, "No longer needed")

        assert req.status == "pending"
        assert not req.is_approved

        req.approve("approver1")
        assert req.is_approved

    def test_skill_risk_assessment(self, tmp_path):
        gc = GovernanceCenter(storage_path=tmp_path)

        assert gc._assess_skill_risk("data-processor") == RiskLevel.LOW
        assert gc._assess_skill_risk("delete-files") == RiskLevel.HIGH
        assert gc._assess_skill_risk("format-disk") == RiskLevel.CRITICAL

    def test_authorize_skill_execution(self, tmp_path):
        gc = GovernanceCenter(storage_path=tmp_path)
        user = User(user_id="u1", username="alice", permissions=[Permission.SKILL_EXECUTE])
        gc.create_user(user)

        assert gc.authorize_skill_execution("u1", "data-processor")
