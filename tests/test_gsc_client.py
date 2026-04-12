"""
[INPUT]: 依赖 google_search_console_mcp.gsc.performance 与 inspection 模块
[OUTPUT]: 对外提供 Search Analytics 模板查询与 batch inspection 回归测试
[POS]: tests 的 GSC API 包装层入口，锁定模板查询、排序语义与 inspection 合同
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from google_search_console_mcp.errors import ValidationError
from google_search_console_mcp.gsc.inspection import inspect_urls_batch
from google_search_console_mcp.gsc.performance import (
    get_page_queries,
    get_pages_by_path_prefix,
    get_query_trend,
    normalize_search_analytics_row,
    sort_rows_by_metric,
)


def test_normalize_search_analytics_row_flattens_metrics() -> None:
    row = {
        "keys": ["2026-04-10"],
        "clicks": 10,
        "impressions": 100,
        "ctr": 0.1,
        "position": 3.2,
    }

    result = normalize_search_analytics_row(["date"], row)

    assert result["date"] == "2026-04-10"
    assert result["clicks"] == 10
    assert result["average_position"] == 3.2


def test_sort_rows_by_metric_uses_ascending_for_average_position() -> None:
    rows = [
        {"page": "/a", "average_position": 20.0, "clicks": 1},
        {"page": "/b", "average_position": 5.0, "clicks": 9},
        {"page": "/c", "average_position": 11.0, "clicks": 3},
    ]

    result = sort_rows_by_metric(rows, "average_position")

    assert [row["page"] for row in result] == ["/b", "/c", "/a"]


def test_get_pages_by_path_prefix_filters_by_url_path_not_query_string() -> None:
    service = FakeSearchAnalyticsService(
        rows=[
            {"keys": ["https://example.com/blog/post-1"], "clicks": 8, "impressions": 80, "ctr": 0.1, "position": 4},
            {"keys": ["https://example.com/tools/page"], "clicks": 5, "impressions": 50, "ctr": 0.1, "position": 6},
            {
                "keys": ["https://example.com/not-blog/?redirect=/blog/post-2"],
                "clicks": 100,
                "impressions": 1000,
                "ctr": 0.1,
                "position": 1,
            },
        ]
    )

    result = get_pages_by_path_prefix(
        service,
        property_uri="sc-domain:example.com",
        path_prefix="/blog/",
        start_date="2026-04-01",
        end_date="2026-04-07",
    )

    assert [row["page"] for row in result] == ["https://example.com/blog/post-1"]


def test_get_query_trend_builds_exact_query_filter() -> None:
    service = FakeSearchAnalyticsService(
        rows=[
            {"keys": ["2026-04-01"], "clicks": 4, "impressions": 40, "ctr": 0.1, "position": 7},
        ]
    )

    get_query_trend(
        service,
        property_uri="sc-domain:example.com",
        query="best shaver",
        start_date="2026-04-01",
        end_date="2026-04-07",
    )

    assert service.last_body["dimensions"] == ["date"]
    assert service.last_body["dimensionFilterGroups"][0]["filters"][0] == {
        "dimension": "query",
        "operator": "equals",
        "expression": "best shaver",
    }


def test_get_page_queries_sorts_by_requested_metric() -> None:
    service = FakeSearchAnalyticsService(
        rows=[
            {"keys": ["query-b"], "clicks": 1, "impressions": 90, "ctr": 0.011, "position": 8},
            {"keys": ["query-a"], "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 4},
        ]
    )

    result = get_page_queries(
        service,
        property_uri="sc-domain:example.com",
        page="https://example.com/post",
        start_date="2026-04-01",
        end_date="2026-04-07",
        metric="clicks",
    )

    assert [row["query"] for row in result] == ["query-a", "query-b"]


def test_inspect_urls_batch_rejects_more_than_fifty_urls() -> None:
    service = FakeInspectionService({})

    with pytest.raises(ValidationError):
        inspect_urls_batch(
            service,
            property_uri="sc-domain:example.com",
            inspection_urls=[f"https://example.com/{idx}" for idx in range(51)],
        )


def test_inspect_urls_batch_halts_on_quota_exhaustion_with_partial_results() -> None:
    service = FakeInspectionService(
        {
            "https://example.com/a": {"inspectionResult": {"indexStatusResult": {"coverageState": "Indexed"}}},
            "https://example.com/b": QuotaError("quota exhausted"),
            "https://example.com/c": {"inspectionResult": {"indexStatusResult": {"coverageState": "Indexed"}}},
        }
    )

    result = inspect_urls_batch(
        service,
        property_uri="sc-domain:example.com",
        inspection_urls=[
            "https://example.com/a",
            "https://example.com/b",
            "https://example.com/c",
        ],
    )

    assert result["halted"] is True
    assert result["halt_reason"] == "quota_exhausted"
    assert result["processed_count"] == 2
    assert result["success_count"] == 1
    assert result["error_count"] == 1


def test_inspect_urls_batch_halts_on_first_error_when_stop_on_error_is_true() -> None:
    service = FakeInspectionService(
        {
            "https://example.com/a": {"inspectionResult": {"indexStatusResult": {"coverageState": "Indexed"}}},
            "https://example.com/b": RuntimeError("boom"),
            "https://example.com/c": {"inspectionResult": {"indexStatusResult": {"coverageState": "Indexed"}}},
        }
    )

    result = inspect_urls_batch(
        service,
        property_uri="sc-domain:example.com",
        inspection_urls=[
            "https://example.com/a",
            "https://example.com/b",
            "https://example.com/c",
        ],
        stop_on_error=True,
    )

    assert result["halted"] is True
    assert result["halt_reason"] == "RuntimeError"
    assert result["processed_count"] == 2
    assert result["success_count"] == 1
    assert result["error_count"] == 1


@dataclass
class FakeSearchAnalyticsService:
    rows: list[dict[str, object]]
    last_body: dict[str, object] | None = None
    last_site_url: str | None = None

    def searchanalytics(self):
        return self

    def query(self, *, siteUrl: str, body: dict[str, object]):
        self.last_site_url = siteUrl
        self.last_body = body
        return self

    def execute(self):
        return {"rows": self.rows}


class FakeInspectionService:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses

    def urlInspection(self):
        return self

    def index(self):
        return self

    def inspect(self, *, body: dict[str, object]):
        inspection_url = body["inspectionUrl"]
        response = self.responses[inspection_url]
        if isinstance(response, Exception):
            raise response
        self._response = response
        return self

    def execute(self):
        return self._response


class QuotaError(RuntimeError):
    pass
