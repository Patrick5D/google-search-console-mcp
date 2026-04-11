"""
[INPUT]: 依赖认证状态、GSC service 构造器与各读取子模块
[OUTPUT]: 对外提供 ReadToolService、build_read_tool_names 与 register_read_tools
[POS]: tools 的只读装配器，把底层读取能力折叠成稳定 MCP 工具接口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..auth import get_auth_status
from ..config import Settings
from ..gsc.client import build_search_console_service
from ..gsc.inspection import inspect_url
from ..gsc.performance import get_site_daily_summary, query_search_analytics
from ..gsc.sitemaps import get_sitemap, list_sitemaps
from ..gsc.sites import get_property, list_properties


def build_read_tool_names() -> list[str]:
    return [
        "get_account_status",
        "list_properties",
        "get_property",
        "query_search_analytics",
        "get_site_daily_summary",
        "inspect_url",
        "list_sitemaps",
        "get_sitemap",
    ]


@dataclass
class ReadToolService:
    settings: Settings
    service_factory: Callable[..., object] = build_search_console_service

    def get_account_status(self):
        return get_auth_status(
            client_path=self.settings.paths.oauth_client_path,
            token_path=self.settings.paths.token_path,
        ).model_dump()

    def _service(self):
        return self.service_factory(
            token_path=self.settings.paths.token_path,
            client_path=self.settings.paths.oauth_client_path,
        )

    def list_properties(self):
        return list_properties(self._service())

    def get_property(self, property_uri: str):
        return get_property(self._service(), property_uri)

    def query_search_analytics(self, **kwargs):
        return query_search_analytics(self._service(), **kwargs)

    def get_site_daily_summary(self, **kwargs):
        return get_site_daily_summary(self._service(), **kwargs)

    def inspect_url(self, **kwargs):
        return inspect_url(self._service(), **kwargs)

    def list_sitemaps(self, **kwargs):
        return list_sitemaps(self._service(), **kwargs)

    def get_sitemap(self, **kwargs):
        return get_sitemap(self._service(), **kwargs)


def register_read_tools(mcp, *, read_service: ReadToolService):
    @mcp.tool(name="get_account_status")
    def _get_account_status():
        return read_service.get_account_status()

    @mcp.tool(name="list_properties")
    def _list_properties():
        return read_service.list_properties()

    @mcp.tool(name="get_property")
    def _get_property(property_uri: str):
        return read_service.get_property(property_uri)

    @mcp.tool(name="query_search_analytics")
    def _query_search_analytics(
        property_uri: str,
        start_date: str,
        end_date: str,
        dimensions: list[str] | None = None,
        row_limit: int = 1000,
        start_row: int = 0,
        dimension_filter_groups: list[dict[str, object]] | None = None,
        search_type: str = "web",
        data_state: str | None = None,
        aggregation_type: str | None = None,
    ):
        return read_service.query_search_analytics(
            property_uri=property_uri,
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions,
            row_limit=row_limit,
            start_row=start_row,
            dimension_filter_groups=dimension_filter_groups,
            search_type=search_type,
            data_state=data_state,
            aggregation_type=aggregation_type,
        )

    @mcp.tool(name="get_site_daily_summary")
    def _get_site_daily_summary(
        property_uri: str,
        start_date: str,
        end_date: str,
        search_type: str = "web",
    ):
        return read_service.get_site_daily_summary(
            property_uri=property_uri,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
        )

    @mcp.tool(name="inspect_url")
    def _inspect_url(property_uri: str, inspection_url: str):
        return read_service.inspect_url(property_uri=property_uri, inspection_url=inspection_url)

    @mcp.tool(name="list_sitemaps")
    def _list_sitemaps(property_uri: str):
        return read_service.list_sitemaps(property_uri=property_uri)

    @mcp.tool(name="get_sitemap")
    def _get_sitemap(property_uri: str, sitemap_url: str):
        return read_service.get_sitemap(property_uri=property_uri, sitemap_url=sitemap_url)
