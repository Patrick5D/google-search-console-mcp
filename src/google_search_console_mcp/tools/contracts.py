"""
[INPUT]: 依赖 Pydantic 参数约束与 QueryRows 元信息
[OUTPUT]: 提供分页参数类型、工具说明与 MCP 结果转换
[POS]: tools 的协议契约；内部列表兼容，MCP 查询输出 rows/meta
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from typing import Annotated

from pydantic import Field

from ..gsc.query import QueryRows

RowLimit = Annotated[int, Field(ge=1, le=25000, description="Maximum returned rows, 1..25000.")]
StartRow = Annotated[int, Field(ge=0, description="Zero-based row offset.")]
MaxRows = Annotated[int, Field(ge=1, le=1000000, description="Automatic pagination budget; truncation is reported.")]

QUERY_NOTE = (
    " Returns {rows, meta}. Dates are inclusive YYYY-MM-DD in America/Los_Angeles. "
    "CTR is a 0..1 ratio; average_position is impression-weighted, not a rank-tracker rank. "
    "Default data is finalized. Missing rows are not proof of zero traffic or deindexing. "
    "Read meta.truncated, pagination_complete and api_metadata before interpreting coverage. "
    "Google omits some rows, including anonymized queries; even exhausted pagination is not a complete keyword inventory."
)
TOP_NOTE = " Fetches at most 100000 API rows before sorting; ranking covers that fetched set. start_row is an offset in the locally sorted result."
DESCRIPTIONS = {
    "get_account_status": "Inspect local OAuth file readiness without a live Google access check; ready does not prove access to any property.",
    "list_properties": "List Search Console properties accessible to the authenticated account and their permission levels.",
    "get_property": "Look up an exact sc-domain: or URL-prefix property in the account's accessible properties.",
    "query_search_analytics": "Run a custom Search Analytics query with AND filters. Default returns one API page; fetch_all enables bounded automatic pagination. start_row offsets API rows; max_rows caps automatic fetches." + QUERY_NOTE,
    "get_site_daily_summary": "Return daily site totals for the inclusive date window." + QUERY_NOTE,
    "get_site_summary_by_device": "Return site metrics grouped by device; row_limit/start_row page through API results." + QUERY_NOTE,
    "get_site_summary_by_country": "Return site metrics grouped by country; row_limit/start_row page through API results." + QUERY_NOTE,
    "get_top_pages": "Rank pages by clicks, impressions, CTR or average_position (ascending for position)." + TOP_NOTE + QUERY_NOTE,
    "get_page_trend": "Return daily metrics for one exact canonical page URL." + QUERY_NOTE,
    "get_pages_by_path_prefix": "Rank pages whose URL path starts with path_prefix; the query string is excluded from matching." + TOP_NOTE + QUERY_NOTE,
    "get_page_queries": "Rank query rows for one exact canonical page URL." + TOP_NOTE + QUERY_NOTE,
    "get_page_query_pairs": "Return one API page of page/query pairs filtered to one exact page URL." + QUERY_NOTE,
    "get_top_queries": "Rank query rows by the requested metric; average_position sorts ascending." + TOP_NOTE + QUERY_NOTE,
    "get_query_trend": "Return daily metrics for one exact search query." + QUERY_NOTE,
    "get_query_pages": "Rank pages for one exact search query." + TOP_NOTE + QUERY_NOTE,
    "get_query_page_pairs": "Return one API page of query/page pairs for one exact query." + QUERY_NOTE,
    "inspect_url": "Read Google's indexed-version inspection for a URL within a property. This is not a live crawl or an indexing request.",
    "inspect_urls_batch": "Inspect up to 50 URLs sequentially. Return successes, errors and processed counts. Stop on exhausted quota; stop_on_error also stops on other errors. Unprocessed URLs have no result.",
    "list_sitemaps": "List sitemaps and their Google-reported status for a property; this does not submit or refresh sitemaps.",
    "get_sitemap": "Read Google-reported metadata for one sitemap URL; this does not crawl the sitemap or prove page indexing.",
    "snapshot_site_day": "Save finalized site totals for one PT date as CSV. Identity is property/search_type/date; repeating the same identity replaces that snapshot. CTR is a ratio. Empty API data raises an error rather than fabricating zeros.",
    "list_snapshots": "List local CSV snapshots, including legacy paths; optionally restrict to a property. Old snapshots can be stale.",
    "read_snapshot": "Read an existing CSV within the configured snapshot root. Fields are CSV strings; check captured_at_utc and search_type before use.",
}


def tool_result(value):
    return value.as_result() if isinstance(value, QueryRows) else value
