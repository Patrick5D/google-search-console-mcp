"""
[INPUT]: 依赖未来的 google_search_console_mcp.tools.read_tools 模块
[OUTPUT]: 对外提供只读工具清单测试
[POS]: tests 的工具层入口，先锁定对外协议名称
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from google_search_console_mcp.tools.read_tools import build_read_tool_names


def test_build_read_tool_names_matches_design() -> None:
    assert build_read_tool_names() == [
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
