import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("drp", ROOT / "scripts" / "drp.py")
drp = importlib.util.module_from_spec(SPEC)
sys.modules["drp"] = drp
SPEC.loader.exec_module(drp)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def drp_module():
    return drp


@pytest.fixture()
def pass_ws(tmp_path):
    """可用的调研工作区副本。"""
    target = tmp_path / "ws"
    shutil.copytree(FIXTURES / "pass", target)
    return target


@pytest.fixture()
def skill_dir(tmp_path):
    """最小可用技能包，含 SKILL.md/manifest/docs/checklist/LICENSE。"""
    root = tmp_path / "deep-research-plus"
    (root / "docs").mkdir(parents=True)
    (root / "checklists").mkdir()
    (root / "scripts").mkdir()
    (root / "scripts" / "drp.py").write_text("# stub\n", encoding="utf-8")
    (root / "SKILL.md").write_text(
        "---\n"
        "name: deep-research-plus\n"
        'description: "测试技能。Triggers: 测试"\n'
        "version: 1.2.3\n"
        "license: MIT\n"
        "---\n\n"
        "# 测试技能\n\n"
        "## 能力需求\n\n表格\n\n"
        "## 流水线\n\nPhase 0 Phase 1 Phase 2 🛑 Phase 3 Phase 4\n\n"
        "## 反例黑名单\n\n| R1 | 反模式 | 替代 |\n\n"
        "## 使用示例\n\n例子\n\n"
        "## 闸门矩阵（按档位）\n\n"
        "| 档位 | 闸门 |\n|---|---|\n"
        "| `light` | 必跑 |\n| `standard` | 必跑 |\n| `deep` | 必跑 |\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# t\n\n> 版本：1.2.3 ｜ 更新：2026-01-01\n", encoding="utf-8")
    (root / "docs" / "USER_MANUAL.md").write_text("# u\n\n> 版本：1.2.3 ｜ 更新：2026-01-01\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n- 维护性更新\n\n## [1.2.3] - 2026-01-01\n\n- 初始\n",
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        '{\n  "name": "deep-research-plus",\n  "version": "1.2.3",\n  "entry": "SKILL.md",\n'
        '  "license": "MIT",\n  "files": ["SKILL.md", "README.md", "LICENSE", "docs/USER_MANUAL.md"]\n}\n',
        encoding="utf-8",
    )
    (root / "checklists" / "skill_audit.yaml").write_text(
        "rules:\n"
        "  - id: CHK-001\n    type: gate_matrix\n    severity: P0\n"
        "    desc: 档位矩阵\n",
        encoding="utf-8",
    )
    return root
