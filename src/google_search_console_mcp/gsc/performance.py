"""
[INPUT]: 依赖 Search Console service 的 searchanalytics().query() 能力
[OUTPUT]: 对外提供 query_search_analytics、get_site_daily_summary 与 normalize_search_analytics_row
[POS]: gsc 的性能数据读取器，负责原始响应到稳定字段的轻度折叠
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations


def normalize_search_analytics_row(dimensions: list[str], row: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    keys = list(row.get("keys", []))
    for index, name in enumerate(dimensions):
        result[name] = keys[index] if index < len(keys) else None
    result["clicks"] = row.get("clicks", 0)
    result["impressions"] = row.get("impressions", 0)
    result["ctr"] = row.get("ctr", 0.0)
    result["average_position"] = row.get("position", 0.0)
    return result


def query_search_analytics(
    service,
    *,
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
) -> list[dict[str, object]]:
    dimensions = dimensions or []
    body: dict[str, object] = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions,
        "rowLimit": row_limit,
        "startRow": start_row,
        "type": search_type,
    }
    if dimension_filter_groups:
        body["dimensionFilterGroups"] = dimension_filter_groups
    if data_state:
        body["dataState"] = data_state
    if aggregation_type:
        body["aggregationType"] = aggregation_type
    response = service.searchanalytics().query(siteUrl=property_uri, body=body).execute()
    return [normalize_search_analytics_row(dimensions, row) for row in response.get("rows", [])]


def get_site_daily_summary(
    service,
    *,
    property_uri: str,
    start_date: str,
    end_date: str,
    search_type: str = "web",
) -> list[dict[str, object]]:
    return query_search_analytics(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=["date"],
        search_type=search_type,
    )
