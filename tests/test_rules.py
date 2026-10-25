"""清单规则引擎：六类 handler 的正反例 + 未知类型保护。"""


def run(drp_module, skill_dir, body, rules):
    return drp_module.run_checklist(skill_dir, {}, body, {"rules": rules})


def ids(issues):
    return [i.code for i in issues]


def test_forbidden_pattern_hit(drp_module, skill_dir):
    body = "## 能力需求\n\n建议先搜官方文档。\n"
    issues = run(
        drp_module,
        skill_dir,
        body,
        [{"id": "CHK-X", "type": "forbidden_patterns", "severity": "P1",
          "params": {"patterns": ["建议"]}}],
    )
    assert ids(issues) == ["CHK-X"]


def test_forbidden_pattern_ignores_section(drp_module, skill_dir):
    body = "## 反例黑名单\n\n建议这类软表述不算规则。\n"
    issues = run(
        drp_module,
        skill_dir,
        body,
        [{"id": "CHK-X", "type": "forbidden_patterns", "severity": "P1",
          "params": {"patterns": ["建议"], "ignore_in_sections": ["反例黑名单"]}}],
    )
    assert issues == []


def test_conflict_pair(drp_module, skill_dir):
    body = "Phase 2 是硬停闸门，但也允许跳过 Phase 2。\n"
    issues = run(
        drp_module,
        skill_dir,
        body,
        [{"id": "CHK-C", "type": "conflict_pairs", "severity": "P0",
          "params": {"pairs": [["跳过 Phase 2", "Phase 2[^\\n]{0,24}(硬停|强制)"]]}}],
    )
    assert ids(issues) == ["CHK-C"]


def test_required_patterns_missing(drp_module, skill_dir):
    issues = run(
        drp_module,
        skill_dir,
        "没有任何命令\n",
        [{"id": "CHK-R", "type": "required_patterns", "severity": "P0",
          "params": {"patterns": ["drp\\.py"]}}],
    )
    assert ids(issues) == ["CHK-R"]


def test_claim_requires_dir(drp_module, skill_dir):
    issues = run(
        drp_module,
        skill_dir,
        "本仓库 `sub-skills/` 已捆绑四个子技能。\n",
        [{"id": "CHK-D", "type": "claim_requires_dir", "severity": "P0",
          "params": {"claims": [{"pattern": "本仓库[^\\n]{0,20}已(捆绑|内置)", "requires_dir": "sub-skills"}]}}],
    )
    assert ids(issues) == ["CHK-D"]


def test_manifest_missing_file(drp_module, skill_dir):
    import json

    manifest = json.loads((skill_dir / "manifest.json").read_text(encoding="utf-8"))
    manifest["files"].append("docs/GONE.md")
    (skill_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    issues = run(
        drp_module,
        skill_dir,
        "",
        [{"id": "CHK-M", "type": "manifest_files_exist", "severity": "P0",
          "params": {"required_keys": ["name", "version"]}}],
    )
    assert "CHK-M" in ids(issues)


def test_gate_matrix_requires_three_tiers(drp_module, skill_dir):
    issues = run(
        drp_module,
        skill_dir,
        "| 档位 |\n|---|\n| light |\n",
        [{"id": "CHK-G", "type": "gate_matrix", "severity": "P0", "params": {}}],
    )
    assert len(issues) == 2  # standard / deep 缺行


def test_unknown_rule_type_fails_loudly(drp_module, skill_dir):
    issues = run(
        drp_module,
        skill_dir,
        "",
        [{"id": "CHK-BAD", "type": "no_such_type", "severity": "P1", "params": {}}],
    )
    assert ids(issues) == ["CHK-000"]


def test_test_prompts_missing(drp_module, skill_dir):
    issues = run(
        drp_module,
        skill_dir,
        "",
        [{"id": "CHK-P", "type": "test_prompts_present", "severity": "P1",
          "params": {"path": "test-prompts.json"}}],
    )
    assert ids(issues) == ["CHK-P"]


def test_test_prompts_without_anomaly(drp_module, skill_dir):
    import json

    (skill_dir / "test-prompts.json").write_text(
        json.dumps(
            {"prompts": [
                {"id": "a", "kind": "typical", "prompt": "p1", "expects": ["x"]},
                {"id": "b", "kind": "typical", "prompt": "p2", "expects": ["y"]},
                {"id": "c", "kind": "typical", "prompt": "p3", "expects": ["z"]},
            ]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    issues = run(
        drp_module,
        skill_dir,
        "",
        [{"id": "CHK-P", "type": "test_prompts_present", "severity": "P1",
          "params": {"min_prompts": 3, "min_anomaly": 1}}],
    )
    assert ids(issues) == ["CHK-P"]
    assert "anomaly" in issues[0].message


def test_test_prompts_ok(drp_module, skill_dir):
    import json
    import shutil
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / "test-prompts.json"
    shutil.copy(source, skill_dir / "test-prompts.json")
    issues = run(
        drp_module,
        skill_dir,
        "",
        [{"id": "CHK-P", "type": "test_prompts_present", "severity": "P1",
          "params": {"min_prompts": 3, "min_anomaly": 1}}],
    )
    assert issues == []


def test_checklist_file_missing(drp_module, skill_dir):
    import pytest

    with pytest.raises(drp_module.DrpError):
        drp_module.load_checklist(skill_dir, str(skill_dir / "nope.yaml"))
