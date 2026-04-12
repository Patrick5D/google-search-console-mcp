"""
[INPUT]: 依赖认证状态、GSC service 构造器与各读取子模块
[OUTPUT]: 对外提供 ReadToolService、build_read_tool_names 与 register_read_tools
[POS]: tools 的只读装配器，把底层读取能力折叠成稳定 MCP 工具接口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Callable

from ..audit import AuditLogger
from ..auth import get_auth_status
from ..config import Settings
from ..gsc.client import build_search_console_service
from ..gsc.inspection import inspect_url, inspect_urls_batch
from ..gsc.performance import (
    get_page_queries,
    get_page_query_pairs,
    get_page_trend,
    get_pages_by_path_prefix,
    get_query_pages,
    get_query_page_pairs,
    get_query_trend,
    get_site_daily_summary,
    get_site_summary_by_country,
    get_site_summary_by_device,
    get_top_pages,
    get_top_queries,
    query_search_analytics,
)
from ..gsc.sitemaps import get_sitemap, list_sitemaps
from ..gsc.sites import get_property, list_properties


def build_read_tool_names() -> list[str]:
    return [
        "get_account_status",
        "list_properties",
        "get_property",
        "query_search_analytics",
        "get_site_daily_summary",
        "get_site_summary_by_device",
        "get_site_summary_by_country",
        "get_top_pages",
        "get_page_trend",
        "get_pages_by_path_prefix",
        "get_page_queries",
        "get_page_query_pairs",
        "get_top_queries",
        "get_query_trend",
        "get_query_pages",
        "get_query_page_pairs",
        "inspect_url",
        "inspect_urls_batch",
        "list_sitemaps",
        "get_sitemap",
    ]


@dataclass
class ReadToolService:
    settings: Settings
    service_factory: Callable[..., object] = build_search_console_service
    audit_logger: AuditLogger | None = None

    def _audit(self, *, tool_name: str, status: str, args_summary: dict[str, object], error_type: str | None = None):
        if self.audit_logger is None:
            return
        record: dict[str, object] = {
            "tool_name": tool_name,
            "status": status,
            "args_summary": args_summary,
        }
        if error_type is not None:
            record["error_type"] = error_type
        self.audit_logger.log(record)

    def _run(self, tool_name: str, args_summary: dict[str, object], fn: Callable[[], Any]):
        try:
            result = fn()
        except Exception as exc:
            self._audit(tool_name=tool_name, status="error", args_summary=args_summary, error_type=type(exc).__name__)
            raise
        self._audit(tool_name=tool_name, status="ok", args_summary=args_summary)
        return result

    def get_account_status(self):
        return self._run(
            "get_account_status",
            {},
            lambda: get_auth_status(
                client_path=self.settings.paths.oauth_client_path,
                token_path=self.settings.paths.token_path,
            ).model_dump(),
        )

    def _service(self):
        return self.service_factory(
            token_path=self.settings.paths.token_path,
            client_path=self.settings.paths.oauth_client_path,
        )

    def list_properties(self):
        return self._run("list_properties", {}, lambda: list_properties(self._service()))

    def get_property(self, property_uri: str):
        return self._run("get_property", {"property_uri": property_uri}, lambda: get_property(self._service(), property_uri))

    def query_search_analytics(self, **kwargs):
        return self._run("query_search_analytics", kwargs, lambda: query_search_analytics(self._service(), **kwargs))

    def get_site_daily_summary(self, **kwargs):
        return self._run("get_site_daily_summary", kwargs, lambda: get_site_daily_summary(self._service(), **kwargs))

    def get_site_summary_by_device(self, **kwargs):
        return self._run("get_site_summary_by_device", kwargs, lambda: get_site_summary_by_device(self._service(), **kwargs))

    def get_site_summary_by_country(self, **kwargs):
        return self._run("get_site_summary_by_country", kwargs, lambda: get_site_summary_by_country(self._service(), **kwargs))

    def get_top_pages(self, **kwargs):
        return self._run("get_top_pages", kwargs, lambda: get_top_pages(self._service(), **kwargs))

    def get_page_trend(self, **kwargs):
        return self._run("get_page_trend", kwargs, lambda: get_page_trend(self._service(), **kwargs))

    def get_pages_by_path_prefix(self, **kwargs):
        return self._run("get_pages_by_path_prefix", kwargs, lambda: get_pages_by_path_prefix(self._service(), **kwargs))

    def get_page_queries(self, **kwargs):
        return self._run("get_page_queries", kwargs, lambda: get_page_queries(self._service(), **kwargs))

    def get_page_query_pairs(self, **kwargs):
        return self._run("get_page_query_pairs", kwargs, lambda: get_page_query_pairs(self._service(), **kwargs))

    def get_top_queries(self, **kwargs):
        return self._run("get_top_queries", kwargs, lambda: get_top_queries(self._service(), **kwargs))

    def get_query_trend(self, **kwargs):
        return self._run("get_query_trend", kwargs, lambda: get_query_trend(self._service(), **kwargs))

    def get_query_pages(self, **kwargs):
        return self._run("get_query_pages", kwargs, lambda: get_query_pages(self._service(), **kwargs))

    def get_query_page_pairs(self, **kwargs):
        return self._run("get_query_page_pairs", kwargs, lambda: get_query_page_pairs(self._service(), **kwargs))

    def inspect_url(self, **kwargs):
        return self._run("inspect_url", kwargs, lambda: inspect_url(self._service(), **kwargs))

    def inspect_urls_batch(self, **kwargs):
        return self._run("inspect_urls_batch", kwargs, lambda: inspect_urls_batch(self._service(), **kwargs))

    def list_sitemaps(self, **kwargs):
        return self._run("list_sitemaps", kwargs, lambda: list_sitemaps(self._service(), **kwargs))

    def get_sitemap(self, **kwargs):
        return self._run("get_sitemap", kwargs, lambda: get_sitemap(self._service(), **kwargs))


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

    @mcp.tool(name="get_site_summary_by_device")
    def _get_site_summary_by_device(
        property_uri: str,
        start_date: str,
        end_date: str,
        search_type: str = "web",
        row_limit: int = 10,
        start_row: int = 0,
    ):
        return read_service.get_site_summary_by_device(
            property_uri=property_uri,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
            row_limit=row_limit,
            start_row=start_row,
        )

    @mcp.tool(name="get_site_summary_by_country")
    def _get_site_summary_by_country(
        property_uri: str,
        start_date: str,
        end_date: str,
        search_type: str = "web",
        row_limit: int = 50,
        start_row: int = 0,
    ):
        return read_service.get_site_summary_by_country(
            property_uri=property_uri,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
            row_limit=row_limit,
            start_row=start_row,
        )

    @mcp.tool(name="get_top_pages")
    def _get_top_pages(
        property_uri: str,
        start_date: str,
        end_date: str,
        metric: str = "clicks",
        search_type: str = "web",
        row_limit: int = 50,
        start_row: int = 0,
    ):
        return read_service.get_top_pages(
            property_uri=property_uri,
            start_date=start_date,
            end_date=end_date,
            metric=metric,
            search_type=search_type,
            row_limit=row_limit,
            start_row=start_row,
        )

    @mcp.tool(name="get_page_trend")
    def _get_page_trend(
        property_uri: str,
        page: str,
        start_date: str,
        end_date: str,
        search_type: str = "web",
    ):
        return read_service.get_page_trend(
            property_uri=property_uri,
            page=page,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
        )

    @mcp.tool(name="get_pages_by_path_prefix")
    def _get_pages_by_path_prefix(
        property_uri: str,
        path_prefix: str,
        start_date: str,
        end_date: str,
        metric: str = "clicks",
        search_type: str = "web",
        row_limit: int = 100,
        start_row: int = 0,
    ):
        return read_service.get_pages_by_path_prefix(
            property_uri=property_uri,
            path_prefix=path_prefix,
            start_date=start_date,
            end_date=end_date,
            metric=metric,
            search_type=search_type,
            row_limit=row_limit,
            start_row=start_row,
        )

    @mcp.tool(name="get_page_queries")
    def _get_page_queries(
        property_uri: str,
        page: str,
        start_date: str,
        end_date: str,
        metric: str = "clicks",
        search_type: str = "web",
        row_limit: int = 100,
        start_row: int = 0,
    ):
        return read_service.get_page_queries(
            property_uri=property_uri,
            page=page,
            start_date=start_date,
            end_date=end_date,
            metric=metric,
            search_type=search_type,
            row_limit=row_limit,
            start_row=start_row,
        )

    @mcp.tool(name="get_page_query_pairs")
    def _get_page_query_pairs(
        property_uri: str,
        page: str,
        start_date: str,
        end_date: str,
        search_type: str = "web",
        row_limit: int = 200,
        start_row: int = 0,
    ):
        return read_service.get_page_query_pairs(
            property_uri=property_uri,
            page=page,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
            row_limit=row_limit,
            start_row=start_row,
        )

    @mcp.tool(name="get_top_queries")
    def _get_top_queries(
        property_uri: str,
        start_date: str,
        end_date: str,
        metric: str = "clicks",
        search_type: str = "web",
        row_limit: int = 100,
        start_row: int = 0,
    ):
        return read_service.get_top_queries(
            property_uri=property_uri,
            start_date=start_date,
            end_date=end_date,
            metric=metric,
            search_type=search_type,
            row_limit=row_limit,
            start_row=start_row,
        )

    @mcp.tool(name="get_query_trend")
    def _get_query_trend(
        property_uri: str,
        query: str,
        start_date: str,
        end_date: str,
        search_type: str = "web",
    ):
        return read_service.get_query_trend(
            property_uri=property_uri,
            query=query,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
        )

    @mcp.tool(name="get_query_pages")
    def _get_query_pages(
        property_uri: str,
        query: str,
        start_date: str,
        end_date: str,
        metric: str = "clicks",
        search_type: str = "web",
        row_limit: int = 100,
        start_row: int = 0,
    ):
        return read_service.get_query_pages(
            property_uri=property_uri,
            query=query,
            start_date=start_date,
            end_date=end_date,
            metric=metric,
            search_type=search_type,
            row_limit=row_limit,
            start_row=start_row,
        )

    @mcp.tool(name="get_query_page_pairs")
    def _get_query_page_pairs(
        property_uri: str,
        query: str,
        start_date: str,
        end_date: str,
        search_type: str = "web",
        row_limit: int = 200,
        start_row: int = 0,
    ):
        return read_service.get_query_page_pairs(
            property_uri=property_uri,
            query=query,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
            row_limit=row_limit,
            start_row=start_row,
        )

    @mcp.tool(name="inspect_url")
    def _inspect_url(property_uri: str, inspection_url: str):
        return read_service.inspect_url(property_uri=property_uri, inspection_url=inspection_url)

    @mcp.tool(name="inspect_urls_batch")
    def _inspect_urls_batch(
        property_uri: str,
        inspection_urls: list[str],
        stop_on_error: bool = False,
    ):
        return read_service.inspect_urls_batch(
            property_uri=property_uri,
            inspection_urls=inspection_urls,
            stop_on_error=stop_on_error,
        )

    @mcp.tool(name="list_sitemaps")
    def _list_sitemaps(property_uri: str):
        return read_service.list_sitemaps(property_uri=property_uri)

    @mcp.tool(name="get_sitemap")
    def _get_sitemap(property_uri: str, sitemap_url: str):
        return read_service.get_sitemap(property_uri=property_uri, sitemap_url=sitemap_url)
