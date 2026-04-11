"""
[INPUT]: 依赖认证、快照与工具服务模块
[OUTPUT]: 对外提供 review 反馈修复的回归测试
[POS]: tests 的回归入口，约束安全边界和运行时语义不再回退
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from google_search_console_mcp.audit import AuditLogger
from google_search_console_mcp.auth import get_auth_status
from google_search_console_mcp.config import Settings
from google_search_console_mcp.errors import SnapshotError
from google_search_console_mcp.tools.read_tools import ReadToolService
from google_search_console_mcp.tools.snapshot_tools import SnapshotToolService


class StubReadService:
    def __init__(self, rows):
        self._rows = rows

    def get_site_daily_summary(self, **kwargs):
        return self._rows


def test_read_snapshot_rejects_paths_outside_snapshot_root(tmp_path: Path) -> None:
    settings = Settings()
    settings.paths.snapshot_root = str(tmp_path / "snapshots")
    service = SnapshotToolService(settings=settings, read_service=StubReadService(rows=[]))

    outside = tmp_path / "outside.csv"
    outside.write_text("a,b\n1,2\n", encoding="utf-8")

    with pytest.raises(SnapshotError):
        service.read_snapshot(str(outside))


def test_snapshot_site_day_raises_when_no_rows_returned(tmp_path: Path) -> None:
    settings = Settings()
    settings.paths.snapshot_root = str(tmp_path / "snapshots")
    service = SnapshotToolService(settings=settings, read_service=StubReadService(rows=[]))

    with pytest.raises(SnapshotError):
        service.snapshot_site_day(property_uri="sc-domain:example.com", date="2026-04-11")


def test_read_tool_service_writes_audit_log(tmp_path: Path) -> None:
    settings = Settings()
    settings.paths.oauth_client_path = str(tmp_path / "oauth_client.json")
    settings.paths.token_path = str(tmp_path / "token.json")
    settings.paths.audit_log_path = str(tmp_path / "audit.jsonl")
    Path(settings.paths.oauth_client_path).write_text("{}", encoding="utf-8")
    Path(settings.paths.token_path).write_text("{}", encoding="utf-8")

    service = ReadToolService(
        settings=settings,
        service_factory=lambda **kwargs: object(),
        audit_logger=AuditLogger(settings.paths.audit_log_path),
    )

    payload = service.get_account_status()

    assert payload["ready"] is False
    log_text = Path(settings.paths.audit_log_path).read_text(encoding="utf-8")
    assert '"tool_name":"get_account_status"' in log_text


def test_get_auth_status_marks_invalid_token_not_ready(tmp_path: Path) -> None:
    client = tmp_path / "oauth_client.json"
    token = tmp_path / "token.json"
    client.write_text("{}", encoding="utf-8")
    token.write_text(json.dumps({"not": "credentials"}), encoding="utf-8")

    status = get_auth_status(client_path=client, token_path=token)

    assert status.client_config_exists is True
    assert status.token_exists is True
    assert status.ready is False
