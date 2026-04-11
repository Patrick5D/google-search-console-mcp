"""
[INPUT]: 依赖 pathlib、json、pydantic 与 Google OAuth 库，读取本地 OAuth client 与 token 文件
[OUTPUT]: 对外提供 AuthStatus、get_auth_status、load_token_payload、load_user_credentials 与 run_oauth_login
[POS]: google_search_console_mcp 的认证边界层，被 CLI、server 与 GSC 客户端共享
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pydantic import BaseModel

from .errors import AuthError

GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


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


def load_user_credentials(
    *,
    client_path: str | Path,
    token_path: str | Path,
    scopes: list[str] | None = None,
) -> Credentials:
    scopes = scopes or GSC_SCOPES
    status = get_auth_status(client_path=client_path, token_path=token_path)
    if not status.client_config_exists:
        raise AuthError(f"missing OAuth client config: {client_path}")
    payload = load_token_payload(token_path)
    credentials = Credentials.from_authorized_user_info(payload, scopes=scopes)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        Path(token_path).write_text(credentials.to_json(), encoding="utf-8")
    if not credentials.valid:
        raise AuthError("OAuth credentials are not valid; run auth login")
    return credentials


def run_oauth_login(
    *,
    client_path: str | Path,
    token_path: str | Path,
    scopes: list[str] | None = None,
) -> AuthStatus:
    client_file = Path(client_path)
    if not client_file.exists():
        raise AuthError(f"missing OAuth client config: {client_file}")

    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), scopes or GSC_SCOPES)
    credentials = flow.run_local_server(port=0)

    token_file = Path(token_path)
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    return get_auth_status(client_path=client_file, token_path=token_file)
