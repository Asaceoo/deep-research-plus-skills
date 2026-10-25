"""并发锁：同一目录只允许一个写操作，过期锁自动接管。"""

import json
import os
import time

import pytest


def test_second_writer_blocked(drp_module, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    with drp_module.WorkspaceLock(ws, "report"):
        with pytest.raises(drp_module.DrpError):
            with drp_module.WorkspaceLock(ws, "bump"):
                pass
    assert not (ws / drp_module.LOCK_NAME).exists()


def test_stale_lock_taken_over(drp_module, tmp_path, capsys):
    ws = tmp_path / "ws"
    ws.mkdir()
    lock = ws / drp_module.LOCK_NAME
    lock.write_text(json.dumps({"pid": 999999, "command": "report"}), encoding="utf-8")
    old = time.time() - drp_module.LOCK_TTL_SECONDS - 60
    os.utime(lock, (old, old))
    with drp_module.WorkspaceLock(ws, "bump") as held:
        assert held.held
    assert "接管过期锁" in capsys.readouterr().out
    assert not lock.exists()


def test_lock_released_on_exception(drp_module, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    with pytest.raises(RuntimeError):
        with drp_module.WorkspaceLock(ws, "report"):
            raise RuntimeError("boom")
    assert not (ws / drp_module.LOCK_NAME).exists()


def test_lock_can_be_disabled(drp_module, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    lock = ws / drp_module.LOCK_NAME
    lock.write_text(json.dumps({"pid": 999999, "command": "report"}), encoding="utf-8")
    with drp_module.WorkspaceLock(ws, "bump", enabled=False) as held:
        assert not held.held
    assert lock.exists()  # 关掉锁就不动它


def test_lock_missing_directory_is_noop(drp_module, tmp_path):
    with drp_module.WorkspaceLock(tmp_path / "nope", "report") as held:
        assert not held.held


def test_report_cli_skips_lock_with_flag(drp_module, pass_ws):
    from pathlib import Path

    lock = Path(pass_ws) / drp_module.LOCK_NAME
    lock.write_text(json.dumps({"pid": 999999, "command": "other"}), encoding="utf-8")
    assert drp_module.main(["report", "--workspace", str(pass_ws)]) == 2
    assert drp_module.main(["report", "--workspace", str(pass_ws), "--no-lock"]) == 0
