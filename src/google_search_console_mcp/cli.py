"""
[INPUT]: 依赖 argparse、配置层与认证层
[OUTPUT]: 对外提供 build_parser 与 main
[POS]: google_search_console_mcp 的命令行入口，负责显式登录与状态查看
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import argparse

from .auth import get_auth_status, run_oauth_login
from .config import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Google Search Console MCP utilities.")
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

    subparsers = parser.add_subparsers(dest="command", required=True)
    auth_parser = subparsers.add_parser("auth", help="OAuth authentication helpers.")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command", required=True)
    auth_subparsers.add_parser("login", help="Run interactive OAuth login.")
    auth_subparsers.add_parser("status", help="Show local OAuth file status.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.server_config, args.paths_config)

    if args.command == "auth" and args.auth_command == "login":
        status = run_oauth_login(
            client_path=settings.paths.oauth_client_path,
            token_path=settings.paths.token_path,
        )
        print(status.model_dump_json(indent=2))
        return

    if args.command == "auth" and args.auth_command == "status":
        status = get_auth_status(
            client_path=settings.paths.oauth_client_path,
            token_path=settings.paths.token_path,
        )
        print(status.model_dump_json(indent=2))
        return

    raise SystemExit("unknown command")


if __name__ == "__main__":
    main()
