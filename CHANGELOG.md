# Changelog

本项目的所有显著变更记录于此。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。

## [1.1.0] - 2026-10-02

### Added
- **复杂度分档**（Phase 0）：轻量/标准/深度三档，依据 Anthropic 多 Agent 缩放规则（多 agent +90.2% 效果 / 15× token）与 Gemini 双档制，简单话题不再跑全编队
- **反方评审闸门**（Phase 3.5，🛑 硬停）：起草后、定稿前强制对抗审查——证据绑定检查、官方口径标注（"未见第三方复现"）、单源结论标记 `single-source`、修订上限 ≤2 轮、去 AI 腔清单
- **大纲级预检**（Phase 1）：items 互斥自检 + 强制 1-2 个反方 item，缺反方视角的大纲不予确认
- **子代理回传纪律**（Phase 3）：只回传结构化 findings，不回传网页原文——防上下文污染（Anthropic 一手经验）
- **断点续跑**（Phase 3）：逐 item 落盘 results/，中断重跑只补缺失项
- 报告结构新增第 5 章「未覆盖与限制」：评审 2 轮后仍未查到的如实列出
- 用户手册与技术手册（docs/），含 8 方案对标调研的设计依据

### Rationale
- v1.1.0 三项核心机制来自对 GPT Researcher / Anthropic 多 Agent 系统 / OpenAI & Google Deep Research / daymade / Weizhena / Stanford STORM / brycewang-stanford / RhinoInsight 的对标调研（全部一手来源带日期）

## [1.0.0] - 2026-10-02

### Added
- 编排层技能首发：融合 4 个调研子技能（deep-research 主干 / research 一手来源纪律 / agent-reach 14 平台源路由 / market-researcher 商业标注规范）
- 六阶段流水线：意图分流 → 大纲字段 → 确认闸门（🛑）→ 并行深调（双纪律）→ 汇总报告 → 交付升级
- 全链路降级矩阵：任一子技能缺失均可执行，报告注明实际工具组合
- 反虚构规则固化：查不到标 `partial`/`uncertain`，绝不编造数字
- 商业类话题强制标注规范：来源+日期、定量暴露公式与假设、结论带置信度
