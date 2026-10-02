---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

## 中文备注
- **一句话**：派一个后台 agent 去"高信任一手来源"（官方文档、源码、spec、第一方 API）调研问题，把带引用的结论写成仓库里的 Markdown。
- **适用场景**：想要某主题被系统调研、收集文档/API 事实、把阅读苦活委托给后台 agent 时；调研结果喂给 `/grill-with-docs`，不替代思考。
- **类别**：调研
- **注意**：无 disable-model-invocation，agent 可在合适场景自动调用；强调追到源头、每条结论带引用；落盘位置遵循仓库既有约定（无则自行选合理位置并告知）。
<!-- /中文备注 -->

Spin up a **background agent** to do the research, so you keep working while it reads.

Its job:

1. Investigate the question against **primary sources** — official docs, source code, specs, first-party APIs — not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.
