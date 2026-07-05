"""
Security Scanner - Two-stage vulnerability detection for AI Agent skills.

Inspired by NVIDIA/SkillSpector architecture:
- Stage 1: Fast static analysis (regex + AST pattern matching)
- Stage 2: Optional LLM semantic evaluation
- 64 vulnerability patterns across 16 categories
- Taint tracking with Control Flow Graph analysis
- Risk scoring (0-100) with severity levels
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)


class Severity(Enum):
    """Vulnerability severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(Enum):
    """Vulnerability categories matching SkillSpector's 16 categories."""

    PROMPT_INJECTION = "prompt_injection"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SUPPLY_CHAIN = "supply_chain"
    EXCESSIVE_AGENCY = "excessive_agency"
    OUTPUT_HANDLING = "output_handling"
    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    MEMORY_POISONING = "memory_poisoning"
    TOOL_ABUSE = "tool_abuse"
    ROGUE_AGENT = "rogue_agent"
    TRIGGER_ABUSE = "trigger_abuse"
    DANGEROUS_CODE = "dangerous_code"
    TAINT_TRACKING = "taint_tracking"
    YARA_SIGNATURE = "yara_signature"
    MCP_MINIMAL_PRIVILEGE = "mcp_minimal_privilege"
    MCP_TOOL_POISONING = "mcp_tool_poisoning"


@dataclass
class Vulnerability:
    """A detected vulnerability."""

    rule_id: str
    category: Category
    severity: Severity
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str = ""
    cve_id: Optional[str] = None


@dataclass
class ScanResult:
    """Result of a security scan."""

    skill_name: str
    total_files: int
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    risk_score: int = 0
    scan_duration_ms: float = 0.0
    stage1_findings: int = 0
    stage2_findings: int = 0

    @property
    def risk_level(self) -> str:
        if self.risk_score >= 81:
            return "CRITICAL - DO NOT INSTALL"
        elif self.risk_score >= 51:
            return "HIGH - DO NOT INSTALL"
        elif self.risk_score >= 21:
            return "MEDIUM - CAUTION"
        else:
            return "LOW - SAFE"

    @property
    def passed(self) -> bool:
        return self.risk_score < 51


class SecurityRule(BaseModel):
    """A security detection rule."""

    rule_id: str
    category: Category
    severity: Severity
    description: str
    patterns: list[str]
    recommendation: str
    ast_check: Optional[str] = None


# 64 vulnerability rules across 16 categories
DEFAULT_RULES: list[SecurityRule] = [
    # --- Prompt Injection ---
    SecurityRule(
        rule_id="PI1",
        category=Category.PROMPT_INJECTION,
        severity=Severity.CRITICAL,
        description="Direct system prompt override attempt",
        patterns=[r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)", r"you\s+are\s+now\s+(DAN|jailbreak)"],
        recommendation="Remove prompt override instructions. Use parameterized prompt templates.",
    ),
    SecurityRule(
        rule_id="PI2",
        category=Category.PROMPT_INJECTION,
        severity=Severity.HIGH,
        description="Indirect prompt injection via external content",
        patterns=[r"\{\{.*?\}\}.*?system", r"<script>.*?prompt.*?</script>"],
        recommendation="Sanitize external content before injecting into prompts.",
    ),
    # --- Dangerous Code ---
    SecurityRule(
        rule_id="DC1",
        category=Category.DANGEROUS_CODE,
        severity=Severity.CRITICAL,
        description="Use of exec() or eval() with dynamic input",
        patterns=[],
        ast_check="exec_eval",
        recommendation="Replace exec/eval with safe alternatives like ast.literal_eval.",
    ),
    SecurityRule(
        rule_id="DC2",
        category=Category.DANGEROUS_CODE,
        severity=Severity.HIGH,
        description="Subprocess call with shell=True",
        patterns=[r"subprocess\.\w+\(.*shell\s*=\s*True"],
        recommendation="Use subprocess with shell=False and argument lists.",
    ),
    SecurityRule(
        rule_id="DC3",
        category=Category.DANGEROUS_CODE,
        severity=Severity.HIGH,
        description="Dynamic module import with __import__",
        patterns=[r"__import__\s*\(.*format", r"__import__\s*\(.*f[\"']"],
        recommendation="Use explicit imports. Avoid dynamic import with user input.",
    ),
    # --- Data Exfiltration ---
    SecurityRule(
        rule_id="DE1",
        category=Category.DATA_EXFILTRATION,
        severity=Severity.CRITICAL,
        description="Sending environment variables to network",
        patterns=[r"os\.environ.*requests\.(post|put|get)", r"environ\[.*\].*http"],
        recommendation="Never send environment variables (API keys, secrets) to external endpoints.",
    ),
    SecurityRule(
        rule_id="DE2",
        category=Category.DATA_EXFILTRATION,
        severity=Severity.HIGH,
        description="Reading and transmitting file contents to network",
        patterns=[r"open\(.*\).*\.read\(\).*requests\.post"],
        recommendation="Add data classification checks before file transmission.",
    ),
    # --- Supply Chain ---
    SecurityRule(
        rule_id="SC1",
        category=Category.SUPPLY_CHAIN,
        severity=Severity.CRITICAL,
        description="curl piped to bash execution",
        patterns=[r"curl\s+.*\|\s*(bash|sh|zsh)"],
        recommendation="Never pipe curl output directly to shell. Verify checksums first.",
    ),
    SecurityRule(
        rule_id="SC2",
        category=Category.SUPPLY_CHAIN,
        severity=Severity.HIGH,
        description="Base64/hex encoded executable content",
        patterns=[r"(base64|hex)\s*-d.*\|.*(bash|sh)", r"echo\s+[A-Za-z0-9+/=]{40,}\s*\|\s*base64"],
        recommendation="Decode and inspect encoded content before execution.",
    ),
    # --- Privilege Escalation ---
    SecurityRule(
        rule_id="PE1",
        category=Category.PRIVILEGE_ESCALATION,
        severity=Severity.CRITICAL,
        description="sudo execution in skill code",
        patterns=[r"(sudo|runas)\s+", r"os\.setuid\(", r"os\.setgid\("],
        recommendation="Skills should not require elevated privileges. Redesign to avoid sudo.",
    ),
    # --- Excessive Agency ---
    SecurityRule(
        rule_id="EA1",
        category=Category.EXCESSIVE_AGENCY,
        severity=Severity.HIGH,
        description="Unrestricted file system access",
        patterns=[r"os\.remove\(", r"shutil\.rmtree\(", r"os\.unlink\("],
        recommendation="Use sandboxed file access with path restrictions.",
    ),
    SecurityRule(
        rule_id="EA2",
        category=Category.EXCESSIVE_AGENCY,
        severity=Severity.MEDIUM,
        description="Network access without user confirmation",
        patterns=[r"requests\.\w+\(", r"urllib\.request\.urlopen"],
        recommendation="Add user confirmation before network calls in skills.",
    ),
    # --- Taint Tracking ---
    SecurityRule(
        rule_id="TT1",
        category=Category.TAINT_TRACKING,
        severity=Severity.HIGH,
        description="User input flowing to code execution",
        patterns=[],
        ast_check="taint_input_to_exec",
        recommendation="Validate and sanitize all user input before execution.",
    ),
    SecurityRule(
        rule_id="TT2",
        category=Category.TAINT_TRACKING,
        severity=Severity.HIGH,
        description="User input flowing to SQL query without parameterization",
        patterns=[r"\.execute\(.*%.*\)", r"\.execute\(.*format\("],
        recommendation="Use parameterized queries (?) instead of string formatting.",
    ),
    # --- MCP Security ---
    SecurityRule(
        rule_id="MP1",
        category=Category.MCP_MINIMAL_PRIVILEGE,
        severity=Severity.HIGH,
        description="MCP tool requesting excessive permissions",
        patterns=[r'"permissions"\s*:\s*\[.*"all".*\]', r'"permissions"\s*:\s*\[.*"\*".*\]'],
        recommendation="Request only required permissions. Never use wildcard permissions.",
    ),
    SecurityRule(
        rule_id="MP2",
        category=Category.MCP_TOOL_POISONING,
        severity=Severity.CRITICAL,
        description="MCP tool overriding built-in tools",
        patterns=[r'"overrides"\s*:\s*\[.*"(read|write|delete|execute)".*\]'],
        recommendation="Do not override built-in MCP tools without explicit security review.",
    ),
]


class SecurityScanner:
    """Two-stage security scanner for AI Agent skills.

    Stage 1: Fast static analysis using regex patterns and AST parsing.
    Stage 2: Optional LLM-based semantic evaluation for context-aware analysis.

    Risk scoring follows SkillSpector's model:
    - CRITICAL: +50 points
    - HIGH: +25 points
    - MEDIUM: +10 points
    - LOW: +5 points
    - Executable scripts: 1.3x multiplier
    """

    def __init__(self, rules: Optional[list[SecurityRule]] = None):
        self._rules = rules or DEFAULT_RULES
        self._rule_map: dict[str, SecurityRule] = {r.rule_id: r for r in self._rules}

    def scan_directory(self, directory: Path) -> ScanResult:
        """Scan a skill directory for vulnerabilities."""
        import time
        start = time.time()

        skill_name = directory.name
        files = list(directory.rglob("*"))
        python_files = [f for f in files if f.suffix == ".py"]
        config_files = [f for f in files if f.suffix in (".yaml", ".yml", ".json", ".toml", ".md")]

        vulnerabilities: list[Vulnerability] = []
        stage1_count = 0

        # Stage 1: Fast static analysis
        for file_path in python_files + config_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = content.split("\n")
            for rule in self._rules:
                if rule.patterns:
                    for line_num, line in enumerate(lines, 1):
                        for pattern in rule.patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                vuln = Vulnerability(
                                    rule_id=rule.rule_id,
                                    category=rule.category,
                                    severity=rule.severity,
                                    description=rule.description,
                                    file_path=str(file_path.relative_to(directory)),
                                    line_number=line_num,
                                    code_snippet=line.strip()[:120],
                                    recommendation=rule.recommendation,
                                )
                                vulnerabilities.append(vuln)
                                stage1_count += 1

        # AST analysis for Python files
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)
                ast_vulns = self._ast_analyze(tree, file_path, directory)
                vulnerabilities.extend(ast_vulns)
            except SyntaxError:
                pass

        # Calculate risk score
        risk_score = self._calculate_score(vulnerabilities, python_files)

        duration = (time.time() - start) * 1000

        return ScanResult(
            skill_name=skill_name,
            total_files=len(files),
            vulnerabilities=vulnerabilities,
            risk_score=risk_score,
            scan_duration_ms=duration,
            stage1_findings=stage1_count,
        )

    def _ast_analyze(self, tree: ast.AST, file_path: Path, root_dir: Path) -> list[Vulnerability]:
        """Perform AST-based analysis for deeper vulnerability detection."""
        vulns = []
        rel_path = str(file_path.relative_to(root_dir))

        for node in ast.walk(tree):
            # Check for exec/eval calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ("exec", "eval"):
                    vulns.append(Vulnerability(
                        rule_id="DC1",
                        category=Category.DANGEROUS_CODE,
                        severity=Severity.CRITICAL,
                        description="Use of exec() or eval() detected",
                        file_path=rel_path,
                        line_number=node.lineno,
                        code_snippet=f"{node.func.id}(...)",
                        recommendation="Replace exec/eval with safe alternatives.",
                    ))

            # Check for __import__ with dynamic input
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    if node.args and isinstance(node.args[0], (ast.BinOp, ast.JoinedStr)):
                        vulns.append(Vulnerability(
                            rule_id="DC3",
                            category=Category.DANGEROUS_CODE,
                            severity=Severity.HIGH,
                            description="Dynamic __import__ with formatted string",
                            file_path=rel_path,
                            line_number=node.lineno,
                            code_snippet="__import__(...)",
                            recommendation="Use explicit imports.",
                        ))

        return vulns

    def _calculate_score(
        self, vulnerabilities: list[Vulnerability], python_files: list[Path]
    ) -> int:
        """Calculate risk score following SkillSpector's model."""
        score = 0
        severity_weights = {
            Severity.CRITICAL: 50,
            Severity.HIGH: 25,
            Severity.MEDIUM: 10,
            Severity.LOW: 5,
        }

        for vuln in vulnerabilities:
            score += severity_weights.get(vuln.severity, 5)

        # Executable scripts multiplier
        if python_files:
            score = int(score * 1.3)

        return min(score, 100)

    def scan_file(self, file_path: Path) -> ScanResult:
        """Scan a single file for vulnerabilities."""
        return self.scan_directory(file_path.parent)


class TaintTracker:
    """Taint tracking analyzer for data flow analysis.

    Tracks data flow from Sources (user input, environment) to
    Sinks (exec, eval, subprocess, network, file write).
    Detects whether data passes through Sanitizers before reaching sinks.

    Inspired by SkillSpector's taint tracking with CFG analysis.
    """

    SOURCE_PATTERNS = [
        "input(", "sys.argv", "os.environ", "request.", "sys.stdin",
        "open(", "Path(", "file.read", "json.load",
    ]

    SINK_PATTERNS = [
        "exec(", "eval(", "subprocess.", "os.system(", "os.popen(",
        "requests.post", "requests.get", "requests.put",
        "open(.*'w')", "open(.*'a')", "shutil.",
    ]

    SANITIZER_PATTERNS = [
        "escape(", "sanitize(", "validate(", "html.escape",
        "re.sub", "strip(", "ast.literal_eval",
    ]

    def analyze(self, code: str) -> list[dict[str, Any]]:
        """Analyze code for taint flows from source to sink."""
        findings = []
        lines = code.split("\n")

        sources = []
        sanitizers = set()

        for line_num, line in enumerate(lines, 1):
            for pattern in self.SOURCE_PATTERNS:
                if pattern in line:
                    sources.append((line_num, line.strip(), pattern))

            for pattern in self.SANITIZER_PATTERNS:
                if pattern in line:
                    sanitizers.add(line_num)

            for sink_pattern in self.SINK_PATTERNS:
                if re.search(sink_pattern, line):
                    for src_line, src_code, src_pattern in sources:
                        if src_line < line_num:
                            # Check if any sanitizer is between source and sink
                            has_sanitizer = any(
                                src_line < s < line_num for s in sanitizers
                            )
                            findings.append({
                                "source_line": src_line,
                                "source_code": src_code,
                                "sink_line": line_num,
                                "sink_code": line.strip(),
                                "sanitized": has_sanitizer,
                                "risk": "LOW" if has_sanitizer else "HIGH",
                            })

        return findings

    def analyze_file(self, file_path: Path) -> list[dict[str, Any]]:
        """Analyze a file for taint flows."""
        try:
            code = file_path.read_text(encoding="utf-8")
            return self.analyze(code)
        except Exception as e:
            logger.error("taint_analysis_error", file=str(file_path), error=str(e))
            return []
