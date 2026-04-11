"""
[INPUT]: 依赖 pathlib 与未来的 google_search_console_mcp.config 模块
[OUTPUT]: 对外提供配置读取与默认值行为测试
[POS]: tests 的配置层入口，先约束两份 YAML 合并成统一 Settings
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path

from google_search_console_mcp.config import load_settings


def test_load_settings_reads_server_and_paths(tmp_path: Path) -> None:
    server = tmp_path / "server.yaml"
    paths = tmp_path / "paths.yaml"
    server.write_text("server:\n  host: 127.0.0.1\n  port: 8766\n", encoding="utf-8")
    paths.write_text(
        "paths:\n"
        "  oauth_client_path: ./config/oauth_client.json\n"
        "  token_path: ./config/token.json\n"
        "  snapshot_root: ./snapshots\n",
        encoding="utf-8",
    )

    settings = load_settings(server, paths)

    assert settings.server.port == 8766
    assert settings.paths.snapshot_root == "./snapshots"
