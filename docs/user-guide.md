# Deep Research Plus 用户手册

> **版本：v1.2.1**（引用格式强化）｜ 更新日期：2026-10-02 ｜ 适用平台：WorkBuddy / Claude Code / OpenAI Codex / OpenCode

---

## 1. 这是什么

deep-research-plus 是一个**深度调研编排技能**：你说一个话题，它按话题类型自动选择信息源、按复杂度自动分配资源，跑完「大纲确认 → 并行深调 → 反方评审 → 汇总报告」流水线，交付一份**每条结论带一手引用**的 Markdown 调研报告。

与普通搜索的区别：

| | 普通搜索 | deep-research-plus |
|---|---|---|
| 深度 | 单轮结果 | 多 items 并行深调 + 反方评审 |
| 来源 | 不分优劣 | 一手来源优先（官方文档/源码 > 二手文章） |
| 引用 | 无 | 每条结论带 URL + 类型 + 日期 |
| 编造风险 | 高 | 查不到标 `partial`/`uncertain`，绝不编数字 |
| 成本 | 低 | 分档控制：简单话题不跑全编队 |

## 2. 安装

### 完整安装（推荐）

仓库已捆绑全部 4 个子技能（`sub-skills/`），照抄以下命令即可零降级运行：

```bash
git clone https://github.com/Asaceoo/deep-research-plus-skills.git
cd deep-research-plus-skills

# 1) 编排层（把 ~/.workbuddy 换成你平台的技能目录，见下表）
mkdir -p ~/.workbuddy/skills/deep-research-plus
cp SKILL.md ~/.workbuddy/skills/deep-research-plus/

# 2) 四个子技能
cp -r sub-skills/deep-research      ~/.workbuddy/skills/
cp -r sub-skills/research           ~/.workbuddy/skills/
cp -r sub-skills/agent-reach        ~/.workbuddy/skills/
cp -r sub-skills/market-researcher  ~/.workbuddy/skills/

# 3) Python 依赖（仅 deep-research 的校验脚本需要）
pip install pyyaml
```

平台技能目录对照：

| 平台 | 技能根目录 |
|------|-----------|
| WorkBuddy | `~/.workbuddy/skills/` |
| Claude Code | `~/.claude/skills/` |
| Codex / OpenCode | `~/.codex/skills/`（OpenCode 自动扫描 Claude/Codex 目录） |

**验证安装**：对 Agent 说"检查 deep-research-plus 的子技能是否齐全"，它会 Glob 四个子技能路径并报告降级状态。

### 最小安装（仅编排层）

```bash
git clone https://github.com/Asaceoo/deep-research-plus-skills.git
mkdir -p ~/.workbuddy/skills/deep-research-plus
cp deep-research-plus-skills/SKILL.md ~/.workbuddy/skills/deep-research-plus/SKILL.md
```

**依赖**：宿主 Agent 需支持 Read / Write / Glob / WebSearch / WebFetch / Task（子代理）/ AskUserQuestion。

### 关于捆绑子技能

四个子技能（deep-research / research / agent-reach / market-researcher）已随仓库捆绑在 `sub-skills/`，**版权仍归各自作者**（见 [THIRD-PARTY-NOTICES.md](../THIRD-PARTY-NOTICES.md)）。完整安装后无任何降级；不装也能跑——技能启动时会自动检测子技能，缺失的按降级模式执行并在报告开头注明。

## 3. 怎么触发

对 Agent 说一句即可语义触发：

```
用 deep-research-plus 调研 主流开源社媒抓取工具对比
```

触发词：`深度调研`、`深度研究`、`系统调研`、`deep research`、`调研一下 X`、`帮我深挖`。

## 4. 核心概念一：复杂度分档（v1.1.0 新增）

启动后 Agent 会判定（或询问你）调研档位：

| 档位 | 适合 | 资源消耗 |
|------|------|----------|
| **轻量** | 单一事实核查、≤3 个条目 | 主代理直接搜，不派子代理，最快 |
| **标准**（默认） | 3-8 个条目的横评/选型 | 2-3 路并行子代理 |
| **深度** | >8 条目、跨领域、明确说"深度/全面" | 全编队并行 + 反方评审全开 |

分档结果会告知你，可手动升降档。**建议**：日常横评用标准档即可；不确定就让它自己判。

## 5. 核心概念二：两道确认闸门

调研过程有两次 🛑 硬停，**必须你点头才会继续**：

1. **Phase 2 大纲确认**：Agent 产出调研大纲（查什么 items + 看哪些字段 fields），你可以增删条目、加字段、调档位。确认后才开始搜索（消耗 token 的环节从此开始）。
2. **Phase 3.5 反方评审**（自动，无需你操作）：报告定稿前的机器质检——每条结论必须能回指到具体证据，官方自述数字会被标注"未见第三方复现"，只有一个来源的结论标 `single-source`。

## 6. 报告怎么读

产出 `report.md` 固定六章结构：

```
1. 核心结论（TL;DR）   ← 每条带 [^n] 引用，单源结论有 single-source 标记
2. 对比总表            ← 所见即最新，注明数据截点日期
3. 逐项详析            ← 事实 → 证据（含来源类型）→ 反证/不确定性
4. 冲突与存疑          ← 多源矛盾单列，不强行和稀泥
5. 未覆盖与限制        ← 没查到的如实列出（不是漏，是诚实）
6. 来源清单            ← 全部 URL 按类型分组
```

**阅读建议**：先看 §1 拿结论，再看 §4 判断结论可信度（有"官方口径"标注的数字要打折扣），引用 §6 可溯源。

## 7. 可选升级交付

报告完成后可要求：

- **杂志风 HTML 信息图**：编辑风版式 + 动画 + 微交互，适合分享汇报（默认推荐）
- **播客/思维导图/测验**：经 NotebookLM 生成（依赖 Google 网络可达，不可达会明确告知并跳过）

## 8. FAQ

**Q: 四个子技能都没装会怎样？**
A: 全降级模式：内置流程 + WebSearch/WebFetch 照常出报告，报告开头注明"实际使用工具组合"。深度能力（结构化 YAML、社媒源、商业标注）会缩水。

**Q: 调研中断了怎么办？**
A: 直接说"继续"。已完成的条目已落盘 `results/`，重跑只补缺失项，不重复消耗搜索。

**Q: 商业/市场类调研有什么特别？**
A: 自动启用商业标注规范：每条数据带来源+日期；定量结论暴露计算公式与假设；查不到的数据标 `partial`——**不编造数字**。

**Q: 为什么报告里有的数字标了"官方口径"？**
A: 该数字仅来自当事方自述（官方博客/自建基准），无第三方复现。这是反方评审的诚实标注，不代表数据是错的，但你应知情。

**Q: 轻量档会跳过反方评审吗？**
A: 会跳过正式评审（2-3 条结论做口头核查即可）；标准/深度档强制评审。

**Q: 能调并行度吗？**
A: 能。Phase 2 确认大纲时直接说"并成 2 路"或"每项独立子代理"。

## 9. 边界与免责

- 社媒平台需 cookie/代理时自动跳过该频道，不算调研失败。
- 报告结论受**数据截点**限制：调研日期之后的动态不在覆盖范围。
- 反方评审修订上限 2 轮：超出的信息缺口会列在 §5，而不是无限补搜。
