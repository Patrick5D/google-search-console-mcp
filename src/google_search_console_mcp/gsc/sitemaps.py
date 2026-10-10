"""
[INPUT]: 依赖 execute_read 有限重试与 Search Console service 的 sitemaps().list()/get() 能力
[OUTPUT]: 对外提供 list_sitemaps 与 get_sitemap
[POS]: gsc 的 sitemap 读取器，负责 sitemap 元数据查询
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from .request import execute_read


def list_sitemaps(service, *, property_uri: str) -> list[dict[str, object]]:
    response = execute_read(service.sitemaps().list(siteUrl=property_uri))
    return list(response.get("sitemap", []))


def get_sitemap(service, *, property_uri: str, sitemap_url: str) -> dict[str, object]:
    return execute_read(service.sitemaps().get(siteUrl=property_uri, feedpath=sitemap_url))
