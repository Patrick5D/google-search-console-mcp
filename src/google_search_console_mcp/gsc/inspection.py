"""
[INPUT]: 依赖 Search Console URL Inspection API 的 inspect() 能力
[OUTPUT]: 对外提供 inspect_url
[POS]: gsc 的 URL 检查读取器，负责单 URL 索引状态查询
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations


def inspect_url(service, *, property_uri: str, inspection_url: str) -> dict[str, object]:
    body = {"inspectionUrl": inspection_url, "siteUrl": property_uri}
    return service.urlInspection().index().inspect(body=body).execute()
