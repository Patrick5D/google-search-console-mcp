"""
[INPUT]: 依赖 Search Console service 的 sites().list() 能力
[OUTPUT]: 对外提供 list_properties 与 get_property
[POS]: gsc 的站点读取器，负责 property 枚举与访问校验
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from ..errors import AuthorizationError


def list_properties(service) -> list[dict[str, object]]:
    response = service.sites().list().execute()
    return list(response.get("siteEntry", []))


def get_property(service, property_uri: str) -> dict[str, object]:
    for entry in list_properties(service):
        if entry.get("siteUrl") == property_uri:
            return entry
    raise AuthorizationError(f"property not accessible: {property_uri}")
