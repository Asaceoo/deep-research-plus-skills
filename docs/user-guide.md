# 用户手册

> 版本：1.6.2 ｜ 更新：2026-10-26 ｜ 适用技能：deep-research-plus

## 1. 这个技能替你做什么

一句话：**把"深度调研"从一次性搜索，变成有交付标准的小流程**。

- 先分档。查一个版本号不该跑六阶段流水线，做行业选型也不该只搜一次。
- 逼着大纲里放反方条目。只收正面证据的大纲，结论一定是偏的。
- 每条结论必须能回指到「完整链接 + 日期 + 来源类型」，且来源数量有下限。
- 决策级结论如果只有单源或只有社区内容支撑，会被强制打标记。
- 用脚本闸门卡住"先写报告再补证据"，并在报告里自动留痕。

它不做的事：

- 不判断哪个方案更好，只保证判断所依据的证据站得住。
- 不保证抓到付费墙后的内容；抓不到会标 `summary-level`，不会编一段。
- **不验证「链接真但内容不支撑」**——这需要读页面语义。它只强制你把核对过程写进 `spot_checks`，让"没核对"变得可见。
- 不复制子技能正文；缺子技能就降级，流程不变。

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
unzip deep-research-plus-v1.6.1.zip -d ~/.workbuddy/skills/deep-research-plus
python ~/.workbuddy/skills/deep-research-plus/scripts/drp.py validate
```

`validate` 输出 `PASS` 说明包装好了；`FAIL` 会逐条给错误码，对照 §10 处理。

脚本需要 Python 3.8+，零第三方依赖。**没有 Python 也能用**，只是五道闸门退化为人工复核，报告头会标 `manual-gate`。

## 3. 五分钟上手

对话里直接说：

> 深度调研一下 2026 年主流开源 TTS 方案，帮我选型。

技能接手后的动作：

1. 判话题类型与档位（light / standard / deep），并说明判据。
2. 生成 4-8 个条目，其中 1 个是反方条目（"已知缺陷与社区吐槽"）。
3. 停下来问你：条目够不够、字段要不要加、档位要不要调。**这一步必须你点头**，点头后它才把 `confirmed: true` 落盘。
4. 逐项搜索，官方文档/源码优先，每项落 `results/item_N.yaml`。
5. 反方评审：挑 3-4 条承重结论开页核对，把结果写进 `review.yaml` 的 `spot_checks`。
6. 输出六章报告，每条结论带尾注链接。

手工起工作区：

```bash
python scripts/drp.py init --workspace ./tts --topic "2026 主流开源 TTS 方案"
# 编辑 ./tts/outline.yaml 补条目，保留 1 个 kind: counter
python scripts/drp.py gate --workspace ./tts --stage outline
```

## 4. 五个场景

### 4.1 技术选型（standard / deep）

> 对比 A、B、C 三个开源向量库，我要决定生产用哪个。

每个候选都要有"已知缺陷"证据；反方条目的 findings 写 `polarity: negative`，且至少一条来自官方文档或仓库 issue。最终结论若只有官方 benchmark 支撑，会被要求标注"官方口径，未见第三方复现"。

### 4.2 行业/市场调研（deep）

> 调研国内免漆门行业的渠道结构。

定量数据必须带口径。查不到的产能/份额标 `partial` 进「未覆盖」，不允许用"约""大概"填坑。渠道分层（工程 / 家装 / 电商 / 出口）每一层都要有独立来源。

### 4.3 舆情/社区洞察（standard）

> 看看 B 站和小红书上对某款剪辑软件的真实评价。

社区源天然多噪声。决策级结论若只有 UGC 支撑会被打 `high-risk`，正式场合不采信；补一条官方口径交叉验证才算过关。

### 4.4 单点事实核查（light）

> 帮我查一下 X 的最新版本号。

1-3 个条目，直接搜，口头确认，不派子代理，不产出 `report.md`。**不要为了用技能而跑全流程。**

### 4.5 中断续跑

> 继续 tts-comparison 的调研。

看 `results/` 里已有的 `item_N.yaml`，只补缺失项。若上次异常退出留下 `.drp-lock`，30 分钟后自动过期；急用可加 `--no-lock`。

## 5. 读懂输出

### 5.1 报告六章

| 章节 | 你该看什么 |
|------|-----------|
| 1 核心结论（TL;DR） | 决策点，每条都有尾注编号 |
| 2 对比总表 | 横评速览，首行写明数据截点 |
| 3 逐项详析 | 每条证据的来源类型与日期 |
| 4 冲突与存疑 | **最该看的一章**：多源矛盾、无证据降级项 |
| 5 未覆盖与限制 | 2 轮评审后仍没查到的 |
| 6 来源清单 | 按来源类型分组，完整 https 链接 + 日期 |

### 5.2 标记含义

| 标记 | 含义 | 怎么用 |
|------|------|--------|
| `single-source` | 只有 1 个来源支撑 | 可以引用，但别当定论 |
| `high-risk` | 决策级结论只靠社区/UGC | 正式场合不采信 |
| `partial` | 数据缺失，只有部分口径 | 引用时必须说明缺什么 |
| `summary-level` | 只有搜索摘要，未核原文 | 重要结论要补开原文 |
| `manual-gate` | 平台无命令执行能力，闸门人工过 | 报告可信度打折，需自查 |
| 官方口径 | 数字来自当事方自述 | 标注"未见第三方复现" |

## 6. 证据怎么算"够"

这一节是 v1.5 之后最容易踩的地方，闸门会逐条查。

| 要求 | 规则 | 违反时的码 |
|------|------|-----------|
| 来源数量 | 每项独立 URL ≥ 档位基数（light 1 / standard 2 / deep 3），反方条目再 +1 | G-RES-017 |
| 反方源类型 | 反方条目至少 1 条 `official` 或 `code`，不许只贴吐槽 | G-RES-018 |
| 链接形态 | 必须是完整 `https://`；`example.com` / `placeholder` / `does-not-exist` 直接判可疑 | G-RES-012 / 019 |
| 日期 | `YYYY-MM-DD`，不得晚于今天 | G-RES-013 / 014 |
| 来源类型 | `official` / `code` / `secondary` / `community` / `journalism` 之一 | G-RES-015 |
| 字段覆盖 | outline 里声明的字段必须被 finding 命中 | G-RES-016 |
| 开页留痕 | 决策级结论必须有 `spot_checks` 记录 | G-REV-013 |

确有理由放宽来源数时，在 `outline.yaml` 的对应 item 写 `min_sources: 1` 并说明，而不是删证据。

### 6.1 `spot_checks` 怎么填

```yaml
spot_checks:
  - decision_id: d1
    url: https://milvus.io/docs/overview.md   # 必须是该结论证据里的 URL
    verdict: supports                          # supports | contradicts | blocked
    note: 页面第 2 节明确写 Apache-2.0
```

- `supports`：页面内容确实支撑结论
- `contradicts`：页面反驳了结论 → 该结论必须移进「冲突与存疑」，不能留在 TL;DR
- `blocked`：付费墙/反爬打不开 → 结论降级为 `summary-level` 并在「未覆盖」写明

### 6.2 什么时候开 `--check-links`

```bash
python scripts/drp.py gate --workspace ./tts --stage results --check-links
```

只在**交稿前最后一遍**开：它逐个 HEAD 请求，慢且受网络影响。403/429 会被判"反爬不可判"而不是失败，但超时会让整批结果不可达——离线环境不要开。

## 7. 命令速查

```bash
D=~/.workbuddy/skills/deep-research-plus/scripts/drp.py

python $D validate                       # 包自检
python $D detect                         # 子技能探测 + 降级方案
python $D init --workspace ./ws --topic "话题"
python $D gate --workspace ./ws --stage outline|confirm|results|review|report
python $D gate --workspace ./ws --stage results --check-links   # 可选：联网核验链接
python $D report --workspace ./ws        # 渲染六章报告
python $D bump --level auto              # 版本递增 + 文档同步
python $D package                        # 两段校验 + 递增 + 出包
python $D selfcheck                      # 清单兜底 + 流水线回归
python $D version                        # 当前版本
```

任意子命令后加 `--json` 拿机器可读输出。写命令（`report` / `bump` / `package`）会加目录锁，`--no-lock` 可跳过。

## 8. 降级矩阵

| 你的环境 | 会怎样 |
|----------|--------|
| 有搜索 + 有抓取 + 有子代理 | 全功能：并行深调，引用可核原文 |
| 有搜索 + 无抓取 | 引用标 `summary-level`，结论保守 |
| 有搜索 + 无子代理 | 串行深调，每项先写小结再搜下一项 |
| 无文件写入 | 报告分段输出在对话，outline 用对话消息承载 |
| 无命令执行 | 闸门人工复核，报告头标 `manual-gate` |
| 无搜索 | 无法执行，技能会直接告诉你 |

## 9. 常见故障

| 症状 | 原因 | 处理 |
|------|------|------|
| 报 G-OUT-012 | 没有反方条目 | 加一个 `kind: counter` 的条目 |
| 报 G-OUT-014 / 015 | 档位与条目数不匹配 | 改 `tier` 或增删条目 |
| 报 G-CON-001 | 用户没确认就开跑 | 确认后补 `confirmed: true` |
| 报 G-RES-012 | 用了 http 或裸域名 | 换完整 `https://` 链接 |
| 报 G-RES-013 | 日期写成"上周""2026年10月" | 改 `YYYY-MM-DD` |
| 报 G-RES-016 | 声明过的字段没有证据覆盖 | 补该字段的 finding，或从 outline 删掉这个字段 |
| 报 G-RES-017 | 来源数不到下限 | 补第二个独立来源；确有理由写 `min_sources` |
| 报 G-RES-018 | 反方条目只有社区源 | 补一条官方文档或仓库 issue |
| 报 G-RES-019 | 用了占位域名/示例链接 | 换真实可访问链接 |
| 报 G-RES-020 / 021 | `--check-links` 探到死链或不可达 | 换链接；网络受限就关掉该开关 |
| 报 G-REV-008 / 009 | 单源或社区源结论没标 | 加 `flags: [single-source]` / `[high-risk]` |
| 报 G-REV-013 | 决策级结论没记录开页核对 | 在 `review.yaml` 补 `spot_checks` |
| 报 G-REV-003 | 评审补搜超过 2 轮 | 停下，把没查到的写进 `uncovered` |
| 报 G-REP-010 / 011 | 报告缺数据截点或来源未分组 | 重跑 `drp.py report` |
| 报 MAN-001 | `manifest.json` 版本和 `SKILL.md` 不一致 | 跑一次 `drp.py bump --level patch` |
| 报 MAN-003 | manifest 登记的某个文件不存在 | 补文件或从 `manifest.files` 移除 |
| 报「目录被占用」 | 另一个进程正在对同一目录做写操作 | 等它跑完；确认无并发后删 `.drp-lock`，或加 `--no-lock` |
| Windows 控制台中文乱码 | 终端编码非 UTF-8 | 脚本已强制 UTF-8 输出；仍有乱码时 `chcp 65001` |
| `YAML 解析失败` | 用了锚点/多文档等内置解析不支持的语法 | 装 PyYAML，或改写成基础结构 |

## 10. 产物与清理

调研产物在 `{topic_slug}/` 下：`outline.yaml`、`fields.yaml`、`results/`、`review.yaml`、`report.md`。
技能包产物在 `dist/` 下：zip、`SHA256SUMS.txt`、`release-notes-*.md`。`dist/` 不入库。

## 11. 升级

```bash
python scripts/drp.py version      # 看当前版本
# 解压新包覆盖（调研工作区不在技能目录里，不会被覆盖）
python scripts/drp.py validate
python scripts/drp.py selfcheck    # 清单 + 内置流水线回归
```

版本规则：新增能力升 minor，修缺陷升 patch，破坏兼容升 major。文档版本号由 `bump` 自动同步，不需要手改。
