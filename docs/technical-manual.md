# 技术手册

> 版本：1.6.2 ｜ 更新：2026-10-26 ｜ 适用技能：deep-research-plus

## 1. 设计目标与不变量

| # | 不变量 | 落地方式 |
|---|--------|----------|
| I1 | 版本号只有一个事实源 | `SKILL.md` frontmatter `version`；`bump` 推导并回写其余文件 |
| I2 | 闸门可执行，不靠自觉 | 每阶段一个 `gate --stage`，退出码 0/1/2 |
| I3 | 规则不得静默失效 | 清单出现未知规则类型 → 直接 P1，不跳过 |
| I4 | 结构性错误不依赖清单 | manifest 版本/名称/文件存在由基础校验 MAN-001..003 负责，清单被裁剪也照样拦 |
| I5 | 失败不留残局 | `package` 先校验再递增；递增后校验失败用快照回滚 |
| I6 | 引用可回指 | 结论绑定 finding id；finding 带 https + 日期 + 类型 + 来源数下限 |
| I7 | 零第三方硬依赖 | 全部 stdlib；PyYAML 只是加速路径 |
| I8 | 产物可校验 | zip 内 `BUILD-MANIFEST.json` 逐文件 sha256；外层 `SHA256SUMS.txt` |
| I9 | 常驻上下文受控 | `SKILL.md` ≤19KB（CHK-010），细节进 `references/`、`docs/` |

## 2. 架构

```
SKILL.md                 技能入口：能力矩阵、机器契约、六阶段、闸门矩阵、反例黑名单
checklists/
  skill_audit.yaml       十条机器规则（文本层约束）
  fixtures/pass/         随包发布的精简 fixture（selfcheck 用）
references/
  report-template.md     Phase 4 六章模板与硬性规则
  usage-examples.md      四类话题完整执行示例
scripts/
  drp.py                 单文件工具层
    ├── YAML 层          PyYAML 优先 / yamlmini 子集兜底
    ├── 基础校验层        frontmatter / 结构 / 路径 / 版本 / 许可 / manifest 一致性
    ├── 规则引擎层        清单规则按 type 分发，未知类型报 CHK-000
    ├── 闸门层           outline / confirm / results / review / report
    ├── 并发层           WorkspaceLock（report / bump / package）
    ├── 渲染层           六章 + 尾注编号 + 数据截点 + 来源分组
    └── 发布层           bump / package（两段校验 + 快照回滚）/ selfcheck
docs/                    用户手册 · 技术手册 · 对抗性审查记录 · 概念图
tests/                   单元 / 契约 / 端到端 / 负路径 / 并发
```

分层原则：`SKILL.md` 面向模型，`checklists` 面向文本约束，`scripts` 面向可判定事实。三者不互相复制，避免改一处漏三处。

## 3. 数据契约

### 3.1 outline.yaml

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `topic` / `slug` | str | 是 | 话题原文 / 产物目录名 |
| `tier` | enum | 是 | `light` / `standard` / `deep` |
| `type` | enum | 是 | `tech` / `market` / `community` / `mixed` |
| `confirmed` | bool | Phase 2 起 | 必须 `true` 才放行 |
| `confirmed_at` | str | Phase 2 起 | `YYYY-MM-DD`，不得晚于今天 |
| `confirmed_by` | str | Phase 2 起 | 谁确认的 |
| `items[]` | list | 是 | 非空；id 唯一；title 唯一 |
| `items[].kind` | enum | 否 | `normal`（默认）/ `counter` |
| `items[].fields` | list[str] | 否 | 必须在 fields.yaml 定义 |
| `items[].min_sources` | int | 否 | 覆盖默认来源数下限 |
| `items[].status` | enum | 否 | `pending` / `done` / `partial` |

档位与条目数：`light` 1-3，`standard` 4-8，`deep` ≥9。

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
| `findings[].value` | str | 关键数值/事实 |
| `findings[].field` | str | 关联 fields.yaml，用于字段覆盖 |
| `findings[].source_url` | str | `https://` 开头，且不得命中占位特征 |
| `findings[].source_type` | enum | `official` / `code` / `secondary` / `community` / `journalism` |
| `findings[].date` | str | `YYYY-MM-DD`，不晚于今天 |
| `findings[].polarity` | enum | `positive` / `negative` / `neutral` |
| `uncertainties[]` | list[str] | 反方条目的兜底证据 |

来源数下限：`DEFAULT_MIN_SOURCES = {light:1, standard:2, deep:3}`，`kind: counter` 再 +1。

### 3.4 review.yaml

| 字段 | 类型 | 约束 |
|------|------|------|
| `rounds` | int | 1-2；>2 判 P0 |
| `capabilities` | str | 写入报告头 |
| `decisions[].id` / `.claim` | str | claim 不得命中 AI 腔黑名单 |
| `decisions[].level` | enum | `decision` / `supporting` |
| `decisions[].evidence` | list[str] | 必须全部命中 findings id |
| `decisions[].flags` | list[str] | `single-source` / `high-risk`，闸门强校验 |
| `spot_checks[].decision_id` | str | 决策级必须覆盖（G-REV-013） |
| `spot_checks[].url` | str | 必须在该决策证据的 URL 集合内（G-REV-014） |
| `spot_checks[].verdict` | enum | `supports` / `contradicts` / `blocked`（G-REV-015） |
| `spot_checks[].note` | str | 开页看到什么，一句话 |
| `conflicts[]` / `uncovered[]` / `corrections[]` | list[str] | 进报告第 4/5 章与评审记录 |

### 3.5 report.md

六章固定：核心结论 / 对比总表 / 逐项详析 / 冲突与存疑 / 未覆盖与限制 / 来源清单。
首部元信息四项：调研日期 / 分档 / 能力组合 / 评审状态。
尾注必须在来源清单定义：`[^id]: <https://…> ｜ YYYY-MM-DD ｜ type`，且按 `source_type` 分组。

## 4. 闸门实现

| stage | 入口 | 主要检查 | 码段 |
|-------|------|----------|------|
| outline | `gate_outline` | 字段齐全、id/标题唯一、反方条目、档位条目数、字段引用 | G-OUT-00x |
| confirm | `gate_confirm` | `confirmed=true`、日期合法非未来、确认人非空 | G-CON-00x |
| results | `gate_results` | 文件对应、finding 必填、https、日期、类型、反方证据、字段覆盖、来源数、占位链接、（可选）链接探测 | G-RES-00x |
| review | `gate_review` | 轮次 ≤2、决策非空、证据命中、单源/社区源标记、开页留痕、AI 腔 | G-REV-00x |
| report | `gate_report` | 六章、元信息、尾注可解析、裸域名、AI 腔、TL;DR 数量、数据截点、来源分组 | G-REP-00x |

### 4.1 严重级语义

| 级别 | 含义 | 打包时 |
|------|------|--------|
| P0 | 契约破坏，继续跑必然产出错误结果 | 阻断 |
| P1 | 规范违背，可信度受损 | 阻断 |
| P2 | 覆盖度提示 / 风格约束 | 记 warnings，不阻断（`--strict` 下升级） |

### 4.2 关键判定逻辑

- **单源**：`decisions[].evidence` 推出的 URL 去重集合大小为 1 → 必须含 `single-source`。
- **高风险**：证据 `source_type` 集合 ⊆ {community, secondary} 且 level=decision → 必须含 `high-risk`。
- **来源覆盖率**：每个 item 的独立 URL 数 ≥ 档位基数（+1 if counter），可用 `min_sources` 覆盖。
- **反方源类型**：`kind: counter` 至少 1 条 `official` 或 `code`。
- **占位链接**：URL 命中 `example.com` / `placeholder` / `does-not-exist` / `localhost` 等特征直接判 G-RES-019，不联网。
- **链接核验**：`--check-links` 才走 HEAD；`_classify_status` 把 2xx/3xx 判 ok、401/403/405/429 判 blocked（不失败）、404/410 判 gone（G-RES-020）、其余与网络异常判 unreachable（G-RES-021）。
- **开页留痕**：决策级结论必须有一条 `spot_checks`，且 url 落在该结论证据内。
- **复核轮次**：`rounds > 2` 直接失败——无限补搜是流程失控信号。

### 4.3 并发锁

`WorkspaceLock` 用 `O_CREAT | O_EXCL` 创建 `.drp-lock`（JSON：pid / command / started_at），无 TOCTOU 窗口。

- 作用对象：`report`（锁 workspace）、`bump` / `package`（锁 skill_dir）；`gate` 只读不加锁。
- 过期接管：锁文件 mtime 超过 30 分钟视为陈旧，覆盖并打印 `[WARN] 接管过期锁`。
- 释放：`__exit__` 只在 pid 匹配时删除，异常路径同样释放。
- 逃生口：`--no-lock`。
- 边界：agent 直接改 `results/*.yaml` 不走工具，锁管不到。

## 5. 基础校验（不依赖清单）

| 码 | 检查 |
|----|------|
| FM-002..005 | frontmatter 缺字段 / 版本非语义化 / name 与目录不一致 / 缺 Triggers |
| SEC-001..003 | 缺必需章节（能力需求/流水线/反例黑名单/使用示例）/ 缺阶段 / 缺硬停标记 |
| PATH-001 / 003 / 004 | 引用路径不存在 / 虚假捆绑声明 / 疑似笔误（首段与顶层目录相似度 ≥0.8） |
| DOC-001 / 002 | 文档缺版本头 / 文档版本与 SKILL 不一致 |
| LIC-001 | 声明 license 但缺 LICENSE |
| MAN-001 | manifest.version 与 SKILL.version 不一致（P0） |
| MAN-002 | manifest.name 与目录名不一致（P1） |
| MAN-003 | manifest.files 登记的文件不存在（P0） |

路径校验只对「首段命中包内顶层条目」的 token 生效；`{slug}/report.md`、`results/` 这类调研产物路径不参与，代码块内的示例也不参与。

## 6. 规则引擎

清单每条规则是 `{id, type, severity, params}`，按 type 分发：

| type | 作用 | 关键参数 |
|------|------|----------|
| `gate_matrix` | 档位×闸门矩阵表存在 | 无 |
| `conflict_pairs` | 两组正则不得同时出现 | `pairs` |
| `forbidden_patterns` | 禁用语扫描 | `patterns`、`ignore_in_sections` |
| `required_patterns` | 必需内容扫描 | `patterns`、`hint` |
| `claim_requires_dir` | "已捆绑"声明必须目录真实存在 | `claims[]` |
| `manifest_files_exist` | manifest 键齐全 + 文件存在（现由 MAN-003 兜底，规则保留兼容） | `required_keys` |
| `test_prompts_present` | 消费者回归用例存在且含 anomaly | `path`、`min_prompts`、`min_anomaly` |
| `commands_exist` | SKILL.md 的 `drp.py <子命令>` / `--stage <阶段>` 必须真实存在 | 无 |
| `max_bytes` | 文件体积上限 | `path`、`max_bytes` |

**未注册的 type 产出 `CHK-000` P1**——清单写错字不能导致"检查通过"。

## 7. 错误码总表

| 段 | 覆盖 | 处理方向 |
|----|------|----------|
| FM / SEC / PATH / DOC / LIC / MAN | 见 §5 | 修包自身 |
| CHK-001..010 | 清单规则命中 | 按 detail 修 SKILL.md 或补文件 |
| G-OUT-001..018 | 大纲问题 | 补条目/字段/反方条目 |
| G-CON-001..005 | 未确认/日期非法/确认人缺失 | 补 confirmed 三件套 |
| G-RES-001..021 | 证据缺失 / 非 https / 日期非法 / 类型非法 / 字段缺证 / 来源数不足 / 反方缺官方源 / 占位链接 / 死链 | 补证据或换来源 |
| G-REV-001..015 | 评审缺失 / 轮次超限 / 证据未绑定 / 未标标记 / 开页留痕缺失 | 补 review.yaml |
| G-REP-001..011 | 缺章 / 尾注未定义 / 裸域名 / AI 腔 / 缺数据截点 / 来源未分组 | 重跑 `report` |

## 8. YAML 解析层

策略：`import yaml` 成功则用 PyYAML（自定义 loader 把 timestamp 保持为字符串，与内置解析对齐）；失败回退 `yamlmini.loads()`。

支持子集：注释、嵌套映射、`- ` 序列（含 `- key: value` 起头的映射项）、行内 `[a, b]` / `{k: v}`、单双引号、整数/浮点/布尔/null、`|` 与 `>` 块标量。
不支持：锚点/别名、多文档、复杂流式嵌套。遇到不支持语法抛 `YamlError`，CLI 转成退出码 2 而不是 traceback。

一致性由 `tests/test_yamlmini.py` 保证：同一批 fixture 双解析器深度相等。

## 9. 版本与打包

```
SKILL.md.version ──bump──▶ manifest.json / README.md / docs/*.md / CHANGELOG.md
                          └─▶ dist/deep-research-plus-v<ver>.zip
                              dist/SHA256SUMS.txt
                              dist/release-notes-v<ver>.md
```

- **递增判定**：读 `CHANGELOG.md` 的 `[Unreleased]`；含 `BREAKING`/不兼容 → major；含 `feat`/`新增`/`增加`/`支持` → minor；有其它条目 → patch；空 → 不递增。
  ⚠️ 措辞直接决定版本号：写「新增」就是 minor，哪怕改的只是锁。
- **两段校验**：递增前先用 `_pack_issues(skip=DOC-001/002, MAN-001)` 校验（这几类 bump 会顺手修好）；递增后再全量校验，失败则用 `_snapshot` / `_restore` 回滚 SKILL/manifest/CHANGELOG/README/docs，版本回到递增前。
- **zip 确定性**：路径排序、固定时间戳 1980-01-01、deflate 9、权限 644。
- **两份清单分工**：`manifest.json#files` 是人工维护的核心清单；`BUILD-MANIFEST.json` 是构建时全量快照（含 sha256 与字节数）。语义不同，不互相替代。

## 10. 测试策略

| 层 | 文件 | 覆盖 |
|----|------|------|
| YAML | `test_yamlmini.py` | 双解析器等值、块标量、行内集合、异常缩进 |
| 契约 | `test_frontmatter.py` | frontmatter、路径与笔误、文档版本、manifest 一致性 |
| 规则 | `test_rules.py` | 各类 handler 正反例、未知 type、体积与命令真实性 |
| 闸门 | `test_gates.py` | 五道闸门逐条错误码，含来源数与开页留痕 |
| 并发 | `test_lock.py` | 阻塞、过期接管、异常释放、禁用、CLI 逃生口 |
| 端到端 | `test_pipeline.py` | init → 五闸门 → report；fixture 回落；selfcheck |
| 发布 | `test_package.py` | 递增三级、文档同步、预校验阻断、回滚、zip 确定性 |

负路径必须覆盖：http 链接、裸域名、缺日期、类型非法、无反方条目、反方缺官方源、来源数不足、占位链接、评审超轮次、证据 id 不存在、开页留痕缺失、报告缺章、尾注未定义、AI 腔、打包失败回滚。

两套 fixture 定位不同：`tests/fixtures/pass` 供源码仓库回归；`checklists/fixtures/pass` 精简版随 zip 发布，供 `selfcheck` 在任何安装形态跑满流水线。两者只保证闸门形态合规，**不保证链接真实可达**——加 `--check-links` 跑它们必然报 G-RES-020，属预期。

## 11. 已知限制

1. 不做 URL 存活检测（除非显式 `--check-links`），死链靠评审开页发现。
2. 无法验证「链接真但内容不支撑」，只能靠 `spot_checks` 留痕。
3. `yamlmini` 不支持锚点/多文档。
4. zip 内文件时间统一 1980-01-01，不反映构建时间（换确定性）。
5. 写命令有锁，但 agent 直接改 `results/*.yaml` 不走工具，锁管不到。
6. `report` 是确定性模板，不负责改写文风；去 AI 腔靠 `gate` 拦 + 人改。
7. 轻量档不产 `report.md`，`gate --stage report` 对其不适用（见闸门矩阵）。

## 12. 扩展指南

**加一条文本规则**：清单加条目 → 用已有 type；缺 type 就实现 handler 并注册进 `RULE_HANDLERS`。改完 `validate` + `selfcheck` 双跑。

**加一个闸门阶段**：写 `gate_xxx(workspace, strict, check_links=False)` → 注册进 `GATES` → 更新 SKILL.md 的闸门矩阵（CHK-001 检查三档行）→ 补测试。

**加一个 findings 字段**：先改渲染与 gate 两侧，再改 §3.3，最后补测试，避免文档与实现漂移。

**改版本行为**：任何触碰 `apply_version` 的改动都要同时跑 `test_package.py` 的回滚用例。

## 13. 发布检查单

1. `python -m pytest tests -q` 全通过
2. `python scripts/drp.py validate` → 0 error
3. `python scripts/drp.py selfcheck` → 全 PASS
4. `python scripts/drp.py package`（先校验、再递增、再出包；失败会自动回滚）
5. 解压到临时目录，`validate` + `version` 复核
6. 上传源码与 `dist/` 三件套到 Release，正文用 `release-notes-v<版本>.md`

CI 等价路径：提交信息带 `[release]` 推到 main，`.github/workflows/release.yml` 依次跑 pytest → validate → selfcheck → package，再以 `v<版本>` 建或更新 Release；不带标记时 job 被 `if` 跳过，属预期。
