---
name: deep-research-plus
description: "深度调研融合编排层：把本机 4 个调研技能串成一条流水线——agent-reach 全网源路由 + research 一手来源引用纪律 + deep-research 结构化主干（大纲→确认→并行深调→反方评审→报告）+ market-researcher 商业标注规范。Use when user asks 深度调研/深度研究/deep research/系统调研一个话题，或需要带引用的结构化调研报告。Triggers: '深度调研', '深度研究', '系统调研', 'deep research', '调研一下 X', '帮我深挖'."
version: 1.2.0
license: MIT
allowed-tools: Read, Write, Glob, Grep, WebSearch, WebFetch, Task, AskUserQuestion
visibility: "public"
---

## 中文备注
- **一句话**：深度调研总编排——按话题类型路由到最合适的源（官方文档走一手来源、社媒舆情走 agent-reach、商业分析走 market-researcher 规范），用 deep-research 的四阶段结构跑主干，产出每条结论带引用的 Markdown 报告。
- **适用场景**：系统调研一个技术话题/产品/行业、工具横评、竞品分析、选型对比、舆情洞察——比单次搜索深、比纯 deep-research 多源且带一手引用。
- **类别**：调研（编排层）
- **注意**：本技能是编排层，不复制子技能内容；子技能缺失时降级为内置 WebSearch 多路搜索；notebooklm-studio 出口在本机依赖 Google 网络，不可达时跳过并说明；商业类结论必须带来源+日期，缺数据标 partial 不编造。
<!-- /中文备注 -->

# Deep Research Plus — 深度调研融合流水线

> 编排层技能：融合本机 4 个调研能力，输出带一手引用的结构化报告。
> **原则：指针不重复**——各子技能的详细流程以指针表引用，本文件只定义「怎么串」。
> v1.1.0 起，融入对标调研结论（Anthropic 多 Agent 系统 / GPT Researcher / RhinoInsight / daymade 等 8 方案），新增：复杂度分档（O1）、反方评审闸门（O2）、claim 级证据绑定（O3）。

## 依赖子技能（指针表）

| 子技能 | 路径 | 在流水线中的角色 | 缺失时降级 |
|--------|------|------------------|-----------|
| `deep-research` | `~/.workbuddy/skills/deep-research/SKILL.md` | **主干**：outline.yaml/fields.yaml → 确认 → 并行深调 → report.md 四阶段 | 用内置流程替代（Phase 1 简化为对话确认清单） |
| `research` | `~/.workbuddy/skills/research/SKILL.md` | **引用纪律**：追一手来源（官方文档/源码/spec），每条结论带引用 | 保留纪律本身，用 WebSearch+WebFetch 执行 |
| `agent-reach` | `~/.workbuddy/skills/agent-reach/SKILL.md` | **源路由扩展**：Twitter/Reddit/YouTube/B站/小红书/微博/GitHub issue 等 14 平台检索 | 跳过社媒源，仅 WebSearch |
| `market-researcher` | `~/.workbuddy/skills/market-researcher/SKILL.md` | **商业标注规范**（商业类话题启用）：来源+日期、定量暴露公式与假设、缺数据标 partial、结论带置信度 | 跳过，按通用引用规范 |

进入流水线前先确认子技能存在（Glob 各路径）；缺失的按降级列执行并在报告中注明。

## 流水线

### Phase 0 — 意图分流 + 复杂度分档（先定性定量，再选路）

用 AskUserQuestion 确认（或从话题直接推断）调研类型：

| 话题类型 | 主工具 | 增强源 |
|----------|--------|--------|
| 技术/选型/工具横评 | deep-research 主干 | research 一手来源纪律（官方 docs、GitHub 源码） |
| 产品/行业/市场 | deep-research 主干 | + market-researcher 标注规范 |
| 舆情/口碑/社区洞察 | agent-reach 为主 | deep-research 的 outline 结构组织条目 |
| 综合（默认） | deep-research 主干 | 三者按需混合 |

**复杂度分档**（依据 Anthropic 缩放规则 + Gemini 双档制；简单话题跑全编队是 token 浪费）：

| 档位 | 判据 | 资源配置 |
|------|------|----------|
| **轻量** | 单一事实核查、≤3 个 items、答案大概率一次搜索可得 | 主代理直接搜，不派子代理；跳过 Phase 2 闸门改为口头确认 |
| **标准**（默认） | 3-8 个 items 的横评/选型 | 按源路由分 2-3 路并行子代理 |
| **深度** | >8 items、跨领域、或用户明说"深度/全面" | 全编队并行 + 反方评审全开 + 每项独立子代理 |

分档结果告知用户，用户可手动升降档。

### Phase 1 — 大纲与字段（deep-research `/research` 阶段）

按 deep-research 的 research/SKILL.md 执行：内部知识生成 items + fields 初稿 → **web-search-agent 补充遗漏**（此处叠加源路由：官方类用 WebSearch/WebFetch，社区/社媒类信号用 agent-reach 频道）→ 用户确认 → 落盘 `{topic_slug}/outline.yaml` + `fields.yaml`。

**大纲级预检**（落盘前 30 秒自检）：items 是否互斥不重叠？是否有 1-2 个"反方 item"（竞品的反对观点/已知缺陷/失效场景）？缺反方视角的大纲天然只收正面证据，补上再确认。

**引用纪律注入**：fields.yaml 中每个事实型字段必须含 `source_url`；一级字段建议加 `source_type`（official / code / secondary / community / journalism）。

### Phase 2 — 确认闸门（🛑 硬停）

向用户展示 outline + fields，**明确确认后**才进入并行深调。用户可增删 items（`/research-add-items`）、加字段（`/research-add-fields`）、调并行度与分档。

### Phase 3 — 并行深调（deep-research `/research-deep` 阶段 + 双纪律）

按 deep-research 的 research-deep/SKILL.md 派子代理逐项搜索，执行两条硬纪律：

1. **一手来源优先**（来自 research）：每个 item 先查官方文档/源码/spec，二手文章只作补充；引用追溯到拥有该事实的源头。
2. **源路由**（来自 agent-reach）：user feedback / 真实使用信号 → agent-reach 平台频道（Reddit/GitHub issues/B站/小红书等）；统计与新闻 → WebSearch。

商业类话题同时执行 market-researcher 标注规范：每条数据带来源+日期；定量结论暴露公式、输入值、假设类型；查不到的数据标 `partial`，**不编造数字**。

结果写 `{topic_slug}/results/item_N.yaml`（含 source_url 数组）。

**子代理回传纪律**：子代理只回传**结构化 findings 文本**（事实+URL+日期），不回传原始网页内容、不写文件——防止原始搜索结果污染主上下文（Anthropic 一手经验：上下文污染是多 agent 系统头号故障源）。

**断点续跑**：每完成一个 item 立即落盘 results/。中途中断后重跑，先检查 `results/` 已有的 item 编号，只补缺失项，不重复消耗已完成的搜索。

### Phase 3.5 — 反方评审闸门（🛑 起草后、定稿前强制）

报告汇总前，以**质疑者视角**对 results + 起草结论做一轮对抗审查（依据 daymade 反方评审团 + RhinoInsight Evidence Audit——RACE 基准显示该机制显著提升引用准确率）：

1. **证据绑定检查（O3）**：每条将写入报告的结论必须能回指到 results 中的具体证据（来源 URL + 类型 + 日期）；回指不到的结论**降级为存疑**，进报告「冲突与存疑」章节，不得以"综合判断"名义保留。
2. **官方数据偏差检查**：性能/份额/准确率类数字若仅来自当事方自述（官方博客、自建基准），标注"官方口径，未见第三方复现"。
3. **单源结论标记**：仅一个来源支撑的结论，标注 `single-source`。
4. **修订上限 ≤2 轮**：评审发现的缺漏最多补搜 2 轮，超出部分如实列入「未覆盖」，不无限补——防止调研变永不收敛。

**去 AI 腔清单**（汇总行文时逐条过）：删除"值得注意的是/总而言之/综上所述"套话；数字不加"显著/大幅"修饰（有对比基准才可写"比 X 高 N%"）；结论句不堆叠三个以上形容词；每节首句直接给事实或判断，不用铺垫句。

### Phase 4 — 汇总报告（deep-research `/research-report` 阶段）

按 research-report/SKILL.md 汇总为 `{topic_slug}/report.md`，强制结构：

```markdown
# <话题> 深度调研报告
> 调研日期：YYYY-MM-DD ｜ 方法：deep-research-plus vX（分档：标准/深度）｜ 评审：反方评审已过
## 1. 核心结论（TL;DR）        # 每条结论尾注 [^n] 引用，单源结论标注 single-source
## 2. 对比总表                  # 所见即最新，注明数据截点
## 3. 逐项详析                  # 每 item：事实 → 证据（含 source_type）→ 反证/不确定性
## 4. 冲突与存疑                # 多源矛盾点 + 证据绑定降级项 + 官方口径数字，单列不和稀泥
## 5. 未覆盖与限制              # 反方评审 2 轮后仍未查到的，如实列出
## 6. 来源清单                  # 全部 URL 按类型分组
```

### Phase 5 — 交付升级（可选，用户点头才做）

| 升级 | 方式 | 条件 |
|------|------|------|
| 杂志风 HTML 信息图 | 按 editorial 风格（动画 + 微交互）重排报告核心内容 | 默认推荐 |
| 播客/思维导图/测验 | notebooklm-studio 导入 report.md | **仅当 Google 可达**；不可达时明确告知并跳过 |

## 边界与降级总表

- 子技能缺失 → 按指针表降级列执行，报告开头注明实际使用的工具组合。
- agent-reach 平台需 cookie/代理时 → 跳过该频道，不算调研失败。
- 全程不编造：查不到就标 `partial` / `uncertain`，报告里单列。
- 相对时间一律写绝对日期 `YYYY-MM-DD`。
- 轻量档允许跳过 Phase 3.5（2-3 条结论的口头核查即可），标准/深度档强制。
