# Changelog

本项目的所有显著变更记录于此。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。

## [1.3.1] - 2026-10-03

### Added — 质量审查增补（鲁班十维审查 88.4 → 93.9）
- **新增「反例黑名单」章节**：R1-R6 六条反模式 + 替代做法（大纲无反方视角 / AI 腔行文 / 编造数字 / 裸域名引用 / 无证据"综合判断" / 单源决策级结论），全程对照，违反即返工
- **新增「使用示例」章节**：标准档选型调研的完整执行路径示例 + 轻量档对照，降低首次执行的理解成本

### Changed
- 能力需求表分层标签「建议」→「可选」（消除歧义：是能力档位而非软化指令）
- 引用纪律注入「建议加 `source_type`」→「应加 `source_type`」

## [1.3.0] - 2026-10-02

### Changed — 跨平台通用化（平台无关化改造）
- **新增「平台适配层」**：所有平台专属机制改为能力需求 + 降级——网络搜索（必需）/ 网页抓取 / 对话确认 / 子代理并行 / 文件读写（后四项均可降级）
- frontmatter 移除平台特定 `allowed-tools`；无子代理平台（Cursor/WPS AI 等）主代理逐项串行深调等价实现；无文件能力平台报告分段输出在对话中
- 子技能检测扩展为多目录（`~/.workbuddy` / `~/.claude` / `~/.codex` / `~/.config/opencode` / 项目 `.skills/`），无法读文件系统时全降级
- 斜杠命令引用改为自然语言交互描述；报告头部新增「能力组合」声明
- **反方评审升级**（吸收 2026 引用审计研究）：新增「承重引用内容对照」（77% 引用错误为"链接真但内容不支撑"的误引用）与 `high-risk` 标记（决策级结论仅社区来源支撑）

### 适用平台
Claude Code / OpenAI Codex / OpenCode / OpenClaw / WorkBuddy / Cursor / WPS AI / 任何能读 Markdown + 联网搜索的智能体

## [1.2.1] - 2026-10-02

### Fixed
- 报告来源清单引用格式强化：必须写完整 `https://` 可点击链接，裸域名不算引用（真实性抽检发现首跑报告的引用均为裸域名，可追溯性打折）

### Verified
- 引用真实性抽检（3 条承重引用）：Anthropic 工程博客（90.2% / 15× token 数字逐字命中，日期精确）、RhinoInsight arXiv:2511.18743（标题/日期/机制描述全部吻合）、Gemini API 文档（fetch 不可达，未证伪）——可验证引用 2/2 属实

## [1.2.0] - 2026-10-02

### Added
- **捆绑子技能分发**：新增 `sub-skills/` 目录，原样收录全部 4 个依赖子技能——克隆仓库即可零降级完整执行（编排层 + 主干 + 引用纪律 + 源路由 + 商业标注）
  - deep-research 1.0.0（结构化主干，22 文件中英双版）
  - research（一手来源调研纪律，单文件）
  - agent-reach 1.1.0（14 平台社媒源路由）
  - market-researcher 1.0.1（商业标注规范）
- `THIRD-PARTY-NOTICES.md`：第三方子技能版权声明（版权归原作者，根 MIT License 不覆盖 sub-skills/）
- README 安装章节重写：完整安装（一键四技能 + pyyaml 依赖说明）与最小安装（自动降级）双路径

### Changed
- 编排层 SKILL.md version 1.1.0 → 1.2.0；两份手册头部版本同步；文档结构树补 sub-skills/

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
