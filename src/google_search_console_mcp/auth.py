"""
[INPUT]: 依赖 pathlib、json 与 pydantic，读取本地 OAuth client 与 token 文件
[OUTPUT]: 对外提供 AuthStatus、get_auth_status 与 load_token_payload
[POS]: google_search_console_mcp 的认证边界层，被 CLI、server 与 GSC 客户端共享
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from .errors import AuthError


class AuthStatus(BaseModel):
    client_config_exists: bool
    token_exists: bool
    ready: bool


def get_auth_status(*, client_path: str | Path, token_path: str | Path) -> AuthStatus:
    client_file = Path(client_path)
    token_file = Path(token_path)
    return AuthStatus(
        client_config_exists=client_file.exists(),
        token_exists=token_file.exists(),
        ready=client_file.exists() and token_file.exists(),
    )


def load_token_payload(token_path: str | Path) -> dict[str, object]:
    path = Path(token_path)
    if not path.exists():
        raise AuthError(f"missing token file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuthError(f"invalid token file: {path}") from exc
