# Changelog

本项目的所有显著变更记录于此。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循语义化版本。
`drp.py bump --level auto` 读取 `[Unreleased]` 段落判定递增级别：出现 BREAKING 判 major，出现 feat/新增 判 minor，其余判 patch。

## [Unreleased]

## [1.6.0] - 2026-10-26

- 加目录锁：`report` / `bump` / `package` 三个写命令对同一目录互斥，锁文件 `.drp-lock` 记录 pid 与命令，超 30 分钟视为过期自动接管，`--no-lock` 可跳过
- 清单加 CHK-010（`commands_exist`）：SKILL.md 里出现的 `drp.py <子命令>` 与 `--stage <阶段>` 必须真实存在，防止文档跑在实现前面
- `manifest.json` 补 `files_note`：写明它与 `BUILD-MANIFEST.json` 的分工——前者是人工维护的核心清单，后者是构建时全量快照
- README 补「发版」章节：`[release]` 提交约定、CI 流水线顺序、手动触发方式；技术手册 §12 同步
- 测试 112 → 121 条（新增锁的阻塞/接管/异常释放/禁用、命令真实性三例）

## [1.5.0] - 2026-10-26

- **来源覆盖率下限**：每个 item 的独立 URL 数必须 ≥ 档位基数（light 1 / standard 2 / deep 3）+ 反方条目 1，`min_sources` 可显式覆盖；只搜一次就落盘会被 G-RES-017 拦下
- **反方来源类型下限**：`kind: counter` 至少要有 1 条 `official` 或 `code` 来源，避免拿单条社区吐槽充当反证（G-RES-018）
- **开页留痕**：`review.yaml` 增 `spot_checks`（decision_id / url / verdict / note），决策级结论必须记录是否真的打开源页面核对过；缺记录判 G-REV-013，url 不在证据里判 G-REV-014，verdict 非法判 G-REV-015
- **可选链接核验**：`gate --stage results --check-links` 走 HEAD 探测，2xx/3xx 可达、401/403/405/429 视为反爬不可判、404/410 判 G-RES-020、网络层失败判 G-RES-021；默认关闭，离线路径零网络依赖
- **离线占位链接识别**：命中 `example.com` / `placeholder` / `does-not-exist` 等特征直接判 G-RES-019，不需要联网
- **报告渲染补齐两处契约**：对比总表自动写「数据截点」，来源清单按 `source_type` 分组；对应新增 G-REP-010 / G-REP-011（P2）
- 测试 100 → 112 条，补足来源覆盖率、反方来源类型、占位链接、状态分类、链接探测、开页留痕、渲染契约七类用例
- 两套 fixture 全部补到「每项 2 个来源、反方 3 个来源含官方源」并加 `spot_checks`，与新版闸门对齐

## [1.4.1] - 2026-10-26

- **字段覆盖缺失从 P2 升为 P1**：`outline` 里声明过的字段若没有任何 finding 覆盖，results 闸门直接失败。原实现只给警告，等于「说好要查的字段整块缺失仍能放行」，报告缺列却显示全绿
- **`validate` 补 manifest 一致性校验**：`manifest.version` 与 `SKILL.md` 版本不一致判 P0（MAN-001），包名与目录名不一致判 P1（MAN-002）。原实现只查键齐全与文件存在，版本漂移会发布出自相矛盾的包
- **自检不再随安装形态缩水**：发布 zip 不含 `tests/`，`selfcheck` 的流水线回归原本直接 SKIP（只跑 10 项）；改为回落到 `checklists/fixtures/pass` 的内置精简 fixture，任何安装形态都跑满 15 项
- 补 `test-prompts.json`：4 条消费者回归用例（2 条典型 + 2 条歧义，覆盖「不用确认直接给报告」与「只有一个源直接下结论」），配套清单规则 CHK-009 校验其存在性与 anomaly 覆盖

## [1.4.0] - 2026-10-26

### Added — 可执行闸门与可校验产物
- **新增 `scripts/drp.py` 工具层**：`validate` / `detect` / `init` / `gate` / `report` / `bump` / `package` / `selfcheck` 八个子命令，阶段推进由退出码（0/1/2）裁决，不再依赖模型自觉
- **新增五道阶段闸门**：outline（条目互斥 + 反方条目 + 档位条目数 + 字段引用）、confirm（`confirmed`/`confirmed_at`/`confirmed_by` 三件套）、results（https 链接 + 日期 + 来源类型 + 反方证据）、review（证据绑定 + 单源/高风险标记 + 轮次上限）、report（六章齐全 + 尾注可解析 + 无裸域名 + 无 AI 腔）
- **新增 `checklists/skill_audit.yaml`**：八条机器规则（闸门矩阵、自相矛盾对、软表述、虚假捆绑声明、manifest 完整性、机器契约入口、占位符、证据分级词汇）；**未知规则类型直接判 P1**，防止清单静默失效
- **新增 `manifest.json`**：登记包内文件，打包时逐项校验存在性
- **新增 `tests/` 92 条回归**：YAML 解析等值、frontmatter、规则引擎、五道闸门的通过与失败路径、端到端流水线、版本与打包确定性
- **新增 `docs/user-guide.md`、`docs/technical-manual.md`**：重写为面向 v1.4.0 的双手册，版本头由 `bump` 自动同步
- **新增 `docs/adversarial-review.md`**：三视角对抗审查记录，含真实命令输出与四轮收敛表
- **新增三张概念图**：流水线与闸门、证据绑定与放行判定、产物与发布链路
- **新增 `package` 确定性构建**：固定时间戳 + 路径排序的 zip、`SHA256SUMS.txt`、`BUILD-MANIFEST.json`（逐文件 sha256）、`release-notes-v<版本>.md`

### Fixed
- **修正 Phase 3.5「🛑 强制」与轻量档「允许跳过」的自相矛盾**：改为「闸门矩阵（按档位）」，逐档写明必跑项与允许省略项
- **修正复杂度分档边界重叠**（原 3 与 8 同时落在两档）：改为互斥区间，轻量 1-3 / 标准 4-8 / 深度 ≥9，并纳入 outline 闸门硬校验
- **修正能力矩阵自相矛盾**：原写「文件读取缺失 → 跳过子技能检测」，但检测方法本身依赖文件系统；改为「无法读文件系统 → 全降级模式」
- **修正引用纪律只有 `source_url` 没有格式约束**：升级为 https 完整链接 + `YYYY-MM-DD` + 五类 `source_type` 三要素强校验，杜绝裸域名与相对时间
- **修正「已捆绑 sub-skills」的表述边界**：该声明对源码仓库成立、对解压后的技能目录不成立；改为指针表 + `drp.py detect` 实测探测，并在 README 区分「完整安装」与「zip 安装」
- **修正 `gate` 单阶段文本模式恒返回 0** 的实现缺陷：退出码按阶段累计
- **修正内置 YAML 解析与 PyYAML 在块标量尾换行上的不一致**：按 clip 语义补齐，`|-` 不补
- **修正通配路径（如 `docs/*.md`）被误判为悬空引用**：命中 0 个文件才报错
- **修正路径误报**：调研产物路径（`{slug}/report.md`、`results/`）不再被当作包内文件校验，改为「首段命中包内条目才校验 + 相似度笔误探测」

### Changed
- 阶段闸门从「口头自觉」改为脚本硬校验；无命令执行能力的平台降级为人工复核，报告头标 `manual-gate`
- 反例黑名单从 R1-R6 扩充到 R1-R8，新增「评审补搜无上限」与「报告头缺元信息」
- `init` 脚手架从「2 条目 + standard 档」改为「4 条目（含 1 反方）+ standard 档」，保证新工作区能直接过 outline 闸门
- 文档命名对齐仓库既有约定：`docs/user-guide.md`、`docs/technical-manual.md`

### Verified
- `python -m pytest tests -q` → 92 passed
- `python scripts/drp.py validate` → 0 error / 0 warning（PyYAML 与 `-S` 零依赖双路径）
- `python scripts/drp.py selfcheck` → 14 项全 PASS
- 真机验证：安装到 `~/.workbuddy/skills/deep-research-plus` 后 `detect` 报 zero-degradation，五道闸门全链路退出码 0

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
