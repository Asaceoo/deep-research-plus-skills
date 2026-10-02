# Deep Research Plus — 深度调研融合流水线

> 跨平台 Agent Skill（Claude Code · OpenAI Codex · OpenCode · WorkBuddy 通用）。
> 一个**编排层**技能：把 4 个调研能力串成一条流水线，产出**每条结论带一手引用**的结构化调研报告。

**当前版本：v1.2.0**（含 4 个捆绑子技能，克隆即完整可用） ｜ [变更日志](./CHANGELOG.md) ｜ [用户手册](./docs/user-guide.md) ｜ [技术手册](./docs/technical-manual.md) ｜ [第三方声明](./THIRD-PARTY-NOTICES.md) ｜ License: MIT

---

## 它解决什么问题

单次搜索的调研浅、漏来源、结论无引用；通用 deep-research 流程不分话题类型、不分复杂度，简单话题跑全编队浪费 token，复杂调研缺质量闸门产出易掺水。

deep-research-plus 的答案：

- **按话题路由源**：技术选型追官方文档/源码一手来源；舆情口碑走 Reddit/GitHub issues/B站/小红书等社区信号；商业分析强制"来源+日期+假设暴露，查不到标 partial 不编造"。
- **按复杂度分档**：轻量（主代理直搜）/ 标准（2-3 路并行子代理）/ 深度（全编队+评审全开）——依据 Anthropic 多 Agent 研究系统的缩放规则（多 agent +90.2% 效果，但 15× token，简单话题不值）。
- **反方评审闸门**：起草后、定稿前强制对抗审查——证据绑定检查、官方自述数字标注、单源结论标记、修订上限 ≤2 轮、去 AI 腔清单。

## 设计原则：指针不重复

本技能是编排层，不复制子技能内容，只定义"怎么串"：

| 子技能 | 角色 | 缺失时 |
|--------|------|--------|
| [Weizhena/Deep-Research-skills](https://github.com/Weizhena/Deep-Research-skills) | 主干：大纲→确认→并行深调→报告 四阶段 | 内置简化流程替代 |
| [research](https://github.com/anthropics/skills)（一手来源纪律） | 每条结论追官方文档/源码/spec | 纪律保留，WebSearch+WebFetch 执行 |
| [agent-reach](https://github.com/) | 14 平台社媒源路由（Twitter/Reddit/YouTube/B站/知乎等） | 跳过社媒源，仅 WebSearch |
| market-researcher | 商业标注规范（来源+日期+置信度） | 跳过，通用引用规范 |

**全链路可降级**：四个子技能缺任何一个都能跑，只是能力缩水，并在报告开头注明实际使用的工具组合。

> 📦 四个子技能已随本仓库捆绑在 `sub-skills/` 目录（版权归原作者，见 [THIRD-PARTY-NOTICES.md](./THIRD-PARTY-NOTICES.md)），完整安装后零降级。

## 安装

### 完整安装（推荐，克隆即完整可用）

```bash
git clone https://github.com/Asaceoo/deep-research-plus-skills.git
cd deep-research-plus-skills

# WorkBuddy
mkdir -p ~/.workbuddy/skills
cp SKILL.md ~/.workbuddy/skills/deep-research-plus/SKILL.md 2>/dev/null || { mkdir -p ~/.workbuddy/skills/deep-research-plus && cp SKILL.md ~/.workbuddy/skills/deep-research-plus/; }
cp -r sub-skills/deep-research      ~/.workbuddy/skills/
cp -r sub-skills/research           ~/.workbuddy/skills/
cp -r sub-skills/agent-reach        ~/.workbuddy/skills/
cp -r sub-skills/market-researcher  ~/.workbuddy/skills/
```

把上面的 `~/.workbuddy` 换成对应平台目录即可适配其他平台：

| 平台 | 技能根目录 |
|------|-----------|
| WorkBuddy | `~/.workbuddy/skills/` |
| Claude Code | `~/.claude/skills/` |
| Codex / OpenCode | `~/.codex/skills/`（OpenCode 自动扫描 Claude/Codex 目录） |

**Python 依赖**（仅 deep-research 的校验脚本需要）：`pip install pyyaml`。

### 最小安装（仅编排层，子技能自动降级）

```bash
git clone https://github.com/Asaceoo/deep-research-plus-skills.git
mkdir -p ~/.workbuddy/skills/deep-research-plus
cp deep-research-plus-skills/SKILL.md ~/.workbuddy/skills/deep-research-plus/SKILL.md
```

**依赖**：宿主 Agent 需支持 Read / Write / Glob / WebSearch / WebFetch / Task（子代理）/ AskUserQuestion。未安装子技能时按降级矩阵自动降级（见技术手册 §4），能力缩水但流程完整。

## 使用

```
「用 deep-research-plus 调研 <话题>」
→ Phase 0  定性话题类型 + 复杂度分档（轻量/标准/深度）
→ Phase 1  产出调研大纲（items + fields），你确认前可增删
→ Phase 2  🛑 确认闸门：大纲获你明确确认后才开搜
→ Phase 3  并行深调（一手来源优先 + 源路由双纪律，逐项落盘支持断点续跑）
→ Phase 3.5 🛑 反方评审：证据绑定 / 官方口径标注 / 单源标记 / 去AI腔
→ Phase 4  汇总报告 report.md（TL;DR带引用 → 对比总表 → 逐项详析 → 冲突存疑 → 未覆盖 → 来源清单）
→ Phase 5  可选升级：杂志风 HTML 信息图 / NotebookLM 播客思维导图
```

## 文档

| 文档 | 内容 |
|------|------|
| [用户手册](./docs/user-guide.md) | 安装、触发、分档选择、四阶段体验、报告解读、FAQ（v1.2.0） |
| [技术手册](./docs/technical-manual.md) | 架构、设计依据（8 方案对标调研）、闸门机制、降级矩阵、扩展指南（v1.2.0） |
| [第三方声明](./THIRD-PARTY-NOTICES.md) | 捆绑子技能的来源与版权归属 |
| [变更日志](./CHANGELOG.md) | 版本历史 |

## 文件结构

```
deep-research-plus-skills/
├── SKILL.md                        # 技能主文件 v1.2.0（编排流程、分档、闸门、降级矩阵）
├── sub-skills/                     # 捆绑的 4 个子技能（克隆即完整可用）
│   ├── deep-research/              # 结构化主干：四阶段流程 + 5 个子命令 + 搜索 agent（22 文件）
│   ├── research/                   # 一手来源调研纪律（单文件）
│   ├── agent-reach/                # 14 平台社媒源路由
│   └── market-researcher/          # 商业标注规范
├── docs/
│   ├── user-guide.md               # 用户手册（v1.2.0）
│   └── technical-manual.md         # 技术手册（v1.2.0）
├── THIRD-PARTY-NOTICES.md          # 第三方子技能版权声明
├── CHANGELOG.md                    # 版本历史
├── LICENSE                         # MIT（覆盖编排层，不含 sub-skills/）
└── .gitignore
```

## 版本号规范

版本号单一来源：`SKILL.md` frontmatter 的 `version` 字段。每次发布自动递增并同步更新 CHANGELOG、两份手册头部标注与 git tag（`vX.Y.Z`）。

## License

MIT — 见 [LICENSE](./LICENSE)
