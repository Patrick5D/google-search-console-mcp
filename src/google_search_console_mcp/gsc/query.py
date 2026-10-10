"""
[INPUT]: 依赖参数校验与有限重试边界，读取 Search Analytics 分页响应
[OUTPUT]: 提供 QueryRows、query_search_analytics 与行字段归一化
[POS]: gsc 的查询边界，保留 API 元信息并限制自动分页规模
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from datetime import datetime, timezone

from .request import execute_read
from .validation import validate_query

PAGE_SIZE = 25000
DEFAULT_MAX_ROWS = 100000
COVERAGE_NOTE = "API-returned rows only; Google can omit anonymized queries and other rows. Not a complete keyword inventory."


class QueryRows(list):
    """内部保持列表兼容；MCP 边界显式输出 rows 与 meta。"""

    def __init__(self, rows=(), *, meta=None):
        super().__init__(rows)
        self.meta = dict(meta or {})

    def select(self, rows, *, matched: int, offset: int = 0):
        return QueryRows(rows, meta={
            **self.meta, "matched_rows": matched, "selection_offset": offset,
            "selection_truncated": offset > 0 or len(rows) < matched,
            "returned_rows": len(rows),
        })

    def as_result(self):
        return {"rows": list(self), "meta": self.meta}


def normalize_search_analytics_row(dimensions: list[str], row: dict[str, object]) -> dict[str, object]:
    keys = list(row.get("keys", []))
    result = {name: keys[i] if i < len(keys) else None for i, name in enumerate(dimensions)}
    result.update(clicks=row.get("clicks", 0), impressions=row.get("impressions", 0),
                  ctr=row.get("ctr", 0.0), average_position=row.get("position"))
    return result


def query_search_analytics(
    service, *, property_uri: str, start_date: str, end_date: str,
    dimensions: list[str] | None = None, row_limit: int = 1000, start_row: int = 0,
    dimension_filter_groups: list[dict[str, object]] | None = None,
    search_type: str = "web", data_state: str | None = None,
    aggregation_type: str | None = None, fetch_all: bool = False,
    max_rows: int = DEFAULT_MAX_ROWS,
) -> QueryRows:
    dimensions = dimensions or []
    validate_query(property_uri=property_uri, start_date=start_date, end_date=end_date,
                   dimensions=dimensions, row_limit=row_limit, start_row=start_row,
                   search_type=search_type, data_state=data_state, aggregation_type=aggregation_type,
                   dimension_filter_groups=dimension_filter_groups, max_rows=max_rows)
    body = {
        "startDate": start_date, "endDate": end_date, "dimensions": dimensions,
        "type": search_type, "dataState": data_state or "final",
    }
    if dimension_filter_groups:
        body["dimensionFilterGroups"] = dimension_filter_groups
    if aggregation_type:
        body["aggregationType"] = aggregation_type
    rows = []
    api_metadata = []
    aggregation_types = set()
    offset = start_row
    truncated = False
    requests = 0
    while True:
        limit = min(PAGE_SIZE, max_rows - len(rows)) if fetch_all else row_limit
        request_body = {**body, "rowLimit": limit, "startRow": offset}
        response = execute_read(service.searchanalytics().query(siteUrl=property_uri, body=request_body))
        requests += 1
        if response.get("metadata") is not None:
            api_metadata.append(response["metadata"])
        if response.get("responseAggregationType"):
            aggregation_types.add(response["responseAggregationType"])
        page = response.get("rows", [])
        rows.extend(normalize_search_analytics_row(dimensions, row) for row in page)
        offset += len(page)
        if len(page) < limit:
            break
        if not fetch_all:
            truncated = True  # 满页时不能断言已穷尽。
            break
        if len(rows) >= max_rows:
            probe = execute_read(service.searchanalytics().query(
                siteUrl=property_uri, body={**body, "rowLimit": 1, "startRow": offset}
            ))
            requests += 1
            truncated = bool(probe.get("rows"))
            break
    return QueryRows(rows, meta={
        "property_uri": property_uri, "start_date": start_date, "end_date": end_date,
        "search_type": search_type, "dimensions": dimensions,
        "filters": dimension_filter_groups or [], "data_state": data_state or "final",
        "requested_aggregation_type": aggregation_type or "auto",
        "response_aggregation_types": sorted(aggregation_types), "api_metadata": api_metadata,
        "timezone": "America/Los_Angeles", "ctr_unit": "ratio_0_1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "start_row": start_row, "fetched_rows": len(rows), "returned_rows": len(rows),
        "requests": requests, "fetch_all": fetch_all,
        "max_rows": max_rows if fetch_all else row_limit,
        "truncated": truncated, "pagination_complete": not truncated and start_row == 0,
        "next_start_row": offset if truncated else None, "coverage_note": COVERAGE_NOTE,
    })
