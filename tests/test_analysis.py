"""
[INPUT]: 依赖确定性分析函数、MCP 装配与按日期分组的模拟 API
[OUTPUT]: 验证等长周期、缺失行、阈值、持续下降与重叠解释
[POS]: tests 的分析回归；用已知数据约束观测结论和协议调用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
import asyncio
import json

from mcp.server.fastmcp import FastMCP

from google_search_console_mcp import analysis
from google_search_console_mcp.config import Settings
from google_search_console_mcp.tools.analysis_tools import register_analysis_tools
from google_search_console_mcp.tools.read_tools import ReadToolService
from test_query_integrity import PagedService, raw, ARGS


class WindowService(PagedService):
    def __init__(self, windows):
        super().__init__([])
        self.windows = windows

    def execute(self):
        self.rows = self.windows.get(self.body["endDate"], [])
        return super().execute()


def test_compare_uses_equal_windows_and_does_not_invent_missing_values():
    service = WindowService({
        "2026-08-31": [raw("both", 10), raw("missing_now", 20), raw("zero", 0)],
        "2026-09-30": [raw("both", 5), raw("new", 5), raw("zero", 5)],
    })
    result = analysis.compare_periods(service, **ARGS)
    assert service.calls[0]["startDate"] == "2026-08-02"
    items = {item["entity"]: item for item in result["items"]}
    assert items["both"]["click_change"] == -5
    assert items["both"]["click_change_ratio"] == -0.5
    assert items["zero"]["click_change_ratio"] is None
    assert items["missing_now"]["current"] is None
    assert "click_change" not in items["missing_now"]
    assert items["new"]["status"] == "not_returned_previous"


def test_site_comparison_queries_totals_instead_of_summing_query_rows():
    service = WindowService({"2026-08-31": [raw("ignored", 10)], "2026-09-30": [raw("ignored", 20)]})
    result = analysis.compare_periods(service, **ARGS, dimension="site")
    assert all(call["dimensions"] == [] for call in service.calls)
    assert result["items"][0]["click_change"] == 10


def test_ctr_candidates_use_ratio_threshold_and_minimum_volume():
    service = PagedService([raw("candidate", 1, 1000), raw("small", 0, 10), raw("good", 80, 1000)])
    result = analysis.find_ctr_opportunities(service, **ARGS, max_ctr=0.02, min_impressions=100)
    assert [row["page"] for row in result["items"]] == ["candidate"]
    assert result["meta"]["thresholds"]["max_ctr"] == 0.02


def test_decline_requires_three_present_monotonic_periods():
    service = WindowService({
        "2026-09-10": [raw("decline", 100), raw("recovery", 100), raw("missing", 100)],
        "2026-09-20": [raw("decline", 70), raw("recovery", 60)],
        "2026-09-30": [raw("decline", 40), raw("recovery", 80), raw("missing", 1)],
    })
    result = analysis.find_declining_pages(service, property_uri=ARGS["property_uri"], end_date="2026-09-30", period_days=10)
    assert len(result["items"]) == 1
    assert result["items"][0]["page"] == "decline"
    assert result["items"][0]["decline_ratio"] == 0.6
    assert result["meta"]["excluded_missing_period_pages"] == 1
    assert result["meta"]["windows"][0] == {"start_date": "2026-09-01", "end_date": "2026-09-10"}


def test_overlap_returns_per_page_evidence_without_claiming_cannibalization():
    rows = [dict(raw("unused", 2, impressions), keys=[query, page]) for query, page, impressions in
            [("shared", "a", 100), ("shared", "b", 200), ("single", "c", 100), ("single", "d", 5)]]
    result = analysis.get_query_overlap(PagedService(rows), **ARGS)
    assert len(result["items"]) == 1
    assert result["items"][0]["query"] == "shared"
    assert result["items"][0]["summed_page_impressions"] == 300
    assert len(result["items"][0]["pages"]) == 2
    assert "not proof" in result["meta"]["interpretation"]


def test_analysis_tools_work_through_mcp_and_share_audit(tmp_path):
    from google_search_console_mcp.audit import AuditLogger
    service = WindowService({"2026-09-30": [raw("page", 1, 1000)]})
    mcp = FastMCP("analysis-test")
    register_analysis_tools(mcp, read_service=ReadToolService(
        Settings(), service_factory=lambda **kw: service, audit_logger=AuditLogger(tmp_path / "audit.jsonl")))
    async def run():
        for name, params in [
            ("compare_periods", ARGS), ("find_ctr_opportunities", ARGS),
            ("find_declining_pages", {"property_uri": ARGS["property_uri"], "end_date": "2026-09-30"}),
            ("get_query_overlap", ARGS),
        ]:
            blocks = await mcp.call_tool(name, params)
            if isinstance(blocks, tuple):
                blocks = blocks[0]
            result = json.loads(blocks[0].text)
            assert "sources" in result["meta"]
            assert "items" in result
    asyncio.run(run())
    entries = [json.loads(line) for line in (tmp_path / "audit.jsonl").read_text().splitlines()]
    assert len(entries) == 4
    assert all(entry["status"] == "ok" for entry in entries)
