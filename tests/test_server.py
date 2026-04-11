"""
[INPUT]: 依赖 google_search_console_mcp.config 与未来的 server 模块
[OUTPUT]: 对外提供 FastMCP 入口组装测试
[POS]: tests 的 server 层入口，先锁定 MCP 服务名与最小装配行为
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from google_search_console_mcp.config import Settings
from google_search_console_mcp.server import create_server


def test_create_server_uses_expected_name() -> None:
    server = create_server(settings=Settings())
    assert server.name == "google-search-console-mcp"
