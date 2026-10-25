# 报告模板（Phase 4 参考）

`python scripts/drp.py report --workspace <dir>` 会按本模板渲染 `report.md`；手写报告时逐字对齐结构，`gate --stage report` 按此校验。

## 骨架

```markdown
# <话题> 深度调研报告
> 调研日期：YYYY-MM-DD ｜ 方法：deep-research-plus vX（分档：standard/deep）｜ 能力组合：并行/串行+抓取/摘要级 ｜ 评审：反方评审已过

## 1. 核心结论（TL;DR）
- 结论一句话，单源标 `single-source`，仅社区支撑标 `high-risk` [^s1]

## 2. 对比总表
> 数据截点：YYYY-MM-DD（各条证据日期见第 6 章）

| 条目 | 字段 A | 字段 B |
|---|---|---|
| 候选一 | 值 | 值 |

## 3. 逐项详析

### 1. <item 标题>
- 事实：一句话（`official`，YYYY-MM-DD）[^s2]
- 反证/不确定性：…

## 4. 冲突与存疑
- 多源矛盾点（写清各自口径）
- 证据绑定降级项：无证据结论一律放这里

## 5. 未覆盖与限制
- 反方评审 2 轮后仍未查到的项

## 6. 来源清单

### official（N 条）
[^s1]: <https://example.com/doc> ｜ YYYY-MM-DD ｜ `official`

### code（N 条）
[^s2]: <https://github.com/org/repo> ｜ YYYY-MM-DD ｜ `code`
```

## 硬性规则

| 规则 | 说明 | 违反后果 |
|------|------|----------|
| 六章齐全 | 缺任何一章即判不合格 | G-REP-002 P0 |
| 报告头四项 | 调研日期 / 分档 / 能力组合 / 评审状态 | G-REP-003 P1 |
| 尾注可解析 | 每个 `[^x]` 都要有定义，定义为 `<完整 https URL> ｜ 日期 ｜ 类型` | G-REP-004/005/006 P0 |
| 无裸域名 | `来源：arxiv.org` 这类不算引用 | G-REP-007 P0 |
| 数据截点 | 对比总表写明证据日期上限 | G-REP-010 P2 |
| 来源分组 | 第 6 章按 `source_type` 分组 | G-REP-011 P2 |
| 无 AI 腔 | 黑名单见 SKILL.md R2 | G-REP-008 P1 |

## 无文件能力时

按同样六章分段输出在对话，尾注改为行内链接（`[来源](https://…)`），并在报告头注明 `manual-gate`。
