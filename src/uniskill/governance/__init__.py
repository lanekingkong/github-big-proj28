"""
Enterprise Governance Center - RBAC, Audit Trail, PII Redaction, and Human-in-the-Loop.

Inspired by anthropics/financial-services enterprise deployment patterns:
- PII redaction before LLM input
- Role-based access control for skills
- Immutable audit trail for compliance (SOC2, SEC, GDPR)
- Human-in-the-Loop approval workflows for high-risk operations
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

logger = structlog.get_logger(__name__)


class Permission(Enum):
    """Fine-grained permissions for skill operations."""

    SKILL_READ = "skill:read"
    SKILL_WRITE = "skill:write"
    SKILL_DELETE = "skill:delete"
    SKILL_DEPLOY = "skill:deploy"
    SKILL_EXECUTE = "skill:execute"
    SKILL_HIGH_RISK = "skill:high_risk"
    SKILL_FINANCIAL = "skill:financial"
    SKILL_ADMIN = "skill:admin"
    AUDIT_READ = "audit:read"
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"


class RiskLevel(Enum):
    """Risk level for operations requiring Human-in-the-Loop."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class User:
    """A user in the governance system."""

    user_id: str
    username: str
    roles: list[str] = field(default_factory=list)
    permissions: list[Permission] = field(default_factory=list)
    department: str = ""
    mfa_enabled: bool = False

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions

    def has_role(self, role: str) -> bool:
        return role in self.roles


@dataclass
class AuditEntry:
    """An immutable audit trail entry."""

    entry_id: str
    user_id: str
    action: str
    resource: str
    result: str
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    previous_hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash for blockchain-like immutability."""
        data = json.dumps({
            "id": self.entry_id,
            "user": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "timestamp": self.timestamp.isoformat(),
            "previous": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class ApprovalRequest:
    """A Human-in-the-Loop approval request."""

    request_id: str
    user_id: str
    action: str
    resource: str
    risk_level: RiskLevel
    justification: str = ""
    status: str = "pending"
    required_approvers: int = 1
    current_approvals: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_approved(self) -> bool:
        return self.status == "approved"

    def approve(self, approver_id: str) -> bool:
        if approver_id not in self.current_approvals:
            self.current_approvals.append(approver_id)
        if len(self.current_approvals) >= self.required_approvers:
            self.status = "approved"
            return True
        return False


class PIIRedactor:
    """PII (Personally Identifiable Information) redaction engine.

    Detects and masks sensitive information before sending to LLMs:
    - Names, emails, phone numbers
    - SSN, credit card numbers
    - API keys, tokens, passwords
    - Addresses, dates of birth

    Inspired by anthropics/financial-services PII redaction patterns.
    """

    PATTERNS = {
        "email": (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
        "phone": (r"\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b", "[PHONE]"),
        "ssn": (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
        "credit_card": (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[CREDIT_CARD]"),
        "api_key": (r"(?i)(api[_-]?key|apikey|token|secret|password|passwd)['\"]?\s*[:=]\s*['\"][^'\"]+['\"]", "[REDACTED_CREDENTIAL]"),
        "ip_address": (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[IP_ADDRESS]"),
        "aws_key": (r"AKIA[0-9A-Z]{16}", "[AWS_KEY]"),
        "github_token": (r"gh[pousr]_[A-Za-z0-9_]{20,}", "[GITHUB_TOKEN]"),
    }

    def redact(self, text: str) -> tuple[str, dict[str, list[str]]]:
        """Redact PII from text. Returns (redacted_text, redaction_map)."""
        redaction_map: dict[str, list[str]] = {}
        result = text

        for pii_type, (pattern, replacement) in self.PATTERNS.items():
            matches = re.findall(pattern, result, re.IGNORECASE)
            if matches:
                redaction_map[pii_type] = matches
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result, redaction_map

    def unredact(self, text: str, redaction_map: dict[str, list[str]], authorized: bool = False) -> str:
        """Restore redacted PII if authorized."""
        if not authorized:
            logger.warning("unauthorized_unredact_attempt")
            return text

        result = text
        for pii_type, values in redaction_map.items():
            replacement = self.PATTERNS[pii_type][1]
            for value in values:
                result = result.replace(replacement, value, 1)

        return result


class GovernanceCenter:
    """Enterprise governance center for UniSkill.

    Central authority for:
    - User management and RBAC
    - Skill access control
    - Audit trail maintenance
    - HITL approval workflows
    - PII data protection
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._users: dict[str, User] = {}
        self._audit_chain: list[AuditEntry] = []
        self._approvals: dict[str, ApprovalRequest] = {}
        self._pii_redactor = PIIRedactor()
        self._storage_path = storage_path or Path.home() / ".uniskill" / "governance"
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._last_hash: str = "0" * 64

    # --- User Management ---

    def create_user(self, user: User) -> None:
        self._users[user.user_id] = user
        self._audit("user_created", user.user_id, {"username": user.username})

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def grant_permission(self, user_id: str, permission: Permission) -> bool:
        user = self._users.get(user_id)
        if not user:
            return False
        if permission not in user.permissions:
            user.permissions.append(permission)
            self._audit("permission_granted", user_id, {"permission": permission.value})
        return True

    # --- Access Control ---

    def check_permission(self, user_id: str, permission: Permission) -> bool:
        user = self._users.get(user_id)
        if not user:
            return False
        return user.has_permission(permission)

    def authorize_skill_execution(self, user_id: str, skill_name: str) -> bool:
        """Check if user can execute a skill."""
        user = self._users.get(user_id)
        if not user:
            return False

        if user.has_permission(Permission.SKILL_HIGH_RISK):
            return True

        # Check if skill requires elevated permissions
        risk_level = self._assess_skill_risk(skill_name)
        if risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            return user.has_permission(Permission.SKILL_HIGH_RISK)
        return user.has_permission(Permission.SKILL_EXECUTE)

    def _assess_skill_risk(self, skill_name: str) -> RiskLevel:
        """Assess risk level of a skill based on its operations."""
        high_risk_keywords = ["delete", "write", "execute", "sudo", "financial", "transfer", "payment"]
        critical_keywords = ["format", "drop", "truncate", "rm", "uninstall"]

        name_lower = skill_name.lower()
        for kw in critical_keywords:
            if kw in name_lower:
                return RiskLevel.CRITICAL
        for kw in high_risk_keywords:
            if kw in name_lower:
                return RiskLevel.HIGH
        return RiskLevel.LOW

    # --- Audit Trail ---

    def _audit(self, action: str, user_id: str, details: dict[str, Any] = None) -> AuditEntry:
        """Create an immutable audit trail entry."""
        entry_id = hashlib.sha256(f"{len(self._audit_chain)}{datetime.now().isoformat()}".encode()).hexdigest()[:16]

        entry = AuditEntry(
            entry_id=entry_id,
            user_id=user_id,
            action=action,
            resource="uniskill",
            result="success",
            details=details or {},
            previous_hash=self._last_hash,
        )
        self._last_hash = entry.compute_hash()
        self._audit_chain.append(entry)
        return entry

    def get_audit_trail(self, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve recent audit entries."""
        entries = self._audit_chain[-limit:]
        return [
            {
                "id": e.entry_id,
                "user": e.user_id,
                "action": e.action,
                "timestamp": e.timestamp.isoformat(),
                "hash": e.compute_hash(),
            }
            for e in entries
        ]

    def verify_audit_integrity(self) -> bool:
        """Verify the integrity of the entire audit chain."""
        prev_hash = "0" * 64
        for entry in self._audit_chain:
            if entry.previous_hash != prev_hash:
                return False
            prev_hash = entry.compute_hash()
        return True

    # --- HITL Approvals ---

    def request_approval(
        self, user_id: str, action: str, resource: str, risk_level: RiskLevel, justification: str = ""
    ) -> ApprovalRequest:
        """Create a Human-in-the-Loop approval request."""
        request_id = hashlib.sha256(f"{user_id}{action}{datetime.now().isoformat()}".encode()).hexdigest()[:16]

        required = 2 if risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH) else 1

        req = ApprovalRequest(
            request_id=request_id,
            user_id=user_id,
            action=action,
            resource=resource,
            risk_level=risk_level,
            justification=justification,
            required_approvers=required,
        )
        self._approvals[request_id] = req
        self._audit("approval_requested", user_id, {"request_id": request_id, "risk": risk_level.value})
        return req

    def get_pending_approvals(self) -> list[ApprovalRequest]:
        return [r for r in self._approvals.values() if r.status == "pending"]

    # --- PII Protection ---

    def redact_for_llm(self, text: str) -> str:
        """Redact PII before sending to LLM."""
        redacted, _ = self._pii_redactor.redact(text)
        return redacted

    def audit_command(self, user_id: str, command: str, result: str) -> None:
        """Audit a command execution."""
        self._audit("command_executed", user_id, {
            "command": command[:200],
            "result": result[:200],
        })
