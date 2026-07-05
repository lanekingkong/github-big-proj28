# UniSkill - Universal Agent Capability Mesh

<div align="center">

![UniSkill](https://img.shields.io/badge/UniSkill-v1.0.0-blue)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Stars](https://img.shields.io/github/stars/lanekingkong/uniskill?style=social)](https://github.com/lanekingkong/uniskill)

**The Universal AI Agent Capability Mesh — Build, Test, Secure, Deploy, and Monitor AI Agent Skills at Enterprise Scale**

[English](README.md) | [中文](README_ZH.md)

</div>

---

## Why UniSkill?

**89% of enterprise AI agent projects never reach production.** Only 2% achieve full-scale operation (Hendricks.ai, 2026). The root causes are not model quality problems — they are infrastructure, safety, observability, and orchestration gaps.

UniSkill is the **first unified platform** that addresses all five root causes simultaneously:

| Pain Point | Industry Rate | UniSkill Solution |
|:---|:---:|:---|
| Integration Complexity | 46% cite as #1 blocker | **Unified MCP/A2A Bridge** — one adapter, all systems |
| Context Window Limits | 60-95% token waste | **Adaptive Context Engine** — smart compression inspired by headroom |
| Agent Safety Vulnerabilities | 64 known attack patterns | **Built-in SkillSpector-class Scanner** — 16 categories, 64 patterns |
| Production Monitoring Void | Detected after 4-6 weeks | **Enterprise Observability** — distributed tracing, golden datasets |
| Multi-Agent Chaos | Exponential coordination overhead | **Skill Lifecycle State Machine** — Plan→Spec→Code→Test→Review→Ship |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        UniSkill Platform                         │
├───────────┬───────────┬───────────┬───────────┬─────────────────┤
│ Marketplace│  Testing  │ Security  │Governance │  Observability  │
│ Registry  │ Framework │  Scanner  │  Center   │    Pipeline      │
│ Discovery │  Golden   │ 64 Rules  │  Audit    │  Distributed     │
│ Versioning│ Datasets  │ Taint Trk │  RBAC     │  Tracing         │
├───────────┴───────────┴───────────┴───────────┴─────────────────┤
│                    Context Engine (Compression)                  │
│  SmartCrusher │ CodeCompressor │ SemanticCompactor │ CCR Reversible│
├─────────────────────────────────────────────────────────────────┤
│              Bridge Layer (MCP Server + A2A Router)              │
│  Claude Code │ Codex CLI │ Cursor │ Gemini │ Goose │ Custom Agent │
├─────────────────────────────────────────────────────────────────┤
│                      Deployment Engine                          │
│  Self-Host │ Cloud │ Hybrid │ Docker │ K8s │ Edge Local          │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install
pip install uniskill

# Initialize a new skill project
uniskill init my-awesome-skill

# Scan an existing skill for vulnerabilities
uniskill security scan ./my-skill/

# Test a skill against golden datasets
uniskill test run ./my-skill/ --dataset ./golden/

# Deploy to MCP server
uniskill deploy start --mcp-port 8787

# Monitor skill performance
uniskill observe dashboard
```

## Core Modules

### 1. Skill Marketplace (`uniskill.marketplace`)
- **Registry**: Decentralized skill index with semantic versioning
- **Discovery**: Vector-based skill search with compatibility matrix
- **Publishing**: One-command publish with auto-validation

### 2. Context Engine (`uniskill.context_engine`)
- **SmartCrusher**: JSON/tabular data compression (85-95% reduction)
- **CodeCompressor**: AST-aware code compression preserving semantics
- **SemanticCompactor**: Embedding-based text summarization
- **CCR (Context-Conscious Retrieval)**: Reversible compression with on-demand expansion

### 3. Security Scanner (`uniskill.security`)
- **Stage 1**: Fast static analysis (regex + AST pattern matching)
- **Stage 2**: Deep semantic analysis with LLM evaluation
- **Taint Tracking**: Data flow analysis from source to sink
- **Risk Scoring**: 0-100 with severity levels and fix recommendations

### 4. Testing Framework (`uniskill.testing`)
- **Golden Dataset Management**: Version-controlled test cases
- **Regression Testing**: Automated pre/post deployment testing
- **Performance Benchmarking**: Token usage, latency, accuracy metrics
- **Fuzzing**: Input edge case generation for robustness testing

### 5. Protocol Bridge (`uniskill.bridge`)
- **MCP Server**: Full Model Context Protocol implementation
- **A2A Router**: Agent-to-Agent capability discovery and delegation
- **AG-UI**: Generative UI protocol for frontend integration
- **Multi-Agent**: Support for Claude Code, Codex, Cursor, Goose, and custom agents

### 6. Enterprise Governance (`uniskill.governance`)
- **RBAC/ABAC**: Fine-grained access control for skills
- **Audit Trail**: Immutable execution logs for compliance (SOC2, SEC)
- **PII Redaction**: Automatic sensitive data masking
- **Human-in-the-Loop**: Approval workflows for high-risk operations

### 7. Observability (`uniskill.observability`)
- **Distributed Tracing**: Step-level execution tracking
- **Metrics Dashboard**: Real-time skill performance monitoring
- **Alerting**: Drift detection and anomaly alerts
- **Eval Pipeline**: Automated quality regression detection

## Comparison with Existing Solutions

| Feature | headroom | SkillSpector | agent-skills | CopilotKit | **UniSkill** |
|:---|:---:|:---:|:---:|:---:|:---:|
| Context Compression | ✅ | ❌ | ❌ | ❌ | ✅ **Enhanced** |
| Security Scanning | ❌ | ✅ | ❌ | ❌ | ✅ **Enhanced** |
| Lifecycle Management | ❌ | ❌ | ✅ | ❌ | ✅ **Enhanced** |
| Generative UI | ❌ | ❌ | ❌ | ✅ | ✅ |
| MCP/A2A Native | ✅* | ❌ | ❌ | ❌ | ✅ **Full** |
| Skill Marketplace | ❌ | ❌ | ❌ | ❌ | ✅ |
| Enterprise Governance | ❌ | ❌ | ❌ | ❌ | ✅ |
| Golden Dataset Testing | ❌ | ❌ | ❌ | ❌ | ✅ |
| Multi-Agent Bridge | ❌ | ❌ | ❌ | ❌ | ✅ |
| Unified Platform | ❌ | ❌ | ❌ | ❌ | ✅ |

## Project Structure

```
uniskill/
├── src/uniskill/
│   ├── marketplace/     # Skill registry, discovery, versioning
│   ├── context_engine/  # Smart compression and context management
│   ├── security/        # Two-stage security scanner
│   ├── compression/     # Compression algorithm implementations
│   ├── testing/         # Test framework with golden datasets
│   ├── bridge/          # MCP + A2A protocol implementations
│   ├── deployment/      # Self-host, cloud, hybrid deployment
│   ├── governance/      # RBAC, audit, PII, HITL
│   ├── observability/   # Tracing, metrics, alerting
│   ├── protocols/       # AG-UI, MCP spec, A2A spec
│   └── cli.py           # Unified CLI interface
├── tests/               # Comprehensive test suite
├── docs/                # Documentation (EN + ZH)
│   ├── en/              # English documentation
│   └── zh/              # Chinese documentation
├── examples/            # Example skills and configurations
├── skills/              # Built-in reference skills
└── .github/workflows/   # CI/CD pipelines
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 — See [LICENSE](LICENSE) for details.

---

**Built with ❤️ by the UniSkill team. Star us on GitHub!**
