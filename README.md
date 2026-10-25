# Deep Research Plus

> 版本：1.6.2 ｜ 更新：2026-10-26

![version](https://img.shields.io/badge/version-1.6.1-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![python](https://img.shields.io/badge/python-3.8%2B%20%7C%20%E9%9B%B6%E4%BE%9D%E8%B5%96-3776ab)

**带闸门的深度调研编排层。** 它不替你判断哪个方案更好，只保证判断所依据的证据站得住：没证据的结论进不了 TL;DR，只靠社区的结论会被打上 `high-risk`，单源支撑会被打上 `single-source`，声明过要查的字段缺证会被闸门直接拦下。

适用于 Claude Code / Codex / OpenCode / OpenClaw / WorkBuddy / Cursor / WPS AI 等任何能读 Markdown 的智能体。脚本层可选：没有命令执行能力时，五道闸门降级为人工复核，报告头标 `manual-gate`。

## 它解决什么问题

深度调研的失败模式很稳定，而且都是**流程问题**，不是模型能力问题：

| 失败模式 | 后果 | 拦截点 |
|----------|------|--------|
| 大纲只收正面证据 | 结论天然偏向首选方案 | `kind: counter` 反方条目（outline 闸门） |
| 每个条目只搜一次就落盘 | 结论薄得像摘要 | 来源数下限 G-RES-017 |
| 反方条目拿一条吐槽充数 | 伪反证 | 反方需 ≥1 条官方/代码源 G-RES-018 |
| 引用写裸域名、占位链接 | 无法回溯，等于没有引用 | 三要素 + 占位特征 G-RES-012/019 |
| 结论回指不到证据 | 观点冒充实证 | review 闸门 G-REV-006 |
| 单源/社区源当决策依据 | 谣言进正式文档 | `single-source` / `high-risk` 强制标记 |
| 说好要查的字段整块缺失 | 报告缺列却显示全绿 | 字段覆盖 G-RES-016 |
| 评审"开页核对"只写在文档里 | 走个过场 | `spot_checks` 留痕 G-REV-013 |
| 先写报告再补证据 | 结论倒逼证据 | 五道闸门按顺序放行 |

![流水线与五道闸门](docs/assets/pipeline.svg)

## 五道闸门

| 闸门 | 卡什么 | 判定 |
|------|--------|------|
| Phase 1 `outline` | 条目重叠、无反方条目、字段未定义、档位与条目数不匹配 | `gate --stage outline` 退出码 |
| Phase 2 `confirm` | 没确认就开跑（`confirmed` / `confirmed_at` / `confirmed_by` 缺一不放行） | `gate --stage confirm` |
| Phase 3 `results` | 链接形态、日期、来源类型、来源数下限、反方源类型、字段覆盖 | `gate --stage results` |
| Phase 3.5 `review` | 证据绑定、单源/高风险标记、开页留痕、补搜轮次上限 | `gate --stage review` |
| Phase 4 `report` | 六章齐全、尾注可解析、无裸域名、数据截点、来源分组、无 AI 腔 | `gate --stage report` |

![证据绑定与放行判定](docs/assets/degradation.svg)

## 它能拦什么，拦不住什么

**能拦**（机器可判）：链接不是 https、日期写"上周"、来源只有 1 个、反方只有吐槽、字段缺证、决策级结论没标单源、评审没记录开页、报告缺章、尾注断链、补搜超过 2 轮。

**拦不住**：链接真但内容不支撑该结论——这需要读页面语义，机器做不了。技能的对策是把它变成**可查的字段**：`review.yaml` 的 `spot_checks` 必须记录每条决策级结论「开了哪个页面、看到什么、支持还是反驳」。留痕不等于判定，真正的防线仍是 Phase 3.5 的质疑者视角。

可选开启 `--check-links` 联网 HEAD 探测死链（默认关闭，离线路径零网络依赖）：2xx/3xx 可达、401/403/405/429 视为反爬不可判、404/410 判死链。

## 安装

### 完整安装（推荐，克隆即零降级）

```bash
git clone https://github.com/Asaceoo/deep-research-plus-skills.git
cd deep-research-plus-skills

mkdir -p ~/.workbuddy/skills/deep-research-plus
cp -r SKILL.md manifest.json scripts checklists references docs ~/.workbuddy/skills/deep-research-plus/

# 四个子技能（版权归原作者，见 THIRD-PARTY-NOTICES.md）
cp -r sub-skills/deep-research      ~/.workbuddy/skills/
cp -r sub-skills/research           ~/.workbuddy/skills/
cp -r sub-skills/agent-reach        ~/.workbuddy/skills/
cp -r sub-skills/market-researcher  ~/.workbuddy/skills/

python ~/.workbuddy/skills/deep-research-plus/scripts/drp.py detect   # 期望 zero-degradation
```

其他平台把 `~/.workbuddy` 换成对应目录：Claude Code `~/.claude/skills/`、Codex `~/.codex/skills/`、OpenCode `~/.config/opencode/skills/`、OpenClaw `~/.openclaw/`；Cursor / WPS AI 直接读 `SKILL.md` 并按能力矩阵降级。

### zip 安装（仅编排层）

从 [Releases](https://github.com/Asaceoo/deep-research-plus-skills/releases) 下载 `deep-research-plus-vX.Y.Z.zip`，解压到 `skills/deep-research-plus/`。**zip 不含 sub-skills**，子技能缺失时 `detect` 会列出降级项，流水线仍可跑，能力缩水。

```bash
unzip deep-research-plus-v1.6.1.zip -d ~/.workbuddy/skills/deep-research-plus
python ~/.workbuddy/skills/deep-research-plus/scripts/drp.py validate
```

Python 3.8+，零第三方硬依赖：有 PyYAML 用它，没有走内置子集解析。

## 快速开始

对话里直接说：

> 深度调研一下 2026 年主流开源 TTS 方案，帮我选型。

手工把闸门当 CI 用：

```bash
D=~/.workbuddy/skills/deep-research-plus/scripts/drp.py

python $D init --workspace ./tts --topic "2026 主流开源 TTS 方案"   # 4 条目骨架，含反方
python $D gate --workspace ./tts --stage outline                    # 大纲闸门
python $D gate --workspace ./tts --stage confirm                    # 用户确认落盘后再过
python $D gate --workspace ./tts --stage results                    # 证据合规（可加 --check-links）
python $D gate --workspace ./tts --stage review                     # 反方评审 + 开页留痕
python $D report --workspace ./tts                                  # 渲染六章报告
python $D gate --workspace ./tts --stage report                     # 报告合规
```

## 命令一览

| 命令 | 作用 |
|------|------|
| `validate` | 校验 frontmatter / 悬空路径 / 文档版本 / manifest 一致性 / 清单规则 |
| `detect` | 探测四个依赖子技能，输出降级方案 |
| `init` | 生成 outline / fields / review 骨架 |
| `gate --stage <stage>` | 阶段闸门：outline / confirm / results / review / report |
| `report` | 渲染六章报告（自动生成尾注、数据截点、来源分组） |
| `bump` | 语义化版本递增，同步 SKILL.md / manifest / README / docs / CHANGELOG |
| `package` | 两段校验 → 自动递增 → 构建 zip + SHA256 + release notes（失败自动回滚） |
| `selfcheck` | 清单逐条复核 + 内置流水线回归 |
| `version` | 输出版本 |

退出码：`0` 通过 / `1` 有违规 / `2` 用法或环境错误。全部子命令支持 `--json`。
`report` / `bump` / `package` 会对目标目录加锁（`.drp-lock`，30 分钟过期自动接管），`--no-lock` 可跳过。

## 产物

![产物与发布链路](docs/assets/artifacts.svg)

`package` 产出三件套：`deep-research-plus-v<版本>.zip`、`SHA256SUMS.txt`、`release-notes-v<版本>.md`。zip 内附 `BUILD-MANIFEST.json`，逐文件记录 sha256，可校验来源与完整性。

## 发版

```bash
# 本地：先校验、再递增、再出包；任一步失败都不会改动版本号
python scripts/drp.py package
```

推送带 `[release]` 标记的提交会触发 `.github/workflows/release.yml`：pytest → `validate` → `selfcheck` → `package`，然后以 `v<版本>` 创建或更新 Release，上传 zip / SHA256SUMS / release notes / 双手册 / README。

```bash
git commit -m "feat: 说明改了什么 [release]"
git push origin main
```

也可在仓库 Actions 页手动 Run workflow。提交信息不带 `[release]` 时 job 会被跳过——这是刻意设计，避免每次推送都发版。

## 目录结构

```
deep-research-plus/
├── SKILL.md                  # 技能入口（版本单一事实源，≤19KB）
├── manifest.json             # 核心文件清单（完整快照见 BUILD-MANIFEST.json）
├── scripts/drp.py            # 工具层（单文件，零硬依赖）
├── checklists/
│   ├── skill_audit.yaml      # 十条机器规则
│   └── fixtures/pass/        # 随包 fixture（selfcheck 用）
├── references/               # 报告模板、四类话题示例（SKILL.md 按需指向）
├── docs/                     # 双手册 + 审查记录 + 概念图
├── tests/                    # 全量回归（含失败路径）
└── dist/                     # 发布产物（不入库）
```

## 文档

| 文档 | 内容 |
|------|------|
| [用户手册](./docs/user-guide.md) | 安装、五个场景、标记含义、`spot_checks` 怎么填、故障排查 |
| [技术手册](./docs/technical-manual.md) | 架构、数据契约、闸门与错误码、并发锁、打包回滚、扩展指南 |
| [对抗性审查记录](./docs/adversarial-review.md) | 三视角审查、多轮收敛、真机验证证据 |
| [第三方声明](./THIRD-PARTY-NOTICES.md) | 捆绑子技能的来源与版权归属 |
| [变更日志](./CHANGELOG.md) | 版本历史 |

## 设计约束

- **指针不重复**：子技能正文不复制，只用指针表引用；缺失即降级。
- **闸门可执行**：阶段放行靠退出码，不靠自觉；没有命令执行能力的平台显式标注降级。
- **失败可回滚**：打包先校验再递增，递增后校验失败会恢复到递增前的状态。
- **不编造**：查不到标 `partial`，进「未覆盖」，不用"综合判断"糊过去。
- **版本单一事实源**：`SKILL.md` 的 `version`，其余文件由 `bump` 同步。
- **正文守体积**：`SKILL.md` ≤19KB（CHK-010），细节进 `references/` 或 `docs/`。

## License

MIT（根目录许可不覆盖 `sub-skills/`，见 [THIRD-PARTY-NOTICES.md](./THIRD-PARTY-NOTICES.md)）
