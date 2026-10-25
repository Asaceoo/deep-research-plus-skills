# 技术手册

> 版本：1.6.0 ｜ 更新：2026-10-26 ｜ 适用技能：deep-research-plus

## 1. 设计目标与不变量

| # | 不变量 | 落地方式 |
|---|--------|----------|
| I1 | 版本号只有一个事实源 | `SKILL.md` frontmatter `version`；`bump` 从它推导并回写其余文件 |
| I2 | 闸门可执行，不靠自觉 | 每个阶段一个 `gate --stage`，退出码 0/1/2 |
| I3 | 规则不得静默失效 | 清单里出现未知规则类型 → 直接 P1，不跳过 |
| I4 | 引用可回指 | 结论必须绑定 finding id；finding 必须带 https URL + 日期 + 类型 |
| I5 | 零第三方硬依赖 | 全部脚本 stdlib；PyYAML 只是加速路径 |
| I6 | 产物可校验 | zip 内 `BUILD-MANIFEST.json` 逐文件 sha256；外层 `SHA256SUMS.txt` |

## 2. 架构

```
SKILL.md                 技能入口，只写「怎么串」+ 能力矩阵 + 闸门矩阵
checklists/
  skill_audit.yaml       八条机器规则（文本层约束）
scripts/
  drp.py                 单文件工具层
    ├── YAML 层          PyYAML 优先 / yamlmini 子集兜底
    ├── 校验层           frontmatter / 路径 / 版本 / 许可 / 结构 / 清单规则
    ├── 闸门层           outline / confirm / results / review / report
    ├── 渲染层           report.md 六章 + 尾注自动编号
    └── 发布层           bump / package / selfcheck
docs/                    用户手册 · 技术手册 · 对抗性审查记录 · 概念图
tests/                   单元 / 契约 / 端到端 / 负路径
```

分层原则：`SKILL.md` 面向模型，`checklists` 面向文本约束，`scripts` 面向可判定事实。三者不互相复制内容，避免改一处漏三处。

## 3. 数据契约

### 3.1 outline.yaml

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `topic` | str | 是 | 话题原文 |
| `slug` | str | 是 | 产物目录名 |
| `tier` | enum | 是 | `light` / `standard` / `deep` |
| `type` | enum | 是 | `tech` / `market` / `community` / `mixed` |
| `confirmed` | bool | Phase 2 起必填 | 必须为 `true` 才放行 |
| `confirmed_at` | str | Phase 2 起必填 | `YYYY-MM-DD`，不得晚于今天 |
| `confirmed_by` | str | Phase 2 起必填 | 谁确认的（用户标识） |
| `items[]` | list | 是 | 非空；id 唯一；title 唯一 |
| `items[].id` | int | 是 | 与 `results/item_<id>.yaml` 对应 |
| `items[].kind` | enum | 否 | `normal`（默认）/ `counter` |
| `items[].fields` | list[str] | 否 | 必须在 fields.yaml 中定义 |
| `items[].status` | enum | 否 | `pending` / `done` / `partial` |
| `items[].min_sources` | int | 否 | 来源数下限；缺省 = 档位基数（light 1 / standard 2 / deep 3）+ 反方条目 1 |

档位与条目数：`light` 1-3，`standard` 4-8，`deep` ≥9。超出即 P0/P1 拦截。

### 3.2 fields.yaml

| 字段 | 类型 | 约束 |
|------|------|------|
| `fields[].name` | str | 唯一，被 outline 引用 |
| `fields[].type` | enum | `fact` / `judgement` |
| `fields[].required` | bool | 缺省 true |

### 3.3 results/item_N.yaml

| 字段 | 类型 | 约束 |
|------|------|------|
| `item_id` | int | 必须等于文件名中的 N |
| `status` | enum | `pending` / `done` / `partial` |
| `findings[].id` | str | 全局唯一（跨 item） |
| `findings[].claim` | str | ≥8 字符 |
| `findings[].value` | str | 关键数值/事实，可比总表直接取用 |
| `findings[].field` | str | 关联 fields.yaml，用于字段覆盖检查 |
| `findings[].source_url` | str | 必须 `https://` 开头 |
| `findings[].source_type` | enum | `official` / `code` / `secondary` / `community` / `journalism` |
| `findings[].date` | str | `YYYY-MM-DD`，不得晚于今天 |
| `findings[].polarity` | enum | `positive` / `negative` / `neutral` |
| `uncertainties[]` | list[str] | 反方条目的兜底证据 |

### 3.4 review.yaml

| 字段 | 类型 | 约束 |
|------|------|------|
| `rounds` | int | 1-2；>2 判 P0（R7） |
| `capabilities` | str | 写入报告头的能力组合 |
| `decisions[].id` | str | 唯一 |
| `decisions[].claim` | str | 不得命中 AI 腔黑名单 |
| `decisions[].level` | enum | `decision` / `supporting` |
| `decisions[].evidence` | list[str] | 必须全部命中 findings id，否则 P0（R5） |
| `decisions[].flags` | list[str] | `single-source` / `high-risk`，由闸门强校验 |
| `spot_checks[].decision_id` | str | 必须命中该决策 id（v1.5.0 起决策级强制） |
| `spot_checks[].url` | str | 必须在该决策 `evidence` 推出的 URL 集合内 |
| `spot_checks[].verdict` | enum | `supports` / `contradicts` / `blocked` |
| `spot_checks[].note` | str | 开页看到什么，一句话 |
| `conflicts[]` | list[str] | 进报告第 4 章 |
| `uncovered[]` | list[str] | 进报告第 5 章 |
| `corrections[]` | list[str] | 记录本轮评审改了什么 |

### 3.5 report.md

六章固定标题（缺一即 P0）：核心结论 / 对比总表 / 逐项详析 / 冲突与存疑 / 未覆盖与限制 / 来源清单。
首行元信息必须含四项：`调研日期`、`分档`、`能力组合`、`评审`。
尾注 `[^id]` 必须在来源清单有 `[^id]: <https://...> ｜ YYYY-MM-DD ｜ type` 定义。

## 4. 闸门实现

| stage | 入口函数 | 主要检查 | 失败码段 |
|-------|----------|----------|----------|
| outline | `gate_outline` | 字段齐全、id/标题唯一、反方条目、档位条目数、字段引用 | G-OUT-00x |
| confirm | `gate_confirm` | `confirmed=true`、日期合法且非未来、确认人非空 | G-CON-00x |
| results | `gate_results` | 文件对应、finding 必填、https、日期、类型、反方证据、字段覆盖 | G-RES-00x |
| review | `gate_review` | 轮次 ≤2、决策非空、证据 id 命中、单源/社区源标记、AI 腔 | G-REV-00x |
| report | `gate_report` | 六章齐全、元信息、尾注可解析、裸域名、AI 腔、TL;DR 数量 | G-REP-00x |

### 4.1 严重级语义

| 级别 | 含义 | 打包时 |
|------|------|--------|
| P0 | 事实错误/契约破坏，继续跑一定产出错误结果 | 阻断 |
| P1 | 规范违背，结果可信度受损 | 阻断 |
| P2 | 建议性/覆盖度提示 | 记 warnings，不阻断 |

### 4.2 关键判定逻辑

- **单源判定**：`decisions[].evidence` 推出的 URL 去重集合大小为 1 → 必须含 `single-source`。
- **高风险判定**：证据的 `source_type` 集合 ⊆ {`community`, `secondary`} 且 level=decision → 必须含 `high-risk`。
- **字段覆盖判定**（v1.4.1 起为 P1）：`outline.items[].fields` 声明过的字段，必须至少被该 item 的一条 finding 的 `field` 命中。字段是 Phase 2 与用户确认过的契约，整块缺证等于契约破坏，不能只给警告。
- **来源覆盖率**（v1.5.0 起）：每个 item 的独立 URL 数必须 ≥ 档位基数（light 1 / standard 2 / deep 3）+ 反方条目 1；`min_sources` 可显式覆盖。只搜一次就落盘会被 G-RES-017 拦。
- **反方来源类型**：`kind: counter` 的 item 至少要有 1 条 `official` 或 `code` 来源，避免用单条社区吐槽充当反证（G-RES-018）。
- **链接形态**：命中 `example.com` / `placeholder` / `does-not-exist` 等占位特征直接判 G-RES-019，不需要联网。
- **链接核验（可选）**：`--check-links` 触发 HEAD 探测，2xx/3xx 视为可达、401/403/405/429 视为「反爬不可判」、404/410 判 G-RES-020、网络层失败判 G-RES-021。默认关闭，离线路径零网络依赖。
- **开页留痕**：决策级结论必须有 `spot_checks` 记录（G-REV-013），且 `url` 必须落在该结论证据里（G-REV-014），`verdict` 三值枚举（G-REV-015）。这是把「承重引用逐条开页」从口头要求变成可查字段。
- **复核轮次**：`rounds > 2` 直接失败，而不是警告——无限补搜是流程失控的典型信号。
- **AI 腔**：正则黑名单在 `SKILL.md`（跳过「反例黑名单」章节）与 `report.md/review.yaml` 全文分别扫描；后者不豁免任何章节。

## 5. 规则引擎（清单层）

`checklists/skill_audit.yaml` 的每条规则是 `{id, type, severity, params}`。已实现的 type：

| type | 作用 | 关键参数 |
|------|------|----------|
| `gate_matrix` | 校验档位×闸门矩阵表存在 | 无 |
| `conflict_pairs` | 两组正则不得同时出现（自相矛盾检测） | `pairs` |
| `forbidden_patterns` | 禁用语扫描 | `patterns`、`ignore_in_sections` |
| `required_patterns` | 必需内容扫描 | `patterns`、`hint` |
| `claim_requires_dir` | "已捆绑"类声明必须目录真实存在 | `claims[].pattern/requires_dir` |
| `manifest_files_exist` | manifest 字段齐全 + 登记文件存在 | `required_keys` |
| `test_prompts_present` | 消费者回归用例存在且含 anomaly 场景 | `path`、`min_prompts`、`min_anomaly` |

扩展方式：实现 `check_xxx(skill_dir, body, params, rule_id, severity)`，注册进 `RULE_HANDLERS`，再写清单条目。
**未注册的 type 会产出 `CHK-000` P1**，这是刻意设计：清单加错字不能导致"检查通过"。

## 6. 错误码速查

| 段 | 覆盖 | 处理方向 |
|----|------|----------|
| FM-002..005 | frontmatter 缺字段/版本非法/名称不一致/缺 Triggers | 改 SKILL.md 头部 |
| SEC-001..003 | 缺章节/缺阶段/缺硬停标记 | 补结构 |
| PATH-001/003/004 | 相对路径不存在/虚假捆绑声明/疑似笔误 | 删指针或补文件 |
| DOC-001/002 | 文档缺版本头/版本不一致 | `bump` 或手工同步 |
| LIC-001 | 声明 license 无 LICENSE | 补文件 |
| MAN-001/002 | manifest 版本与 SKILL 不一致 / 名称与目录不一致 | 跑 `bump` 或改 manifest |
| CHK-001..010 | 清单规则命中 | 按 detail 修 SKILL.md 或补文件 |
| G-OUT-001..018 | 大纲问题 | 见用户手册 §8 |
| G-CON-001..005 | 未确认/日期非法/确认人缺失 | 补 confirmed 三件套 |
| G-RES-001..021 | 证据缺失 / 链接非 https / 日期非法 / 类型非法 / 来源数不足 / 占位链接 / 死链 | 补证据字段或换真实来源 |
| G-REV-001..015 | 评审缺失 / 轮次超限 / 证据未绑定 / 未标标记 / 开页留痕缺失 | 补 review.yaml |
| G-REP-001..011 | 报告缺章/尾注未定义/裸域名/AI 腔/缺数据截点/来源未分组 | 重跑 `report` |

## 7. YAML 解析层

策略：`import yaml` 成功则用 PyYAML（自定义 loader 把 timestamp 保持为字符串，避免与内置解析结果不一致）；失败则用 `loads()`。

`yamlmini` 支持的子集：注释、嵌套映射、`- ` 序列（含 `- key: value` 起头的映射项）、行内 `[a, b]` / `{k: v}`、单双引号、整数/浮点/布尔/null、`|` 与 `>` 块标量（缩进按最小缩进合并）。

不支持的语法：锚点/别名（`&`/`*`）、多文档（`---` 分隔的多个 doc）、复杂流式嵌套。
遇到不支持语法应安装 PyYAML 或改写文件；`loads` 会抛 `YamlError`，CLI 转成退出码 2 而不是 traceback。

一致性由 `tests/test_yamlmini.py` 保证：同一批 fixture 分别用两种解析器解析，断言结果深度相等。

## 8. 版本与打包

```
SKILL.md.version  ──bump──▶  manifest.json / README.md / docs/*.md / CHANGELOG.md
                          └─▶ dist/deep-research-plus-v<ver>.zip
                              dist/SHA256SUMS.txt
                              dist/release-notes-v<ver>.md
```

- **递增判定**：读 `CHANGELOG.md` 的 `[Unreleased]` 条目；含 `BREAKING`/不兼容 → major；含 `feat`/`新增`/`增加`/`支持` → minor；有其它条目 → patch；空 → 不递增。
- **同步范围**：`README.md`、`docs/*.md` 中的 `版本：x.y.z` 与 `更新：YYYY-MM-DD`。
- **CHANGELOG 重写**：保留空的 `[Unreleased]` 段，新增 `[x.y.z] - 日期` 段，正文取原 Unreleased 条目。
- **zip 确定性**：文件按路径排序，固定时间戳 `1980-01-01`，deflate level 9，权限 644；同名产物可比对 sha256。
- **BUILD-MANIFEST.json**：打包瞬间记录每个文件的 sha256 与字节数，位于 zip 根，不写入源目录，避免自我引用。
- **两份清单的分工**：`manifest.json` 的 `files` 是**人工维护的核心文件清单**（问答「这个包由哪些关键文件构成」）；`BUILD-MANIFEST.json` 是**构建时全量快照**（回答「这个 zip 里到底有什么、有没有被改过」）。两者语义不同，不要互相替代；校验器只强制前者登记的文件存在、版本与 SKILL.md 一致。

## 9. 测试策略

| 层 | 文件 | 覆盖 |
|----|------|------|
| 单元 | `test_yamlmini.py` | 与 PyYAML 等值；块标量、行内集合、引号、注释 |
| 契约 | `test_frontmatter.py` | frontmatter 解析、非法版本、缺字段 |
| 规则 | `test_rules.py` | 六类 handler 的正反例；未知 type 报 CHK-000 |
| 闸门 | `test_gates.py` | 每个 stage 的通过/失败路径，逐条错误码断言 |
| 端到端 | `test_pipeline.py` | init → outline → confirm → results → review → report → gate 全链路 |
| 发布 | `test_package.py` | bump 三级、文档同步、zip 内容、SHA256、release notes |
| 真机 | 手工 + `selfcheck` | 安装到真实 skills 目录后跑 detect/validate/全链路 |

运行：

```bash
python -m pytest tests -q
python scripts/drp.py selfcheck
```

负路径必须覆盖：http 链接、缺日期、裸域名、无反方条目、评审超 2 轮、证据 id 不存在、报告缺章、尾注未定义、AI 腔命中、来源数不足、反方缺官方源、占位链接、开页留痕缺失。

两套 fixture 的定位不同：`tests/fixtures/pass` 用于源码仓库的单元与端到端回归；`checklists/fixtures/pass` 是精简版，随 zip 发布，供 `selfcheck` 在任何安装形态下跑满流水线。两者只保证闸门形态合规，**不保证链接真实可达**——加 `--check-links` 跑它们会报 G-RES-020，属预期。

## 10. 已知限制

1. 不做 URL 存活检测（要求离线可跑）。链接失效靠反方评审人工开页发现。
2. `yamlmini` 不支持锚点/多文档，复杂 YAML 需装 PyYAML。
3. 文件时间戳统一为 1980-01-01，zip 内文件时间不反映真实构建时间（换确定性）。
4. 写命令（report / bump / package）有目录锁，但 agent 自己改 `results/*.yaml` 不走工具，锁管不到；同一 `{topic_slug}` 仍应一个进程处理。
5. `report` 渲染是确定性模板，不负责改写文风；去 AI 腔靠 `gate` 拦 + 人改。
6. 轻量档不产 `report.md`，因此 `gate --stage report` 对轻量档不适用（见闸门矩阵）。

## 11. 扩展指南

**加一条文本规则**：清单里加条目 → 用已有 type；缺 type 就实现 handler 并注册。改完 `validate` + `selfcheck` 双跑。

**加一个闸门阶段**：写 `gate_xxx(workspace, strict)` → 注册进 `GATES` → 更新 SKILL.md 的闸门矩阵（CHK-001 会检查表里是否有三档行）→ 补测试。

**加一个 findings 字段**：先改渲染与 gate 两侧（渲染取 `value`，gate 校验必填），再改本文档 §3.3，最后补测试，避免文档与实现漂移。

## 12. 发布检查单（人工）

1. `python scripts/drp.py selfcheck` 全 PASS
2. `python -m pytest tests -q` 全通过
3. `python scripts/drp.py package` 自动递增并出包
4. 解压到临时目录，`validate` + `version` 复核
5. 上传源码与 `dist/` 三件套到 Release，正文用 `release-notes-v<版本>.md`

CI 等价路径：提交信息带 `[release]` 推到 main，`.github/workflows/release.yml` 会依次跑 pytest → validate → selfcheck → package，再以 `v<版本>` 建或更新 Release；不带标记时 job 被 `if` 跳过，属预期。
