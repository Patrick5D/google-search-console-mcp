"""
[INPUT]: 依赖 googleapiclient 与认证层的可刷新用户凭据
[OUTPUT]: 对外提供 build_search_console_service
[POS]: gsc 的 service 构造器，被 sites、performance、inspection 与 sitemaps 模块共享
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build

from ..auth import GSC_SCOPES, load_user_credentials


def build_search_console_service(token_path: str, client_path: str = "./config/oauth_client.json") -> Any:
    credentials = load_user_credentials(
        client_path=client_path,
        token_path=token_path,
        scopes=GSC_SCOPES,
    )
    return build("searchconsole", "v1", credentials=credentials, cache_discovery=False)
