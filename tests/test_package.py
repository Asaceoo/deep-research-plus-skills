"""版本递增、文档同步、打包产物与确定性。"""

import hashlib
import json
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_bump_minor_syncs_all_docs(drp_module, skill_dir):
    changelog = skill_dir / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## [Unreleased]\n\n- 新增闸门矩阵与工具层\n\n## [1.2.3] - 2026-01-01\n\n- 初始\n",
        encoding="utf-8",
    )
    assert drp_module.main(["--skill-dir", str(skill_dir), "bump"]) == 0
    assert drp_module.read_version(skill_dir) == "1.3.0"
    assert "版本：1.3.0" in (skill_dir / "README.md").read_text(encoding="utf-8")
    assert "版本：1.3.0" in (skill_dir / "docs" / "USER_MANUAL.md").read_text(encoding="utf-8")
    manifest = json.loads((skill_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "1.3.0"
    text = changelog.read_text(encoding="utf-8")
    assert "## [1.3.0]" in text
    assert text.index("## [Unreleased]") < text.index("## [1.3.0]")


def test_bump_patch_and_major(drp_module, skill_dir):
    assert drp_module.bump_semver("1.2.3", "patch") == "1.2.4"
    assert drp_module.bump_semver("1.2.3", "minor") == "1.3.0"
    assert drp_module.bump_semver("1.2.3", "major") == "2.0.0"


def test_bump_auto_breaking(drp_module, skill_dir):
    (skill_dir / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n- BREAKING 重命名 gate 参数\n", encoding="utf-8"
    )
    assert drp_module.detect_bump_level(skill_dir) == "major"


def test_bump_auto_noop_when_unreleased_empty(drp_module, skill_dir):
    (skill_dir / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.2.3] - 2026-01-01\n\n- 初始\n", encoding="utf-8"
    )
    assert drp_module.detect_bump_level(skill_dir) is None
    assert drp_module.main(["--skill-dir", str(skill_dir), "bump"]) == 0
    assert drp_module.read_version(skill_dir) == "1.2.3"


def test_package_builds_zip_and_checksums(drp_module, skill_dir, tmp_path):
    out = tmp_path / "dist"
    assert drp_module.main(["--skill-dir", str(skill_dir), "package", "--no-bump", "--out", str(out)]) == 0
    zip_path = out / "deep-research-plus-v1.2.3.zip"
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        assert "SKILL.md" in names
        assert "BUILD-MANIFEST.json" in names
        assert "scripts/drp.py" in names
        manifest = json.loads(archive.read("BUILD-MANIFEST.json"))
    assert manifest["version"] == "1.2.3"
    assert any(item["path"] == "SKILL.md" for item in manifest["files"])
    sums = (out / "SHA256SUMS.txt").read_text(encoding="utf-8").strip()
    assert sums == f"{sha(zip_path)}  {zip_path.name}"
    notes = out / "release-notes-v1.2.3.md"
    assert notes.exists()
    assert "SHA256" in notes.read_text(encoding="utf-8")


def test_package_is_deterministic(drp_module, skill_dir, tmp_path):
    out = tmp_path / "dist"
    drp_module.main(["--skill-dir", str(skill_dir), "package", "--no-bump", "--out", str(out)])
    first = sha(out / "deep-research-plus-v1.2.3.zip")
    drp_module.main(["--skill-dir", str(skill_dir), "package", "--no-bump", "--out", str(out)])
    assert sha(out / "deep-research-plus-v1.2.3.zip") == first


def test_package_aborts_on_validation_failure(drp_module, skill_dir, tmp_path):
    (skill_dir / "docs" / "USER_MANUAL.md").write_text(
        "# u\n\n> 版本：9.9.9 ｜ 更新：2026-01-01\n", encoding="utf-8"
    )
    out = tmp_path / "dist"
    assert drp_module.main(["--skill-dir", str(skill_dir), "package", "--no-bump", "--out", str(out)]) == 1
    assert not (out / "deep-research-plus-v1.2.3.zip").exists()


def test_package_auto_bumps_then_builds(drp_module, skill_dir, tmp_path):
    (skill_dir / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n- 新增 detect 子命令\n\n## [1.2.3] - 2026-01-01\n\n- 初始\n",
        encoding="utf-8",
    )
    out = tmp_path / "dist"
    assert drp_module.main(["--skill-dir", str(skill_dir), "package", "--out", str(out)]) == 0
    assert (out / "deep-research-plus-v1.3.0.zip").exists()
    assert drp_module.read_version(skill_dir) == "1.3.0"
