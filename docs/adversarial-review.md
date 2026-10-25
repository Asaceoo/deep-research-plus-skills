# 对抗性审查记录

> 版本：1.6.2 ｜ 更新：2026-10-26 ｜ 对象：deep-research-plus 技能包（记录起点 v1.3.1，后续轮次追加在本文件）

本文件记录三视角对抗审查的过程与证据。所有"真实报错"均为本机命令输出原文，未做美化；修复后重跑结果附在每轮末尾。

## 0. 审查方法

| 视角 | 关注点 | 产出物 |
|------|--------|--------|
| 工具实现者 | 脚本自身正确性：解析、边界、退出码、误报率 | 代码修复 + 单元/契约测试 |
| 审查者 | 技能内容是否自洽：声明与实物是否一致、规则是否互相矛盾 | 内容修复 + 清单规则 |
| AI 使用方 | 一个模型拿到这份技能，能否真的被执行、被校验、被纠正 | 机器契约 + 错误码 + JSON 输出 |

每轮流程固定：**跑工具拿真实失败 → 定位是规则错还是内容错 → 修 → 重跑同一命令 → 记录前后差异**。
不以"看代码觉得有问题"为依据，只以命令输出和测试结果为依据。

## 1. 基线取证（改造前，v1.3.1）

拿新写的校验器直接打旧包，得到 13 条失败——这是后续所有修复的起点：

```
$ python scripts/drp.py --skill-dir ~/.workbuddy/skills/deep-research-plus validate \
      --checklist ./checklists/skill_audit.yaml
[FAIL] validate(deep-research-plus v1.3.1): 13 error(s), 0 warning(s)
  [P1] PATH-002 @ SKILL.md: 引用的目录不存在：skills/
  [P1] PATH-002 @ SKILL.md: 引用的目录不存在：sub-skills/
  [P0] PATH-001 @ SKILL.md: 引用的相对路径不存在：tts-comparison/report.md
  [P0] PATH-003 @ SKILL.md: 声称本仓库已捆绑 sub-skills/，但该目录不存在
  [P1] LIC-001 @ LICENSE: 声明 license=MIT 但缺少 LICENSE 文件
  [P0] CHK-001 @ SKILL.md: 闸门矩阵缺少档位行：light
  [P0] CHK-001 @ SKILL.md: 闸门矩阵缺少档位行：standard
  [P0] CHK-004 @ SKILL.md: 声明依赖 sub-skills，但该目录不存在
  [P0] CHK-005 @ manifest.json: 缺少 manifest.json（打包与版本同步依赖它）
  [P0] CHK-006 @ SKILL.md: 缺少必需内容：/drp\.py/
  [P0] CHK-006 @ SKILL.md: 缺少必需内容：/gate --stage/
  [P0] CHK-006 @ SKILL.md: 缺少必需内容：/bump/
  [P0] CHK-006 @ SKILL.md: 缺少必需内容：/package/
```

其中 2 条（PATH-001 的 `tts-comparison/report.md`、PATH-002 的 `skills/`）事后判定为**工具误报**，不是内容缺陷——记在 R1-T1。

## 2. 轮次一：工具实现者视角

| # | 缺陷 | 真实证据 | 修复 |
|---|------|----------|------|
| T1 | 路径规则把调研产物路径当包内路径，产生误报 | 上面 PATH-001/002 两条 | 改为「首段命中包内顶层条目才校验」，未命中且与顶层条目相似度 ≥0.8 时判 PATH-004 疑似笔误，其余视为产物路径 |
| T2 | 报告尾注日期检查恒为失败 | `[P0] G-REP-006 尾注 [^s1] 缺少日期`，而尾注实际含日期 | 根因是 `DATE_RE` 带 `^...$` 锚点却用于 `re.search`；新增 `DATE_IN_TEXT_RE` 专用于文本内嵌日期 |
| T3 | 内置 YAML 解析与 PyYAML 不等值 | `AssertionError: {'desc': '一行说明'} != {'desc': '一行说明\n'}` | 块标量按 YAML 的 clip 语义补尾换行，`|-` 不补 |
| T4 | 通配路径被误判悬空 | `[P0] PATH-001: 引用的相对路径不存在：docs/*.md` | 含 `*` 的 token 走 glob，命中 0 个才报错 |
| T5 | `gate` 单阶段文本模式恒返回 0（闸门等于没有） | `test_gate_cli_returns_nonzero_on_failure` 断言失败 | 改为 `rc = max(rc, report_issues(...))`，文本模式也累计退出码 |
| T6 | 文档承诺「任意子命令后加 `--json`」不成立 | argparse 全局参数必须在子命令前，`version --json` 报 unrecognized | 子命令侧补 `--json`/`--skill-dir`，用 `default=SUPPRESS` 避免覆盖全局值 |

本轮结束测试状态：`85 passed, 7 failed`（7 条里 4 条是 T2/T5 连带，2 条是测试夹具自身写错，1 条是待补文档）。

## 3. 轮次二：审查者视角（内容自洽性）

| # | 缺陷 | 证据 | 修复 |
|---|------|------|------|
| R1 | 声称「本仓库 `sub-skills/` 已捆绑全部四个」但目录不存在 | PATH-003 真实命中 | 删除捆绑声明，改为指针表 + `drp.py detect` 实测探测，输出降级清单 |
| R2 | 声明 `license: MIT` 却没有 LICENSE 文件 | LIC-001 | 补 MIT LICENSE |
| R3 | Phase 3.5 标「🛑 强制」，结尾又写「轻量档允许跳过」——同一份文件两条相反规则 | CHK-001 缺档位矩阵（矩阵是消除歧义的手段） | 新增「闸门矩阵（按档位）」表，逐档写明哪些闸门必跑、允许省略什么 |
| R4 | 复杂度分档边界重叠：≤3 与 3-8、8 与 >8 在两档同时成立 | 人工比对原文 | 改为互斥区间：轻量 1-3 / 标准 4-8 / 深度 ≥9，并写进 `gate_outline` 硬校验 |
| R5 | 引用纪律只要求 `source_url`，没有 https、日期、类型约束 | 与 R4 反例黑名单 R4 自相矛盾 | 升级为三要素强校验：https 完整链接 + `YYYY-MM-DD` + 五类 `source_type` |
| R6 | 能力矩阵说「文件读取缺失 → 跳过子技能检测」，但检测方法本身依赖读文件系统 | 人工比对原文 | 改为「无法读文件系统 → 按全降级模式跑」，并在 detect 输出里区分"脚本探测"与"人工确认" |

本轮结束：旧包 13 条失败中，真实内容缺陷 9 条全部修复；2 条误报由 T1 消除；2 条由新增 manifest/LICENSE 消除。

## 4. 轮次三：AI 使用方视角

站在"模型拿到技能后实际会怎么执行"的角度，问题集中在一件事：**规则只写在散文里，没有可判定的落点**。

| # | 缺陷 | 为什么对 AI 致命 | 修复 |
|---|------|------------------|------|
| A1 | 阶段推进没有机器信号，模型只能"觉得"该进下一阶段 | 长上下文里最容易漏掉的就是"用户确认了吗" | 每阶段一个 `gate --stage`，退出码 0/1/2；Phase 2 必须落 `confirmed/confirmed_at/confirmed_by` 三件套 |
| A2 | 报告模板只是模板，缺章、尾注断链都发现不了 | 模板会被省略成三段 | `report` 确定性渲染六章 + `gate --stage report` 校验章节、尾注、裸域名、AI 腔 |
| A3 | 输出噪音会让模型学会忽略工具 | 一次误报就足以让 agent 把 FAIL 当背景音 | 见 T1：误报率从 2/13 降到 0；另有 `--strict` 单独控制 P2 |
| A4 | 没有机器可读输出，无法接 CI 或其它 agent | 只能人眼看日志 | 全部子命令支持 `--json`，输出 `{ok, errors, issues[], code}` |
| A5 | `init` 生成的骨架跑不过自己的闸门 | 新用户第一步就撞墙，直接弃用 | 模板从「2 条目 + standard 档」改为「4 条目（含 1 反方）+ standard 档」，`test_init_creates_scaffold_and_passes_outline_gate` 守住 |

## 5. 轮次四：收敛验证

```
$ python -m pytest tests -q
92 passed

$ python scripts/drp.py validate
[PASS] validate(deep-research-plus v1.3.1): 0 error(s), 0 warning(s)

$ python scripts/drp.py selfcheck
selfcheck v1.3.1（14 项，失败 0）
```

> 上述输出来自收敛验证时的 `v1.3.1`（92 条测试 / 14 项清单）。v1.4.1 起为 100 条 / 15 项，差异来自后续补的三条规则与消费者回归用例，结论不变。

收敛判定标准（三条同时满足才算收敛）：

1. 全部测试通过（92 条），且每条闸门规则都有一正一负两个用例；
2. 清单 8 条规则 + 5 项基础校验全 PASS，无 SKIP；
3. 连续两轮针对同一命令的输出不再变化（无新增缺陷）。

| 轮次 | 视角 | 新增缺陷 | 其中 P0 | 已修复 | 测试状态 |
|------|------|----------|---------|--------|----------|
| R0 | 基线取证 | 13 | 9 | — | 未建测试 |
| R1 | 工具实现者 | 6 | 2 | 6 | 85 passed / 7 failed |
| R2 | 审查者 | 6 | 3 | 6 | 91 passed / 1 failed |
| R3 | AI 使用方 | 5 | 2 | 5 | 92 passed |
| R4 | 收敛确认 | 0 | 0 | — | 92 passed |

## 6. 真机验证

不是"在临时目录跑一遍"，而是装到真实技能目录后按用户路径跑：

| 步骤 | 命令 | 结果 |
|------|------|------|
| 安装 | 解压 zip 到 `~/.workbuddy/skills/deep-research-plus` | 目录结构与包内一致 |
| 自检 | `drp.py validate` | 0 error / 0 warning |
| 子技能探测 | `drp.py detect` | 命中 deep-research / research / agent-reach / market-researcher 四个真实安装 |
| 建工作区 | `drp.py init --workspace ... --topic ...` | 4 条目骨架，outline 闸门直接通过 |
| 全链路 | `gate outline → confirm → results → review → report → gate report` | 每步退出码 0 |
| 产物 | `drp.py package` | 自动递增 + zip + SHA256 + release notes |
| 解压复核 | 解压到全新目录后 `validate` + `version` | 版本一致，校验通过 |

真机环境：Windows 11 + Python 3.13.14（托管版）与 Python 3.12.4（系统版）双跑，验证零第三方依赖路径。

## 7. 未修复/已知限制

| # | 限制 | 现状 |
|---|------|------|
| L1 | 不校验 URL 存活 | **已改**：默认离线，`--check-links` 显式开启 HEAD 探测（G-RES-020/021） |
| L2 | 内置 YAML 解析不支持锚点/多文档 | 保留。子集解析换零依赖，复杂 YAML 需装 PyYAML，会以退出码 2 明确报错 |
| L3 | 工作区并发写无锁 | **已改**：`report`/`bump`/`package` 加 `.drp-lock`；但 agent 直接改 `results/*.yaml` 仍不受保护 |
| L4 | 去 AI 腔只做黑名单拦截 | 保留。风格改写不该由校验器承担 |
| L5 | 无法判断「链接真但内容不支撑」 | 保留。对策是 `spot_checks` 留痕（G-REV-013/014/015），留痕不等于判定 |

这些限制已同步写入技术手册 §11，避免使用者误以为校验器能兜住一切。

## 8. 第五轮（v1.5.0 → v1.6.2）：从形状校验到失败可回滚

前四轮解决的是「文档自洽」与「规则可执行」；这一轮集中在三件事：内容校验、并发安全、失败后的状态。

| # | 缺陷 | 真实证据 | 修复 |
|---|------|----------|------|
| N1 | 闸门只验形状，假链接照样放行 | 注入 `https://example.com/this-page-does-not-exist-9f2a` → `[PASS] 0 error` | 来源数下限 G-RES-017、反方源类型 G-RES-018、占位链接 G-RES-019、可选 HEAD 探测 G-RES-020/021 |
| N2 | 「承重引用逐条开页」只写在散文里 | `review.yaml` 无任何字段记录是否开页 | `spot_checks` + G-REV-013/014/015，决策级强制留痕 |
| N3 | 报告渲染与六章契约两处漂移 | 实测渲染输出：对比总表无「数据截点」，来源清单未按类型分组 | 渲染器补齐，并加 G-REP-010/011 防回退 |
| N4 | 打包失败会污染版本 | 注入 Unreleased 条目 + 删除 manifest 登记文件 → `package exit=1`，版本仍从 1.6.1 跳到 1.6.2，CHANGELOG 已生成发布段 | 改为两段校验：递增前先校验（放行 DOC/MAN-001），递增后再全量校验，失败用快照回滚 SKILL/manifest/CHANGELOG/README/docs |
| N5 | manifest 结构校验依赖清单 | 删掉清单里的 `manifest_files_exist` 规则后，缺文件不再报警 | 上移为基础校验 MAN-001..003；清单规则降级为补充 |
| N6 | 文档里的数字会漂移 | README 写「121 条回归」，实际已是 123 条 | 移除硬编码条数，改为「全量回归（含失败路径）」；规则条数只写在清单文件里 |
| N7 | 并发写同一目录无保护 | 无锁，后写覆盖先写 | `WorkspaceLock`：O_EXCL 建锁、30 分钟过期接管、异常释放、`--no-lock` 逃生口 |
| N8 | 正文 19.7KB 且不指向 checklist/手册 | 实测 `checklists/` 出现 0 次、手册 0 次 | 模板与示例移入 `references/`，加「包内导航」表，CHK-010 守 19KB 上限 |

收敛验证：

```
$ python -m pytest tests -q
125 passed

$ python scripts/drp.py validate
[PASS] validate(deep-research-plus v1.6.1): 0 error(s), 0 warning(s)

$ python scripts/drp.py selfcheck
selfcheck v1.6.1（16 项，失败 0）
```

回滚探针（N4 修复后）：

```
$ python scripts/drp.py package
[FAIL] 打包前校验未通过，已中止（版本未变动）：
  [P0] MAN-003 @ manifest.json: 登记的文件不存在：docs/adversarial-review.md
exit=1
$ python scripts/drp.py version
1.6.1
```

真机验证覆盖：安装到 `~/.workbuddy/skills/deep-research-plus` 后 `validate` 0/0、`selfcheck` 16 项全 PASS、包内 fixture 五道闸门退出码全 0、锁行为（占用 exit 2 / `--no-lock` 放行）实测。
