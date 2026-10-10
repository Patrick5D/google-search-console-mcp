"""
[INPUT]: 依赖分页查询、模板排序与快照服务
[OUTPUT]: 验证跨页候选、取数上限、响应元信息与快照隔离
[POS]: tests 的数据完整性回归，使用模拟 API 而非真实账号
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from pathlib import Path

from google_search_console_mcp.gsc.performance import get_top_pages, get_pages_by_path_prefix
from google_search_console_mcp.gsc.query import query_search_analytics
from google_search_console_mcp.snapshots.csv_writer import write_site_day_snapshot, read_snapshot_rows, list_snapshot_files

ARGS = dict(property_uri="sc-domain:example.com", start_date="2026-09-01", end_date="2026-09-30")


class PagedService:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def searchanalytics(self):
        return self

    def query(self, *, siteUrl, body):
        self.calls.append(body)
        self.body = body
        return self

    def execute(self):
        start = self.body["startRow"]
        return {"rows": self.rows[start:start + self.body["rowLimit"]],
                "responseAggregationType": "byPage", "metadata": {"first_incomplete_date": "2026-09-30"}}


def raw(page, clicks=10, impressions=100):
    return {"keys": [page], "clicks": clicks, "impressions": impressions, "ctr": clicks / impressions, "position": 5}


def test_top_impressions_and_prefix_find_candidates_after_first_api_page():
    rows = [raw(f"https://example.com/{i}") for i in range(25000)]
    rows.append(raw("https://example.com/blog/winner", 1, 1000000))
    for fn, extra in [(get_top_pages, {}), (get_pages_by_path_prefix, {"path_prefix": "/blog/"})]:
        service = PagedService(rows)
        result = fn(service, **ARGS, **extra, metric="impressions", row_limit=1)
        assert result[0]["page"] == "https://example.com/blog/winner"
        assert [c["startRow"] for c in service.calls] == [0, 25000]
        assert result.meta["pagination_complete"]
        assert result.meta["fetched_rows"] == 25001


def test_bounded_pagination_reports_truncation_and_keeps_api_metadata():
    result = query_search_analytics(PagedService([raw(str(i)) for i in range(5)]),
                                   **ARGS, dimensions=["page"], fetch_all=True, max_rows=3, data_state="all")
    assert len(result) == 3
    assert result.meta["truncated"]
    assert result.meta["next_start_row"] == 3
    assert result.meta["api_metadata"][0]["first_incomplete_date"] == "2026-09-30"
    assert result.meta["response_aggregation_types"] == ["byPage"]
    assert not result.meta["pagination_complete"]


def test_exact_cap_probe_distinguishes_complete_from_truncated():
    result = query_search_analytics(PagedService([raw("a"), raw("b")]), **ARGS, fetch_all=True, max_rows=2)
    assert result.meta["pagination_complete"]
    assert not result.meta["truncated"]


def test_search_type_snapshots_coexist_and_legacy_files_remain_readable(tmp_path):
    paths = []
    for search_type, clicks in [("web", 10), ("image", 2)]:
        paths.append(write_site_day_snapshot(snapshot_root=tmp_path, property_uri=ARGS["property_uri"],
                     date="2026-09-01", row={"search_type": search_type, "clicks": clicks}))
    assert paths[0] != paths[1]
    assert [read_snapshot_rows(p)[0]["clicks"] for p in paths] == ["10", "2"]
    legacy = paths[0].parent.parent / "2026-08-31.csv"
    legacy.write_text("clicks\n7\n")
    assert set(list_snapshot_files(tmp_path, ARGS["property_uri"])) == {*paths, legacy}
