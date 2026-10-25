# 用户手册

> 版本：1.5.0 ｜ 更新：2026-10-26 ｜ 适用技能：deep-research-plus

## 1. 这个技能替你做什么

一句话：**把"深度调研"从一次性搜索变成有交付标准的小流程**。

它做的事：

- 先分档。查一个版本号不该跑六阶段流水线，做行业选型也不该只搜一次。
- 逼着大纲里放反方条目。只收正面证据的大纲，结论一定是偏的。
- 每条结论必须能回指到「完整链接 + 日期 + 来源类型」，回指不到就降级为存疑。
- 决策级结论如果只有单源或只有社区内容支撑，强制打标记，不允许悄悄混进 TL;DR。
- 用脚本闸门卡住"先写报告再补证据"这种倒做。

它不做的事：

- 不替你判断哪个方案更好。它只保证判断所依据的证据是站得住的。
- 不保证抓到付费墙后的内容。抓不到会标 `summary-level`，而不是编一段。
- 不复制子技能正文。缺子技能就降级，功能打折但流程不变。

## 2. 安装

技能包是一个 zip，解压到平台的 skills 目录即可。

| 平台 | 目录 |
|------|------|
| WorkBuddy | `~/.workbuddy/skills/deep-research-plus/` |
| Claude Code | `~/.claude/skills/deep-research-plus/` |
| Codex | `~/.codex/skills/deep-research-plus/` |
| OpenCode | `~/.config/opencode/skills/deep-research-plus/` |
| 项目内 | `<项目>/.skills/deep-research-plus/` 或 `<项目>/skills/deep-research-plus/` |

```bash
unzip deep-research-plus-v1.4.0.zip -d ~/.workbuddy/skills/deep-research-plus
python ~/.workbuddy/skills/deep-research-plus/scripts/drp.py validate
```

`validate` 输出 `PASS` 说明包装好了；`FAIL` 会逐条给错误码，对照技术手册 §6 处理。

脚本需要 Python 3.8+，零第三方依赖（有 PyYAML 会用，没有走内置解析）。**没有 Python 也能用**，只是所有闸门退化为人工复核。

## 3. 五分钟上手

在对话里直接说：

> 深度调研一下 2026 年主流开源 TTS 方案，帮我选型。

技能接手后的动作序列：

1. 判定话题类型 = 技术/选型，档位 = standard 或 deep，并告诉你为什么这么判。
2. 生成 6 个左右条目 + 字段，其中 1 个是反方条目（"已知缺陷与社区吐槽"）。
3. 停下来问你：条目够不够、字段要不要加、档位要不要调。**这一步必须你点头**。
4. 逐项搜索，官方文档/源码优先，结果逐项落盘。
5. 反方评审：挑 TL;DR 里 3-4 条承重结论，打开源页面核对内容是否真的支撑结论。
6. 输出六章报告，每条结论带尾注链接。

如果你装了脚本，也可以手工起一个工作区：

```bash
python scripts/drp.py init --workspace ./tts --topic "2026 主流开源 TTS 方案"
# 编辑 ./tts/outline.yaml，补满条目，保留 1 个 kind: counter
python scripts/drp.py gate --workspace ./tts --stage outline
```

## 4. 五个真实场景

### 4.1 技术选型（standard / deep）

> 对比 A、B、C 三个开源向量库，我要决定生产用哪个。

要点：每个候选都要有"已知缺陷"证据，而不是只列优点。反方条目不是走过场，它的 findings 要写 `polarity: negative`。最终结论如果只有官方 benchmark 支撑，会标"官方口径，未见第三方复现"。

### 4.2 行业/市场调研（deep）

> 调研国内免漆门行业的渠道结构。

要点：定量数据必须带口径。查不到的产能/份额标 `partial` 进「未覆盖」，不允许用"约""大概"填坑。

### 4.3 舆情/社区洞察（standard）

> 看看 B 站和小红书上对某款剪辑软件的真实评价。

要点：社区源天然多噪声。决策级结论若只有 UGC 支撑会被打 `high-risk`，正式场合不采信；补一条官方口径做交叉验证才算过关。

### 4.4 单点事实核查（light）

> 帮我查一下 X 的最新版本号。

要点：1-3 个条目，直接搜，口头确认，不派子代理，不产出 report.md，只在对话里答。**不要为了用技能而跑全流程。**

### 4.5 续跑（中断恢复）

调研跑到一半断了，重新开会话说：

> 继续 tts-comparison 的调研。

技能会看 `results/` 里已有的 `item_N.yaml`，只补缺失项，不重跑已完成的。

## 5. 读懂输出

### 5.1 报告六章

| 章节 | 你该看什么 |
|------|-----------|
| 1 核心结论（TL;DR） | 决策点，每条都有尾注编号 |
| 2 对比总表 | 横评速览，注意数据截点 |
| 3 逐项详析 | 每条证据的来源类型与日期 |
| 4 冲突与存疑 | **最该看的一章**：多源矛盾、无证据降级项 |
| 5 未覆盖与限制 | 2 轮评审后仍没查到的 |
| 6 来源清单 | 完整 https 链接 + 日期，可逐条点开 |

### 5.2 标记含义

| 标记 | 含义 | 怎么用 |
|------|------|--------|
| `single-source` | 只有 1 个来源支撑 | 可以引用，但别当定论 |
| `high-risk` | 决策级结论只靠社区/UGC | 正式场合不采信 |
| `partial` | 数据缺失，只有部分口径 | 引用时必须说明缺什么 |
| `summary-level` | 只有搜索摘要，未核原文 | 重要结论要补开原文 |
| `manual-gate` | 平台无命令执行能力，闸门人工过 | 报告可信度打折，需自查 |
| 官方口径 | 数字来自当事方自述 | 标注"未见第三方复现" |

## 6. 命令速查

```bash
D=~/.workbuddy/skills/deep-research-plus/scripts/drp.py

python $D validate                      # 包自检
python $D detect                        # 子技能探测 + 降级方案
python $D init --workspace ./ws --topic "话题"
python $D gate --workspace ./ws --stage outline|confirm|results|review|report
python $D gate --workspace ./ws --stage results --check-links   # 可选：联网核验链接死活
python $D report --workspace ./ws       # 渲染六章报告
python $D bump --level auto             # 版本递增 + 文档同步
python $D package                       # 出包（自动递增）
python $D selfcheck                     # 清单兜底 + 流水线回归
python $D version                       # 当前版本
```

JSON 输出：任意子命令后加 `--json`，便于接 CI 或其它 agent。

## 7. 降级矩阵

| 你的环境 | 会怎样 |
|----------|--------|
| 有搜索 + 有抓取 + 有子代理 | 全功能：并行深调，引用可核原文 |
| 有搜索 + 无抓取 | 引用标 `summary-level`，结论保守 |
| 有搜索 + 无子代理 | 串行深调，每项先写小结再搜下一项 |
| 无文件写入 | 报告分段输出在对话，outline 用对话消息承载 |
| 无命令执行 | 闸门人工复核，报告头标 `manual-gate` |
| 无搜索 | 无法执行，技能会直接告诉你 |

## 8. 常见故障

| 症状 | 原因 | 处理 |
|------|------|------|
| `gate --stage outline` 报 G-OUT-012 | 没有反方条目 | 加一个 `kind: counter` 的条目 |
| 报 G-OUT-014 / 015 | 档位与条目数不匹配 | 改 `tier` 或增删条目 |
| `gate --stage confirm` 报 G-CON-001 | 用户没确认就开跑 | 确认后补 `confirmed: true` |
| 报 G-RES-012 | 用了 http 或裸域名 | 换完整 `https://` 链接 |
| 报 G-RES-013 | 日期写成"上周""2026年10月" | 改 `YYYY-MM-DD` |
| 报 G-REV-008 | 单源结论没标 | 加 `flags: [single-source]` 或补第二个源 |
| 报 G-REV-003 | 评审补搜超过 2 轮 | 停下，把没查到的写进 `uncovered` |
| 报 G-RES-016 | outline 声明的字段没有任何证据覆盖（v1.4.1 起判失败） | 补该字段的 finding，或从 outline 删掉这个字段 |
| 报 G-RES-017 | 某个条目的来源数不到下限（light 1 / standard 2 / deep 3，反方 +1） | 补第二个独立来源；确有理由可在 outline 写 `min_sources` 并说明 |
| 报 G-RES-019 | 用了占位域名或示例链接 | 换成真实可访问链接 |
| 报 G-REV-013 | 决策级结论没记录「开页核对」 | 在 `review.yaml` 的 `spot_checks` 补一条 |
| 报 G-REP-010/011 | 报告缺数据截点或来源未分组 | 重跑 `drp.py report`（渲染器已自动带） |
| 报 MAN-001 | `manifest.json` 版本和 `SKILL.md` 不一致 | 跑一次 `drp.py bump --level patch` 同步 |
| `report` 后 gate 报 G-REP-005 | 尾注缺链接 | 检查 `review.yaml` 的 evidence id 是否存在 |
| Windows 控制台中文乱码 | 终端编码非 UTF-8 | 脚本已强制 UTF-8 输出；仍有乱码时 `chcp 65001` |
| `yaml 解析失败` | 用了锚点/多文档等内置解析不支持的语法 | 装 PyYAML，或改写成基础结构 |

## 9. 产物与清理

调研产物在 `{topic_slug}/` 下：`outline.yaml`、`fields.yaml`、`results/`、`review.yaml`、`report.md`。
技能包产物在 `dist/` 下：zip、`SHA256SUMS.txt`、`release-notes-*.md`。`dist/` 不入库。

## 10. 升级

```bash
python scripts/drp.py version      # 看当前版本
# 解压新包覆盖（保留你自己的调研工作区，它不在技能目录里）
python scripts/drp.py validate
```

版本号规则：新增功能升 minor，修 bug 升 patch，破坏兼容升 major。文档版本号由 `bump` 自动同步，不需要手改。
