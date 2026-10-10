"""
[INPUT]: 依赖公共筛选、多站对比、搜索类型对比和本站 CTR 模块
[OUTPUT]: 验证过滤一致、部分失败、缺失侧及留一页面基准
[POS]: tests 的扩展分析回归；以可手算样本校验计算口径
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
import asyncio
import json
import re

import pytest
from mcp.server.fastmcp import FastMCP

from google_search_console_mcp import analysis, portfolio_analysis, ctr_benchmark
from google_search_console_mcp.gsc.filters import build_filter_groups
from google_search_console_mcp.errors import AuthorizationError
from google_search_console_mcp.config import Settings
from google_search_console_mcp.tools.read_tools import ReadToolService
from google_search_console_mcp.tools.analysis_tools import register_analysis_tools
from test_query_integrity import PagedService, ARGS, raw


FILTERS = dict(country="USA", device="mobile", page_prefix="/blog/", query_include="shoe|boot", query_exclude="brand")


def test_filter_groups_share_and_semantics_and_path_not_query():
    group = build_filter_groups(FILTERS)[0]
    assert group["groupType"] == "and"
    assert group["filters"][0]["expression"] == "usa"
    assert group["filters"][1]["expression"] == "MOBILE"
    pattern = group["filters"][2]["expression"]
    assert re.search(pattern, "https://example.com/blog/a")
    assert not re.search(pattern, "https://example.com/?next=/blog/a")
    assert not re.search(pattern, "https://example.com?next=/blog/a")


@pytest.mark.parametrize("name,params", [
    ("compare_periods", ARGS), ("find_ctr_opportunities", ARGS), ("get_query_overlap", ARGS),
    ("find_declining_pages", {"property_uri": ARGS["property_uri"], "end_date": "2026-09-30"}),
])
def test_all_existing_analyses_propagate_filters_to_every_window(name, params):
    service = PagedService([])
    getattr(analysis, name)(service, **params, filters=FILTERS)
    assert service.calls
    assert all(call["dimensionFilterGroups"] == build_filter_groups(FILTERS) for call in service.calls)


class MultiService(PagedService):
    def query(self, *, siteUrl, body):
        if siteUrl == "sc-domain:denied.com":
            raise AuthorizationError("forbidden")
        self.site = siteUrl
        return super().query(siteUrl=siteUrl, body=body)

    def execute(self):
        current = self.body["endDate"] == ARGS["end_date"]
        clicks = (10 if current else 100) if self.site == "sc-domain:loss.com" else (200 if current else 100)
        self.rows = [raw("ignored", clicks, 1000)]
        return super().execute()


def test_multi_site_keeps_error_deduplicates_and_orders_losses_first():
    service = MultiService([])
    result = portfolio_analysis.get_multi_site_summary(service,
        property_uris=["sc-domain:gain.com", "sc-domain:denied.com", "sc-domain:loss.com", "sc-domain:loss.com"],
        start_date=ARGS["start_date"], end_date=ARGS["end_date"])
    assert [item["property_uri"] for item in result["items"]] == ["sc-domain:loss.com", "sc-domain:gain.com", "sc-domain:denied.com"]
    assert result["items"][0]["click_change"] == -90
    assert result["meta"]["error_count"] == 1
    assert result["meta"]["unique_count"] == 3
    assert all(call["dimensions"] == [] for call in service.calls)


class SurfaceService(PagedService):
    def execute(self):
        self.rows = [raw("shared"), raw("web_only")] if self.body["type"] == "web" else [raw("shared"), raw("image_only")]
        return super().execute()


def test_search_types_preserve_missing_sides():
    result = portfolio_analysis.compare_search_types(SurfaceService([]), **ARGS)
    items = {item["entity"]: item for item in result["items"]}
    assert items["shared"]["status"] == "both"
    assert items["web_only"]["image"] is None
    assert items["image_only"]["web"] is None


def sample(page, query, clicks, impressions, position):
    return {**raw(page, clicks, impressions), "keys": [page, query], "position": position}


def test_ctr_excludes_target_uses_weighted_ratios_and_target_mix():
    rows = [sample("target", "t1", 9, 100, 2), sample("target", "t2", 3, 300, 5),
            sample("peer1", "q1", 10, 100, 2), sample("peer2", "q2", 90, 900, 2),
            sample("peer1", "q1", 20, 1000, 5), sample("peer2", "q3", 0, 1000, 5)]
    result = ctr_benchmark.benchmark_page_ctr(PagedService(rows), **ARGS, page="target",
        min_reference_impressions=100, min_reference_queries=2, min_reference_pages=2)
    item = result["items"][0]
    assert item["actual_ctr"] == pytest.approx(12 / 400)
    assert item["benchmark_ctr"] == pytest.approx((0.1 * 100 + 0.01 * 300) / 400)
    assert item["buckets"][0]["reference_impressions"] == 1000
    assert item["buckets"][1]["reference_ctr"] == 0.01
    assert all(bucket["reference_pages"] == 2 for bucket in item["buckets"])


def test_ctr_does_not_fallback_when_peers_insufficient():
    rows = [sample("target", "q", 20, 100, 2)]
    item = ctr_benchmark.benchmark_page_ctr(PagedService(rows), **ARGS)["items"][0]
    assert item["status"] == "insufficient_sample"
    assert item["benchmark_ctr"] is None
    assert item["ctr_gap"] is None
    assert item["buckets"][0]["reference_queries"] == 0


def test_ctr_shared_queries_remain_in_reference_and_partial_buckets_do_not_make_full_baseline():
    rows = [sample("target", "shared", 1, 100, 2), sample("peer", "shared", 2, 100, 2),
            sample("target", "alone", 1, 100, 15)]
    item = ctr_benchmark.benchmark_page_ctr(PagedService(rows), **ARGS, page="target",
        min_reference_impressions=1, min_reference_queries=1, min_reference_pages=1)["items"][0]
    assert item["buckets"][0]["reference_queries"] == 1
    assert item["benchmark_ctr"] is None
    assert item["reference_coverage_ratio"] == 0.5


def test_all_seven_analysis_tools_work_through_mcp_with_nested_filters():
    service = PagedService([])
    mcp = FastMCP("test")
    register_analysis_tools(mcp, read_service=ReadToolService(Settings(), service_factory=lambda **kw: service))
    async def run():
        assert len(await mcp.list_tools()) == 7
        for name, args in [("compare_periods", ARGS), ("find_ctr_opportunities", ARGS), ("get_query_overlap", ARGS),
            ("find_declining_pages", {"property_uri": ARGS["property_uri"], "end_date": "2026-09-30"}),
            ("compare_search_types", ARGS), ("benchmark_page_ctr", ARGS),
            ("get_multi_site_summary", {"property_uris": [ARGS["property_uri"]], "start_date": ARGS["start_date"], "end_date": ARGS["end_date"]})]:
            blocks = await mcp.call_tool(name, {**args, "filters": FILTERS})
            if isinstance(blocks, tuple): blocks = blocks[0]
            assert "meta" in json.loads(blocks[0].text)
    asyncio.run(run())
    assert all(call["dimensionFilterGroups"] == build_filter_groups(FILTERS) for call in service.calls)


def test_multi_site_preserves_other_results_after_transport_failure(monkeypatch):
    from google_search_console_mcp.gsc.request import execute_read
    from test_protocol_contracts import Request
    original = portfolio_analysis.compare_periods
    def with_failure(service, **kwargs):
        if kwargs["property_uri"] == "sc-domain:offline.com":
            return execute_read(Request([TimeoutError() for _ in range(3)]))
        return original(service, **kwargs)
    monkeypatch.setattr("google_search_console_mcp.gsc.request.time.sleep", lambda _: None)
    monkeypatch.setattr(portfolio_analysis, "compare_periods", with_failure)
    result = portfolio_analysis.get_multi_site_summary(MultiService([]),
        property_uris=["sc-domain:offline.com", "sc-domain:loss.com"],
        start_date=ARGS["start_date"], end_date=ARGS["end_date"])
    assert result["meta"]["error_count"] == 1
    assert result["items"][0]["click_change"] == -90
    assert result["items"][1]["error_type"] == "UpstreamApiError"
