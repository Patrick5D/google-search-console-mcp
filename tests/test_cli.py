"""
[INPUT]: 依赖未来的 google_search_console_mcp.cli 模块
[OUTPUT]: 对外提供 auth CLI 结构测试
[POS]: tests 的命令行入口测试，先锁定 auth login/status 的命令面
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from google_search_console_mcp.cli import build_parser


def test_build_parser_has_login_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["auth", "login"])
    assert args.command == "auth"
    assert args.auth_command == "login"
