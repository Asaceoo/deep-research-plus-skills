# 使用示例全集（四类话题 + 续跑）

SKILL.md 只保留最短路径示例；这里是完整执行记录，照着改参数即可。

## 1. 技术选型（standard / deep）

> 深度调研一下 2026 年主流开源 TTS 方案，帮我选型。

```
Phase 0  判 type=tech、tier=standard（6 个候选）→ 告知用户可升 deep
Phase 1  init --workspace ./tts --topic "2026 主流开源 TTS 方案"
         补 items：5 个候选 + 1 个 counter（"各方案已知缺陷与社区吐槽"）
         gate --workspace ./tts --stage outline        → 0
🛑      用户确认 → 在 outline.yaml 写 confirmed: true / confirmed_at / confirmed_by
         gate --stage confirm                          → 0
Phase 3  每项先查官方 docs / 仓库源码，社区帖只作补充
         每项至少 2 个独立 URL；counter 项至少 3 个且含 1 条 official|code
         gate --stage results                          → 0
Phase 3.5 挑 3 条承重结论开页核对，写 review.yaml 的 spot_checks
         gate --stage review                           → 0
Phase 4  report --workspace ./tts → gate --stage report → 0
```

常见失分：只收官方 benchmark 当性能证据（缺第三方复测）、counter 项只贴一条 Reddit 吐槽（G-RES-018 拦）。

## 2. 市场 / 商业（deep）

> 调研国内免漆门行业的渠道结构。

- `type: market`，商业标注规范全开：每条数据带来源 + 日期，定量结论写清口径与假设。
- 查不到的产能/份额标 `partial`，进「未覆盖」，不要用"约""大概"填坑。
- 渠道分层（工程 / 家装 / 电商 / 出口）每一个都要有独立来源，不能靠一份研报推全部。

## 3. 舆情 / 社区（standard）

> 看看 B 站和小红书上对某款剪辑软件的真实评价。

- 社区源为主，`source_type: community`；决策级结论若只有 UGC 支撑，必须标 `high-risk`。
- 补一条官方口径做交叉验证，否则结论进「冲突与存疑」而不是 TL;DR。
- 抓不到（需 cookie / 反爬）就跳过该频道，不算调研失败，在「未覆盖」写明。

## 4. 单点事实（light）

> 帮我查一下 X 的最新版本号。

`light` 档：直接搜，口头确认，不派子代理，不落 `report.md`，不跑全流水线。1-3 个条目、每项 1 个来源即可。

## 5. 断点续跑

中断后重开：

1. `ls results/` 看已完成编号，只补缺失项；
2. `drp.py gate --stage outline` 确认大纲没被改坏；
3. 继续 Phase 3，每完成一项立刻落盘（锁文件 `.drp-lock` 只在写操作期间存在，异常中断 30 分钟后自动过期）。
