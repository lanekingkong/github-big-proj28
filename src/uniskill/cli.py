"""
UniSkill CLI - Command-line interface for the UniSkill platform.

Provides commands for:
- Skill creation, testing, and deployment
- Marketplace search and download
- Security scanning
- Context compression
- Deployment management
- Governance administration
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import rich
from rich.console import Console
from rich.table import Table

from uniskill import __version__
from uniskill.core import EngineConfig, SkillLifecycleState, SkillMetadata, UniSkillEngine
from uniskill.marketplace import SkillRegistry
from uniskill.security import SecurityScanner
from uniskill.context_engine import ContextManager

console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="uniskill",
        description="UniSkill - Universal Agent Capability Mesh",
        epilog="For more information: https://github.com/lanekingkong/uniskill",
    )
    parser.add_argument("--version", action="version", version=f"UniSkill v{__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- init ---
    init_parser = subparsers.add_parser("init", help="Initialize a new skill project")
    init_parser.add_argument("name", help="Skill name")
    init_parser.add_argument("--description", default="", help="Skill description")
    init_parser.add_argument("--author", default="", help="Author name")
    init_parser.add_argument("--dir", default=".", help="Output directory")
    init_parser.add_argument("--template", choices=["basic", "agent", "tool", "pipeline"], default="basic")

    # --- scan ---
    scan_parser = subparsers.add_parser("scan", help="Security scan a skill directory")
    scan_parser.add_argument("path", help="Path to skill directory")
    scan_parser.add_argument("--json", action="store_true", help="Output as JSON")
    scan_parser.add_argument("--stage2", action="store_true", help="Enable Stage 2 LLM analysis")

    # --- test ---
    test_parser = subparsers.add_parser("test", help="Run skill tests")
    test_parser.add_argument("skill_dir", help="Path to skill directory")
    test_parser.add_argument("--suite", help="Specific test suite to run")
    test_parser.add_argument("--fuzz", action="store_true", help="Run fuzzing tests")

    # --- build ---
    build_parser = subparsers.add_parser("build", help="Build a skill package")
    build_parser.add_argument("skill_dir", help="Path to skill directory")
    build_parser.add_argument("--output", "-o", default=".", help="Output directory")

    # --- publish ---
    publish_parser = subparsers.add_parser("publish", help="Publish skill to marketplace")
    publish_parser.add_argument("skill_dir", help="Path to skill directory")
    publish_parser.add_argument("--registry", help="Registry URL")

    # --- install ---
    install_parser = subparsers.add_parser("install", help="Install a skill from marketplace")
    install_parser.add_argument("name", help="Skill name")
    install_parser.add_argument("--version", default="latest", help="Skill version")

    # --- search ---
    search_parser = subparsers.add_parser("search", help="Search marketplace for skills")
    search_parser.add_argument("query", nargs="?", default="", help="Search query")
    search_parser.add_argument("--tags", nargs="+", help="Filter by tags")

    # --- list ---
    list_parser = subparsers.add_parser("list", help="List installed skills")

    # --- compress ---
    compress_parser = subparsers.add_parser("compress", help="Compress context for token savings")
    compress_parser.add_argument("--text", help="Text to compress")
    compress_parser.add_argument("--file", help="File to compress")
    compress_parser.add_argument("--stats", action="store_true", help="Show compression statistics")

    # --- deploy ---
    deploy_parser = subparsers.add_parser("deploy", help="Deploy UniSkill")
    deploy_parser.add_argument("--mode", choices=["self-hosted", "docker", "kubernetes"], default="self-hosted")
    deploy_parser.add_argument("--port", type=int, default=8787)

    # --- info ---
    info_parser = subparsers.add_parser("info", help="Show UniSkill system information")

    # --- config ---
    config_parser = subparsers.add_parser("config", help="Manage UniSkill configuration")
    config_parser.add_argument("action", choices=["show", "set"], default="show")
    config_parser.add_argument("key", nargs="?", help="Config key")
    config_parser.add_argument("value", nargs="?", help="Config value")

    return parser


def cmd_init(args) -> None:
    """Initialize a new skill project."""
    skill_dir = Path(args.dir) / args.name
    if skill_dir.exists():
        console.print(f"[red]Directory '{skill_dir}' already exists.[/red]")
        return

    skill_dir.mkdir(parents=True)

    # Create skill.yaml
    skill_yaml = f"""name: {args.name}
version: 0.1.0
description: {args.description or 'A new UniSkill skill'}
author: {args.author or 'unknown'}
license: Apache-2.0

entry_point: skill.py

dependencies: {{}}
tags: []
compatible_agents: []

lifecycle:
  state: init

quality_gates:
  lint: true
  test: true
  security_scan: true
  coverage_threshold: 80
"""

    (skill_dir / "skill.yaml").write_text(skill_yaml)

    # Create skill.py template
    templates = {
        "basic": '''"""Basic skill template."""\n\ndef execute(input_data: dict) -> dict:\n    """Execute the skill."""\n    return {"result": "Hello from {name}!"}\n',
        "agent": '''"""Agent skill template."""\n\nfrom typing import Any\n\nclass {name_title}Agent:\n    """An AI agent skill."""\n\n    def __init__(self):\n        self.name = "{name}"\n\n    def run(self, task: str, **kwargs) -> dict[str, Any]:\n        """Run the agent."""\n        return {{"status": "completed", "task": task}}\n''',
        "tool": '''"""Tool skill template."""\n\ndef tool_function(input_text: str) -> dict:\n    """Process input and return result."""\n    return {{"output": f"Processed: {{input_text}}"}}\n''',
        "pipeline": '''"""Pipeline skill template."""\n\nfrom typing import Any\n\nclass Pipeline:\n    """A multi-stage processing pipeline."""\n\n    def __init__(self):\n        self.stages = []\n\n    def add_stage(self, func) -> None:\n        self.stages.append(func)\n\n    def run(self, data: Any) -> Any:\n        result = data\n        for stage in self.stages:\n            result = stage(result)\n        return result\n''',
    }

    name_title = args.name.replace("-", " ").title().replace(" ", "")
    template = templates.get(args.template, templates["basic"])
    (skill_dir / "skill.py").write_text(template.format(name=args.name, name_title=name_title))

    # Create SKILL.md
    skill_md = f"""# {args.name}

{args.description or 'A new UniSkill skill'}

## Usage

```python
from {args.name} import execute

result = execute({{}})
```

## Author

{args.author or 'unknown'}
"""
    (skill_dir / "SKILL.md").write_text(skill_md)

    console.print(f"[green]Skill '{args.name}' initialized at {skill_dir}[/green]")
    console.print(f"  - skill.yaml (manifest)")
    console.print(f"  - skill.py (code)")
    console.print(f"  - SKILL.md (documentation)")


def cmd_scan(args) -> None:
    """Security scan a skill directory."""
    scanner = SecurityScanner()
    result = scanner.scan_directory(Path(args.path))

    if args.json:
        console.print(json.dumps({
            "skill": result.skill_name,
            "risk_score": result.risk_score,
            "risk_level": result.risk_level,
            "vulnerabilities": [
                {"rule": v.rule_id, "severity": v.severity.value, "file": v.file_path, "line": v.line_number}
                for v in result.vulnerabilities
            ],
        }, indent=2))
        return

    # Rich table output
    severity_colors = {"critical": "red", "high": "orange1", "medium": "yellow", "low": "green"}

    console.print(f"\n[bold]Security Scan: {result.skill_name}[/bold]")
    console.print(f"Files scanned: {result.total_files}")
    console.print(f"Risk Score: [{severity_colors.get(result.risk_level.split()[0].lower(), 'white')}]{result.risk_score}/100 - {result.risk_level}[/{severity_colors.get(result.risk_level.split()[0].lower(), 'white')}]")

    if result.vulnerabilities:
        table = Table(title="Vulnerabilities")
        table.add_column("Rule", style="bold")
        table.add_column("Severity")
        table.add_column("File")
        table.add_column("Description")

        for v in result.vulnerabilities:
            table.add_row(
                v.rule_id,
                f"[{severity_colors.get(v.severity.value, 'white')}]{v.severity.value}[/{severity_colors.get(v.severity.value, 'white')}]",
                f"{v.file_path}:{v.line_number}",
                v.description[:80],
            )
        console.print(table)
    else:
        console.print("[green]No vulnerabilities found.[/green]")


def cmd_test(args) -> None:
    """Run skill tests."""
    console.print(f"[yellow]Test runner for {args.skill_dir}[/yellow]")
    console.print("Tests would run here. Currently requires a golden dataset.")


def cmd_compress(args) -> None:
    """Compress context."""
    manager = ContextManager()
    text = args.text
    if args.file:
        text = Path(args.file).read_text()

    if not text:
        console.print("[red]No text provided. Use --text or --file.[/red]")
        return

    result = manager._router.route(text)

    if args.stats:
        console.print(f"Algorithm: {result.algorithm}")
        console.print(f"Original tokens: ~{result.original_tokens}")
        console.print(f"Compressed tokens: ~{result.compressed_tokens}")
        console.print(f"Compression ratio: {result.compression_ratio:.2%}")
        console.print(f"Token savings: {result.savings_percent:.1f}%")
    else:
        console.print(f"Compressed ({result.savings_percent:.1f}% savings)")


def cmd_info(args) -> None:
    """Show UniSkill system information."""
    engine = UniSkillEngine()
    health = engine.health_check()

    console.print(f"\n[bold green]UniSkill v{__version__}[/bold green]")
    console.print(f"Status: {health['status']}")
    console.print(f"Registered skills: {health['registered_skills']}")

    console.print("\n[bold]Subsystems:[/bold]")
    for name, status in health["subsystems"].items():
        color = "green" if status == "ok" else "red"
        console.print(f"  {name}: [{color}]{status}[/{color}]")


def cmd_deploy(args) -> None:
    """Deploy UniSkill."""
    console.print(f"[green]Deploying UniSkill in {args.mode} mode on port {args.port}...[/green]")


def cmd_search(args) -> None:
    """Search marketplace."""
    registry = SkillRegistry()
    results = registry.search(args.query) if args.query else registry.list_all()

    if not results:
        console.print("[yellow]No skills found.[/yellow]")
        return

    table = Table(title="Skill Marketplace")
    table.add_column("Name", style="bold")
    table.add_column("Version")
    table.add_column("Description")
    table.add_column("Downloads")

    for pkg in results[:20]:
        table.add_row(pkg.name, str(pkg.version), pkg.description[:60], str(pkg.download_count))

    console.print(table)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    command_map = {
        "init": cmd_init,
        "scan": cmd_scan,
        "test": cmd_test,
        "compress": cmd_compress,
        "info": cmd_info,
        "deploy": cmd_deploy,
        "search": cmd_search,
    }

    handler = command_map.get(args.command)
    if handler:
        try:
            handler(args)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    else:
        console.print(f"[yellow]Command '{args.command}' not fully implemented yet.[/yellow]")


if __name__ == "__main__":
    main()
