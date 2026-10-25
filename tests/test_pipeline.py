"""端到端：init → gate → report → 全链路 CLI 返回码。"""

import json
from pathlib import Path


def test_init_creates_scaffold_and_passes_outline_gate(drp_module, tmp_path, capsys):
    ws = tmp_path / "ws"
    rc = drp_module.main(["init", "--workspace", str(ws), "--topic", "测试话题", "--slug", "test-topic"])
    assert rc == 0
    assert (ws / "outline.yaml").exists()
    assert (ws / "fields.yaml").exists()
    assert (ws / "review.yaml").exists()
    assert (ws / "results").is_dir()
    issues = drp_module.gate_outline(ws, False)
    assert not [i for i in issues if i.severity in ("P0", "P1")], [i.render() for i in issues]


def test_init_refuses_non_empty_dir(drp_module, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "keep.txt").write_text("x", encoding="utf-8")
    assert drp_module.main(["init", "--workspace", str(ws), "--topic", "t"]) == 2
    assert drp_module.main(["init", "--workspace", str(ws), "--topic", "t", "--force"]) == 0


def test_gate_cli_returns_nonzero_on_failure(drp_module, pass_ws):
    text = (pass_ws / "outline.yaml").read_text(encoding="utf-8").replace("kind: counter", "kind: normal")
    (pass_ws / "outline.yaml").write_text(text, encoding="utf-8")
    assert drp_module.main(["gate", "--workspace", str(pass_ws), "--stage", "outline"]) == 1


def test_gate_cli_json_payload(drp_module, pass_ws, capsys):
    text = (pass_ws / "outline.yaml").read_text(encoding="utf-8").replace("kind: counter", "kind: normal")
    (pass_ws / "outline.yaml").write_text(text, encoding="utf-8")
    drp_module.main(["gate", "--workspace", str(pass_ws), "--stage", "outline", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert any(item["code"] == "G-OUT-012" for item in payload["issues"])


def test_report_cli_then_report_gate(drp_module, pass_ws, capsys):
    assert drp_module.main(["report", "--workspace", str(pass_ws)]) == 0
    assert (pass_ws / "report.md").exists()
    assert drp_module.main(["gate", "--workspace", str(pass_ws), "--stage", "report"]) == 0


def test_gate_all_stops_on_first_failures(drp_module, pass_ws):
    assert drp_module.main(["gate", "--workspace", str(pass_ws), "--stage", "all"]) == 1  # 还没渲染 report.md
    drp_module.main(["report", "--workspace", str(pass_ws)])
    assert drp_module.main(["gate", "--workspace", str(pass_ws), "--stage", "all"]) == 0


def test_validate_cli_ok_and_broken(drp_module, skill_dir, capsys):
    assert drp_module.main(["--skill-dir", str(skill_dir), "validate"]) == 0
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8").replace("version: 1.2.3", "version: 1.2"),
        encoding="utf-8",
    )
    assert drp_module.main(["--skill-dir", str(skill_dir), "validate"]) == 1
    out = capsys.readouterr().out
    assert "FM-002" in out or "FM-003" in out


def test_version_cli_json(drp_module, skill_dir, capsys):
    assert drp_module.main(["--skill-dir", str(skill_dir), "version", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == "1.2.3"
    assert payload["name"] == "deep-research-plus"


def test_detect_reports_four_sub_skills(drp_module, skill_dir):
    result = drp_module.detect_sub_skills(skill_dir)
    assert set(result["sub_skills"]) == {"deep-research", "research", "agent-reach", "market-researcher"}
    assert result["level"].endswith("degraded") or result["level"] == "zero-degradation"


def test_selfcheck_on_real_pack(drp_module):
    root = Path(__file__).resolve().parents[1]
    rc = drp_module.main(["--skill-dir", str(root), "selfcheck", "--no-pipeline"])
    assert rc == 0
