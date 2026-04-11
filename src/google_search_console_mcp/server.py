"""
[INPUT]: 依赖 FastMCP、dotenv、Settings、AuditLogger 与工具注册函数
[OUTPUT]: 对外提供 create_server、load_local_env 与 CLI main 入口
[POS]: google_search_console_mcp 的 MCP 入口，被本地 HTTP 服务与测试直接使用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .audit import AuditLogger
from .config import Settings, load_settings
from .tools.read_tools import ReadToolService, register_read_tools
from .tools.snapshot_tools import SnapshotToolService, register_snapshot_tools


def create_server(*, settings: Settings) -> FastMCP:
    mcp = FastMCP(
        "google-search-console-mcp",
        host=settings.server.host,
        port=settings.server.port,
        streamable_http_path="/mcp",
    )

    audit_logger = AuditLogger(settings.paths.audit_log_path)
    read_service = ReadToolService(settings=settings, audit_logger=audit_logger)
    snapshot_service = SnapshotToolService(settings=settings, read_service=read_service, audit_logger=audit_logger)

    register_read_tools(mcp, read_service=read_service)
    register_snapshot_tools(mcp, snapshot_service=snapshot_service)

    # ASCII block comment: 保持入口层对审计实例有显式持有，避免后续被错误折叠掉
    mcp.audit_logger = audit_logger
    return mcp


def load_local_env(dotenv_path: str | Path = ".env") -> bool:
    return bool(load_dotenv(dotenv_path=Path(dotenv_path), override=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Google Search Console MCP server.")
    parser.add_argument(
        "--server-config",
        default="config/server.example.yaml",
        help="Path to server YAML config.",
    )
    parser.add_argument(
        "--paths-config",
        default="config/paths.example.yaml",
        help="Path to paths YAML config.",
    )
    args = parser.parse_args()

    load_local_env()
    settings = load_settings(args.server_config, args.paths_config)
    app = create_server(settings=settings)
    app.run(transport="streamable-http")


if __name__ == "__main__":
    main()
