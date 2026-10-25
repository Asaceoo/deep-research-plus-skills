"""frontmatter 解析与基础校验。"""

from pathlib import Path


def codes(issues):
    return {i.code for i in issues}


def test_parse_ok(drp_module):
    meta, body, lines = drp_module.parse_frontmatter(
        "---\nname: x\nversion: 1.0.0\n---\n\n# body\n"
    )
    assert meta["name"] == "x"
    assert meta["version"] == "1.0.0"
    assert body.startswith("\n# body")
    assert lines >= 3


def test_parse_missing(drp_module):
    meta, body, _ = drp_module.parse_frontmatter("# no fm\n")
    assert meta == {}
    assert body == "# no fm\n"


def test_missing_required_keys(drp_module, skill_dir):
    issues = drp_module.check_frontmatter(skill_dir, {"name": "deep-research-plus"})
    assert "FM-002" in codes(issues)


def test_bad_version(drp_module, skill_dir):
    issues = drp_module.check_frontmatter(
        skill_dir, {"name": "deep-research-plus", "description": "d Triggers", "version": "v1"}
    )
    assert "FM-003" in codes(issues)


def test_name_mismatch(drp_module, skill_dir):
    issues = drp_module.check_frontmatter(
        skill_dir, {"name": "other-skill", "description": "d Triggers", "version": "1.0.0"}
    )
    assert "FM-004" in codes(issues)


def test_missing_triggers_is_warning(drp_module, skill_dir):
    issues = drp_module.check_frontmatter(
        skill_dir, {"name": "deep-research-plus", "description": "没有关键词声明", "version": "1.0.0"}
    )
    assert "FM-005" in codes(issues)
    assert all(i.severity == "P2" for i in issues if i.code == "FM-005")


def test_license_without_file(drp_module, skill_dir):
    (skill_dir / "LICENSE").unlink()
    issues = drp_module.check_license(skill_dir, {"license": "MIT"})
    assert "LIC-001" in codes(issues)


def test_doc_version_mismatch(drp_module, skill_dir):
    (skill_dir / "docs" / "USER_MANUAL.md").write_text(
        "# u\n\n> 版本：9.9.9 ｜ 更新：2026-01-01\n", encoding="utf-8"
    )
    issues = drp_module.check_versions(skill_dir, {"version": "1.2.3"})
    assert "DOC-002" in codes(issues)


def test_doc_version_header_missing(drp_module, skill_dir):
    (skill_dir / "docs" / "USER_MANUAL.md").write_text("# u\n\n无版本头\n", encoding="utf-8")
    issues = drp_module.check_versions(skill_dir, {"version": "1.2.3"})
    assert "DOC-001" in codes(issues)


def test_dangling_package_path(drp_module, skill_dir):
    body = "见 `scripts/missing.py`。"
    issues = drp_module.check_paths(skill_dir, body)
    assert "PATH-001" in codes(issues)


def test_typo_path_detected(drp_module, skill_dir):
    body = "见 `script/drp.py`。"
    issues = drp_module.check_paths(skill_dir, body)
    assert "PATH-004" in codes(issues)


def test_workspace_artifact_path_ignored(drp_module, skill_dir):
    body = "产物写到 `tts-comparison/report.md`，续跑看 `results/`。"
    assert drp_module.check_paths(skill_dir, body) == []


def test_fake_bundle_claim(drp_module, skill_dir):
    body = "本仓库 `sub-skills/` 已捆绑全部四个。"
    issues = drp_module.check_paths(skill_dir, body)
    assert "PATH-003" in codes(issues)


def test_structure_missing_section(drp_module, skill_dir):
    issues = drp_module.check_structure(skill_dir, {}, "# 空\n\n## 能力需求\n")
    assert "SEC-001" in codes(issues)
    assert "SEC-002" in codes(issues)
    assert "SEC-003" in codes(issues)
