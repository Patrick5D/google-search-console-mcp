"""
[INPUT]: 依赖 googleapiclient、google.oauth2.credentials 与本地 token payload
[OUTPUT]: 对外提供 build_search_console_service
[POS]: gsc 的 service 构造器，被 sites、performance、inspection 与 sitemaps 模块共享
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from ..auth import load_token_payload

GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def build_search_console_service(token_path: str | Path) -> Any:
    payload = load_token_payload(token_path)
    credentials = Credentials.from_authorized_user_info(payload, scopes=GSC_SCOPES)
    return build("searchconsole", "v1", credentials=credentials, cache_discovery=False)
