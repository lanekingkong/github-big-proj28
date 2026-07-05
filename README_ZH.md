# UniSkill - 通用AI Agent能力网格

<div align="center">

![UniSkill](https://img.shields.io/badge/UniSkill-v1.0.0-blue)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Stars](https://img.shields.io/github/stars/lanekingkong/uniskill?style=social)](https://github.com/lanekingkong/uniskill)

**通用AI Agent能力网格 — 在企业级规模上构建、测试、安全防护、部署和监控AI Agent技能**

[English](README.md) | [中文](README_ZH.md)

</div>

---

## 为什么需要UniSkill？

**89%的企业AI Agent项目从未进入生产环境**，仅有2%实现全规模运营（Hendricks.ai, 2026）。根本原因不是模型质量——而是基础设施、安全、可观测性和编排的差距。

UniSkill是**首个统一平台**，同时解决五大根本原因：

| 痛点 | 行业数据 | UniSkill解决方案 |
|:---|:---:|:---|
| 系统集成复杂性 | 46%视为首要障碍 | **统一MCP/A2A桥接** — 一套适配器，连接所有系统 |
| 上下文窗口限制 | 60-95%Token浪费 | **自适应上下文引擎** — 借鉴headroom的智能压缩 |
| Agent安全漏洞 | 64种已知攻击模式 | **内置SkillSpector级扫描器** — 16类别、64种模式 |
| 生产环境监控缺失 | 错误发现延迟4-6周 | **企业级可观测性** — 分布式追踪、黄金数据集 |
| 多Agent混乱 | 协调开销指数级增长 | **技能生命周期状态机** — 规划→规格→编码→测试→审查→发布 |

## 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        UniSkill 平台                             │
├───────────┬───────────┬───────────┬───────────┬─────────────────┤
│  技能市场  │  测试框架  │  安全扫描  │  治理中心  │  可观测性管道    │
│  注册中心  │  黄金数据  │  64规则   │  审计追踪  │  分布式追踪      │
│  发现引擎  │  回归测试  │  污点追踪  │  权限控制  │  实时告警        │
├───────────┴───────────┴───────────┴───────────┴─────────────────┤
│               上下文引擎 (智能压缩层)                            │
│  SmartCrusher │ CodeCompressor │ SemanticCompactor │ CCR可逆压缩  │
├─────────────────────────────────────────────────────────────────┤
│           桥接层 (MCP Server + A2A Router)                      │
│  Claude Code │ Codex CLI │ Cursor │ Gemini │ Goose │ 自定义Agent  │
├─────────────────────────────────────────────────────────────────┤
│                      部署引擎                                   │
│  自托管 │ 云端 │ 混合 │ Docker │ K8s │ 边缘本地                  │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

```bash
# 安装
pip install uniskill

# 初始化新技能项目
uniskill init my-awesome-skill

# 扫描现有技能的安全漏洞
uniskill security scan ./my-skill/

# 基于黄金数据集测试技能
uniskill test run ./my-skill/ --dataset ./golden/

# 部署到MCP服务器
uniskill deploy start --mcp-port 8787

# 监控技能性能
uniskill observe dashboard
```

## 核心模块

### 1. 技能市场 (`uniskill.marketplace`)
- **注册中心**：去中心化技能索引，支持语义化版本管理
- **发现引擎**：基于向量的技能搜索与兼容性矩阵
- **发布系统**：一键发布，自动验证

### 2. 上下文引擎 (`uniskill.context_engine`)
- **SmartCrusher**：JSON/表格数据压缩（85-95%压缩率）
- **CodeCompressor**：AST感知代码压缩，保留语义
- **SemanticCompactor**：基于Embedding的文本摘要
- **CCR（上下文感知检索）**：可逆压缩，按需解压

### 3. 安全扫描器 (`uniskill.security`)
- **第一阶段**：快速静态分析（正则+AST模式匹配）
- **第二阶段**：深度语义分析+LLM评估
- **污点追踪**：从Source到Sink的数据流分析
- **风险评分**：0-100分，含严重等级与修复建议

## 与现有方案对比

| 功能 | headroom | SkillSpector | agent-skills | CopilotKit | **UniSkill** |
|:---|:---:|:---:|:---:|:---:|:---:|
| 上下文压缩 | ✅ | ❌ | ❌ | ❌ | ✅ **增强版** |
| 安全扫描 | ❌ | ✅ | ❌ | ❌ | ✅ **增强版** |
| 生命周期管理 | ❌ | ❌ | ✅ | ❌ | ✅ **增强版** |
| 生成式UI | ❌ | ❌ | ❌ | ✅ | ✅ |
| MCP/A2A原生 | ✅* | ❌ | ❌ | ❌ | ✅ **完整版** |
| 技能市场 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 企业治理 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 黄金数据集测试 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 多Agent桥接 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 统一平台 | ❌ | ❌ | ❌ | ❌ | ✅ |

## 许可证

Apache 2.0 — 详见 [LICENSE](LICENSE)
