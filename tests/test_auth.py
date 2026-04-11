"""
[INPUT]: 依赖 pathlib 与未来的 google_search_console_mcp.auth 模块
[OUTPUT]: 对外提供认证状态与 token 缺失行为测试
[POS]: tests 的认证层入口，先约束未登录状态的可观测输出
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path

from google_search_console_mcp.auth import get_auth_status


def test_get_auth_status_reports_missing_token(tmp_path: Path) -> None:
    client = tmp_path / "oauth_client.json"
    client.write_text("{}", encoding="utf-8")

    status = get_auth_status(client_path=client, token_path=tmp_path / "token.json")

    assert status.client_config_exists is True
    assert status.token_exists is False
    assert status.ready is False
