# 第三方组件声明 (Third-Party Notices)

本仓库（deep-research-plus-skills）由两部分组成：

## 1. 编排层（本仓库原创，MIT License）

- `SKILL.md`、`README.md`、`docs/`、`CHANGELOG.md` — 由本项目维护者编写，适用仓库根目录的 [MIT License](./LICENSE)。

## 2. 捆绑的子技能（`sub-skills/` 目录，版权归原作者）

为使技能开箱即用（克隆即可完整执行），本仓库捆绑了 4 个第三方子技能。**它们的版权与所有权利归各自作者所有**；各目录内容以捆绑时原样收录，未做修改（仅移除 `__pycache__` 等运行时产物）。若你是权利人且不希望被收录，请提 issue，我们会立即移除。

| 子技能 | 目录 | 捆绑版本 | 来源 |
|--------|------|----------|------|
| Deep Research | `sub-skills/deep-research/` | 1.0.0 | WorkBuddy 技能市场（市场版）；上游开源项目 [Weizhena/Deep-Research-skills](https://github.com/Weizhena/Deep-Research-skills) |
| research | `sub-skills/research/` | — | 单文件技能（一手来源调研纪律）；上游为 Anthropic skills 生态流传版本 |
| Agent Reach | `sub-skills/agent-reach/` | 1.1.0 | SkillHub 市场版；上游开源项目 agent-reach（7500+ GitHub stars） |
| market-researcher | `sub-skills/market-researcher/` | 1.0.1 | WorkBuddy 技能市场（市场版） |

**说明**：

- 截至捆绑日期（2026-10-02），各子技能分发目录中均未随附 LICENSE 文件，其授权条款以各自上游项目的声明为准。
- 仓库根目录的 MIT License **不覆盖** `sub-skills/` 目录内容。
- 各子技能可独立安装使用（见 README「安装」），捆绑仅为降低用户的完整部署成本。
