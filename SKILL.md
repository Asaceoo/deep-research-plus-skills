---
name: deep-research-plus
description: "深度调研融合编排层：跨平台通用（Claude / Codex / Cursor / WorkBuddy / WPS AI / OpenCode / OpenClaw 等任何能读 Markdown 的智能体）。按话题类型路由信息源（官方一手来源 / 社媒社区信号 / 商业标注规范），跑「大纲→确认→并行深调→反方评审→报告」流水线，每条结论带一手引用，并用内置脚本做阶段闸门硬校验。Use when user asks 深度调研/深度研究/deep research/系统调研一个话题，或需要带引用的结构化调研报告。Triggers: '深度调研', '深度研究', '系统调研', 'deep research', '调研一下 X', '帮我深挖'."
version: 1.4.1
license: MIT
visibility: "public"
---

## 中文备注
- **一句话**：深度调研总编排——按话题类型路由到最合适的源（官方文档走一手来源、社媒舆情走社区信号、商业分析走标注规范），产出每条结论带引用的 Markdown 报告，并用脚本闸门卡住"没证据就下结论"。
- **适用场景**：系统调研一个技术话题/产品/行业、工具横评、竞品分析、选型对比、舆情洞察——比单次搜索深、比普通 deep research 多源且带一手引用。
- **类别**：调研（编排层）｜ **跨平台**：无平台专属工具硬依赖，能力缺失逐项降级。
- **注意**：本技能是编排层，不复制子技能正文；子技能缺失时降级为内置搜索多路深调；商业类结论必须带来源+日期，缺数据标 `partial`，禁止编造。
<!-- /中文备注 -->

# Deep Research Plus — 深度调研融合流水线（跨平台通用版）

> 编排层技能：融合调研能力，输出带一手引用的结构化报告。任何具备「网络搜索 + 对话确认」能力的 AI 智能体均可执行。
> **原则：指针不重复**——子技能的详细流程以指针表引用，本文件只定义「怎么串」。
> **原则：闸门可执行**——阶段放行不靠自觉，靠 `scripts/drp.py` 的退出码；没有命令执行能力的平台退回人工复核，并在报告头注明。

## 能力需求与降级（平台适配层）

按所在平台实有能力执行，**每项都有降级路径**，缺什么降什么，报告开头注明实际能力组合：

| 能力 | 需要 | 有 | 缺失 → 降级 |
|------|------|----|-----------|
| 网络搜索 | 必需 | WebSearch / 联网检索 / 搜索插件 | 无搜索能力无法执行本技能，直接告知用户并终止 |
| 网页抓取 | 可选 | WebFetch / 浏览器 / 读 URL | 仅用搜索摘要作证据，引用标 `summary-level`（未经原文核验） |
| 对话确认 | 必需 | 任意能与用户往轮对话的机制 | 无（对话本身即确认通道） |
| 子代理并行 | 增强 | Task / 子 agent / 后台任务 | 主代理逐项串行：每完成一个 item 先写一行小结再搜下一项，防上下文过载 |
| 文件写入 | 可选 | Write / 文件保存 | 报告分段输出在对话；大纲与结果以对话消息留存，断点续跑引用上一轮内容 |
| 文件读取 | 可选 | Read / 读工作区 | 子技能探测跳过，按全降级模式跑 |
| 命令执行 | 增强 | Bash / 终端 / 代码执行 | 全部闸门降级为人工复核，报告头标 `manual-gate`；本文件其余流程不变 |

## 依赖子技能（可选增强，自动检测）

| 子技能 | 角色所在 | 常见安装位置（存在才用） | 缺失时降级 |
|--------|----------|--------------------------|-----------|
| `deep-research` | 主干：outline → 确认 → 深调 → report 四阶段 | 各平台 skills 目录下的同名目录 | 内置流程替代（Phase 1 简化为对话确认清单） |
| `research` | 引用纪律：追一手来源，每条结论带引用 | 同上 | 纪律保留，用搜索+抓取执行 |
| `agent-reach` | 源路由扩展：Twitter/Reddit/YouTube/B站/小红书/微博/GitHub issue 等 14 平台 | 同上 | 跳过社媒源，仅通用搜索 |
| `market-researcher` | 商业标注规范：来源+日期、定量暴露假设、缺数据标 partial | 同上 | 跳过，按通用引用规范 |

**检测方法**：跑 `python scripts/drp.py detect`，脚本按 `~/.workbuddy/skills/`、`~/.claude/skills/`、`~/.codex/skills/`、`~/.config/opencode/skills/`、项目内 .skills 与 skills 目录、技能根下 sub-skills 目录的顺序探测，输出命中路径与降级清单。
**无法执行脚本时**：按上表手工确认一遍，缺哪个按降级列执行；无法读文件系统则按全降级模式跑。
**分发边界**：源码仓库随附 sub-skills 目录（版权归原作者，见 THIRD-PARTY-NOTICES.md），克隆安装即零降级；发布 zip 只含编排层，不含子技能，从 zip 安装时 detect 会列出降级项。

## 机器契约（工具层）

`scripts/drp.py` 单文件、零第三方硬依赖（有 PyYAML 用它，没有回退内置子集解析）。退出码：`0` 通过 / `1` 有违规 / `2` 用法或环境错误。

| 命令 | 作用 | 失败含义 |
|------|------|----------|
| `python scripts/drp.py validate` | 校验技能包：frontmatter、悬空路径、文档版本一致、清单规则 | 技能包自身损坏，禁止发布 |
| `python scripts/drp.py detect` | 探测四个依赖子技能并给出降级方案 | 仅提示，不阻断 |
| `python scripts/drp.py init --workspace <dir> --topic "<话题>"` | 生成 outline.yaml / fields.yaml / review.yaml 骨架 | 目录非空且未加 --force |
| `python scripts/drp.py gate --workspace <dir> --stage outline` | Phase 1 预检：条目互斥、反方条目存在、字段已定义 | 大纲不合格，返工 |
| `python scripts/drp.py gate --stage confirm` | Phase 2 闸门：确认已落盘且含时间与人 | 用户未确认就开跑 |
| `python scripts/drp.py gate --stage results` | Phase 3 校验：https 链接、日期、source_type、反方证据 | 证据不合格，禁入评审 |
| `python scripts/drp.py gate --stage review` | Phase 3.5 校验：证据绑定、单源/高风险标记、轮次上限 | 评审走过场 |
| `python scripts/drp.py report --workspace <dir>` | 渲染 report.md（六章结构 + 尾注引用） | 缺输入文件 |
| `python scripts/drp.py gate --stage report` | Phase 4 校验：章节齐全、尾注可解析、无裸域名、无 AI 腔 | 报告不合格 |
| `python scripts/drp.py bump --level auto` | 版本递增并同步 SKILL.md / 文档 / README / CHANGELOG | 版本号不一致 |
| `python scripts/drp.py package` | 自动递增 + 全量校验 + 构建 zip/SHA256/release notes | 校验未过则中止 |
| `python scripts/drp.py selfcheck` | 清单逐条复核 + 内置流水线回归（兜底） | 有规则未过 |

**闸门用法**：每次进入下一阶段前跑一次对应 `gate --stage`；退出码非 0 就停在原地补齐，禁止"先写报告再补证据"。

## 流水线

### Phase 0 — 意图分流 + 复杂度分档（先定性定量，再选路）

向用户确认（或从话题直接推断）调研类型：

| 话题类型 | 主干 | 增强源 |
|----------|------|--------|
| 技术/选型/工具横评 | 四阶段主干 | 一手来源纪律（官方 docs、源码仓库） |
| 产品/行业/市场 | 四阶段主干 | 商业标注规范 |
| 舆情/口碑/社区洞察 | 社区源为主 | 主干的 outline 结构组织条目 |
| 综合（默认） | 四阶段主干 | 三者按需混合 |

**复杂度分档**（判据互斥，不重叠；简单话题跑全编队是 token 浪费）：

| 档位 | 判据（条目数） | 资源配置 |
|------|----------------|----------|
| `light` 轻量 | 1-3 个 items，单一事实核查或小范围对比 | 直接搜，不派子代理；口头确认；产出对话答复 |
| `standard` 标准（默认） | 4-8 个 items 的横评/选型 | 按源路由分 2-3 路（有子代理并行，无则串行） |
| `deep` 深度 | ≥9 个 items、跨领域，或用户明说"深度/全面" | 每项独立深调 + 反方评审全开 + 承重引用逐条开页 |

分档结果告知用户，用户可手动升降档；升降档后重跑 `gate --stage outline`。

### Phase 1 — 大纲与字段

1. 生成 items + fields 初稿；叠加源路由：官方类查文档/源码，社区/社媒类走对应渠道。
2. 落盘 `outline.yaml`（topic / slug / tier / type / items）与 `fields.yaml`（name / type / required）。
3. 跑 `python scripts/drp.py gate --workspace <dir> --stage outline`。

**大纲级预检**（脚本强制）：条目互斥不重叠（标题唯一）、至少 1 个 `kind: counter` 的反方条目（竞品反对观点/已知缺陷/失效场景）、字段引用已定义、档位与条目数匹配。
缺反方条目的大纲天然只收正面证据，`gate` 会直接判 P0 拦下。

**引用纪律注入**：每个事实型字段必须含 `source_url`（https 完整链接）+ `date`（YYYY-MM-DD）+ `source_type`（official / code / secondary / community / journalism）。

### Phase 2 — 确认闸门（🛑 硬停）

向用户展示 outline + fields，**明确确认后**才进入深调（交互组件平台用选项卡；对话平台直接问"确认后回复'开始'"）。用户可增删条目、加字段、调并行度与分档。

确认后把结果写回 `outline.yaml`：`confirmed: true`、`confirmed_at: YYYY-MM-DD`、`confirmed_by: <谁确认的>`，再跑 `gate --stage confirm`。
没落盘就等于没确认，闸门不放行。

### Phase 3 — 深调（有子代理则并行，无则串行）

逐项搜索，执行两条硬纪律：

1. **一手来源优先**：每个 item 先查官方文档/源码/spec，二手文章只作补充；引用追溯到拥有该事实的源头。
2. **源路由**：用户反馈/真实使用信号 → 社区渠道（Reddit/GitHub issues/B站/小红书等）；统计与新闻 → 通用搜索。

商业类话题同时执行商业标注规范：每条数据带来源+日期；定量结论暴露公式、输入值、假设类型；查不到的数据标 `partial`，**禁止编造数字**。

结果写 `results/item_N.yaml`，单条 finding 的最小结构：

```yaml
item_id: 1
status: done
findings:
  - id: f1
    claim: 一句话结论
    value: 关键数值或事实
    field: license
    source_url: https://example.com/doc
    source_type: official
    date: 2026-10-01
    polarity: neutral      # 反方证据写 negative
uncertainties: []
```

落盘后跑 `gate --stage results`。

**回传纪律**（有子代理时）：子代理只回传**结构化 findings 文本**（事实+URL+日期），不回传原始网页内容——防上下文污染（Anthropic 一手经验：上下文污染是多 agent 系统头号故障源）。串行模式下每项完成后先写一行小结再搜下一项，等价实现。

**断点续跑**：每完成一个 item 立即落盘。中途中断后重跑，先看 `results/` 已有编号，只补缺失项。

### Phase 3.5 — 反方评审闸门（🛑 起草后、定稿前）

报告汇总前，以**质疑者视角**对结果与起草结论做一轮对抗审查，结论写 `review.yaml`：

1. **证据绑定检查**：每条将写入报告的结论必须回指到具体证据 id（来源 URL + 类型 + 日期）；回指不到的结论降级为存疑，进「冲突与存疑」章节，不得以"综合判断"名义保留。
2. **承重引用内容对照**：对 TL;DR 中 3-4 条决策级结论，逐条打开源页面核对**内容是否支撑该结论**（不是检查链接是否存在——行业数据表明 77% 的引用错误是"链接真但内容不支撑"的误引用）。
3. **官方数据偏差检查**：性能/份额/准确率类数字若仅来自当事方自述，标注"官方口径，未见第三方复现"。
4. **单源与来源类型标记**：仅一个来源支撑的结论标 `single-source`；决策级结论仅由社区/用户生成内容支撑的标 `high-risk`（带脚注的谣言）。
5. **修订上限 2 轮**：评审缺漏最多补搜 2 轮，超出列入「未覆盖」，不无限补（`rounds` 超过 2 会被 `gate --stage review` 判 P0）。

`review.yaml` 结构：

```yaml
rounds: 1
capabilities: 串行+抓取
decisions:
  - id: d1
    claim: 结论本身
    level: decision        # decision | supporting
    evidence: [f1, f3]
    flags: [single-source]
conflicts: []
uncovered: []
corrections:
  - 删掉 1 条无证据结论，补搜 1 轮
```

跑 `gate --stage review`，通过后再汇总。**去 AI 腔**：汇总行文时逐条过「反例黑名单」§R2。

### Phase 4 — 汇总报告

`python scripts/drp.py report --workspace <dir>` 渲染 `report.md`，再跑 `gate --stage report` 校验。强制结构：

```markdown
# <话题> 深度调研报告
> 调研日期：YYYY-MM-DD ｜ 方法：deep-research-plus vX（分档：standard/deep）｜ 能力组合：并行/串行+抓取/摘要级 ｜ 评审：反方评审已过
## 1. 核心结论（TL;DR）        # 每条结论尾注 [^n] 引用，单源标 single-source，高风险标 high-risk
## 2. 对比总表                  # 所见即最新，注明数据截点
## 3. 逐项详析                  # 每 item：事实 → 证据（含 source_type）→ 反证/不确定性
## 4. 冲突与存疑                # 多源矛盾点 + 证据绑定降级项 + 官方口径数字，单列不和稀泥
## 5. 未覆盖与限制              # 反方评审 2 轮后仍未查到的，如实列出
## 6. 来源清单                  # 全部 URL 按类型分组；必须写完整 https:// 可点击链接，每条带日期
```

无文件能力时按同样六章结构分段输出在对话，尾注改为行内链接。

### Phase 5 — 交付升级（可选，用户点头才做）

| 升级 | 方式 | 条件 |
|------|------|------|
| 杂志风 HTML 信息图 | 按 editorial 风格（动画 + 微交互）重排报告核心内容 | 平台具备代码生成/文件能力 |
| 播客/思维导图 | NotebookLM 类工具导入 report.md | 依赖外部服务可达；不可达时明确告知并跳过 |

## 闸门矩阵（按档位）

| 档位 | Phase 1 outline 闸门 | Phase 2 confirm 闸门 | Phase 3 results 闸门 | Phase 3.5 review 闸门 | Phase 4 report 闸门 | 允许的省略 |
|------|----------------------|----------------------|----------------------|------------------------|---------------------|------------|
| `light` | 必跑（`gate --stage outline`） | 口头确认 + `confirmed: true` | 必跑 | 自查 2 条结论，不落 review.yaml | 不适用：产出对话答复，不落 report.md | 子代理、HTML 升级、review.yaml |
| `standard` | 必跑 | 必跑 | 必跑 | 必跑（`rounds` ≤2） | 必跑 | 子代理可换串行 |
| `deep` | 必跑 | 必跑 | 必跑 | 必跑 + 承重引用逐条开页核对 | 必跑 | 仅 HTML 升级按需 |

无命令执行能力的平台：上表所有"必跑"改为人工逐条对照本节与各 Phase 的检查项，报告头标 `manual-gate`。

## 反例黑名单（全程对照，违反即返工）

| # | 反模式 | 替代做法 |
|---|--------|----------|
| R1 | 大纲只收正面证据 | 每份大纲必须含 1-2 个反方 item（Phase 1 预检强制） |
| R2 | AI 腔行文：套话（"值得注意的是/总而言之/综上所述"）、无基准修饰（"显著/大幅"）、三连形容词、铺垫式开头 | 删除套话；有对比基准才写"比 X 高 N%"；每节首句直接给事实或判断 |
| R3 | 编造数字 / 填补数据空洞 | 查不到就标 `partial` / `uncertain`，进「冲突与存疑」或「未覆盖」 |
| R4 | 裸域名或 http 链接当引用（如"来源：arxiv.org"） | 必须写完整 `https://` 可点击链接，每条带日期 |
| R5 | 以"综合判断"名义保留无证据结论 | 回指不到证据的结论降级为存疑，进「冲突与存疑」 |
| R6 | 决策级结论仅单源或仅社区内容支撑 | 标 `single-source` / `high-risk`，正式场合不采信 high-risk |
| R7 | 评审缺漏反复补搜没有上限 | 最多 2 轮，超出列入「未覆盖」 |
| R8 | 报告头缺元信息（日期/分档/能力组合/评审状态） | 六章模板首行固定写全四项 |

## 使用示例

**技术选型**："深度调研一下 2026 年主流开源 TTS 方案，帮我选型。"
Phase 0 判 `deep` 档（若只比 6 个方案则 `standard`）→ `init` 生成骨架 → 补成 6 个 items（含 1 个 counter："各方案已知缺陷与社区吐槽"）→ `gate --stage outline` → 🛑 用户确认并落 `confirmed: true` → 并行深调，每项落 `results/item_N.yaml` → `gate --stage results` → 反方评审写 `review.yaml`（TL;DR 承重引用逐条开页对照）→ `gate --stage review` → `report` 渲染 → `gate --stage report` → 交付 `report.md`。

**市场/商业**："调研国内免漆门行业的渠道结构。"
`type: market`，商业标注规范全开：每条数据带来源+日期，定量结论写清口径与假设，查不到的产能数据标 `partial` 并进「未覆盖」。

**舆情/社区**："看看 B 站和小红书上对某款剪辑软件的真实评价。"
`type: community`，社区源为主；决策级结论若只有用户生成内容支撑，标 `high-risk`，并补一条官方口径交叉验证。

**轻量对照**："帮我查一下 X 的最新版本号。"
`light` 档：直接搜，口头确认，不派子代理，不落 report.md，不跑全流水线。

## 产物布局

```
{topic_slug}/
  outline.yaml        # Phase 1：条目 + 档位 + 确认状态
  fields.yaml         # Phase 1：字段定义
  results/item_N.yaml # Phase 3：逐项证据（含 URL/日期/类型）
  review.yaml         # Phase 3.5：决策 + 证据绑定 + 存疑
  report.md           # Phase 4：六章报告
```

## 版本与发布

- 版本号单一事实源：`SKILL.md` 的 frontmatter `version`。
- `python scripts/drp.py bump --level auto` 按 `CHANGELOG.md` 的 `[Unreleased]` 条目判定 major/minor/patch，并同步 `manifest.json`、`README.md`、`docs/*.md` 的版本与更新日期。
- `python scripts/drp.py package` 先递增再全量校验，通过才产出 `dist/deep-research-plus-v<版本>.zip` + `SHA256SUMS.txt` + `release-notes-v<版本>.md`。
- 发布前跑 `python scripts/drp.py selfcheck`：清单逐条复核 + 内置流水线回归，任一 FAIL 停发。

## 边界与降级总表

- 平台能力缺失 → 按能力矩阵降级列执行，报告头注明实际能力组合。
- 子技能缺失 → 按指针表降级列执行；无法检测文件系统时全降级。
- 社区平台需 cookie/代理时 → 跳过该频道，不算调研失败。
- 全程禁止编造：查不到就标 `partial` / `uncertain`，报告里单列。
- 相对时间一律写绝对日期 `YYYY-MM-DD`。
- 轻量档产出对话答复，不落 report.md；标准/深度档六章报告缺一章即判不合格。
