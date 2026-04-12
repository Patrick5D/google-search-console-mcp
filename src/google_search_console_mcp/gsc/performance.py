"""
[INPUT]: 依赖 Search Console service 的 searchanalytics().query() 能力与 URL path 解析
[OUTPUT]: 对外提供 query_search_analytics、站点/页面/query 模板查询与排序辅助函数
[POS]: gsc 的性能数据读取器，负责原始响应到稳定字段的轻度折叠与高频任务模板
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from urllib.parse import urlsplit


SORT_ASC_METRICS = {"average_position"}


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


def sort_rows_by_metric(rows: list[dict[str, object]], metric: str) -> list[dict[str, object]]:
    reverse = metric not in SORT_ASC_METRICS
    return sorted(rows, key=lambda row: row.get(metric, 0), reverse=reverse)


def _equals_filter(dimension: str, expression: str) -> list[dict[str, object]]:
    return [{"filters": [{"dimension": dimension, "operator": "equals", "expression": expression}]}]


def _top_rows(
    service,
    *,
    property_uri: str,
    start_date: str,
    end_date: str,
    dimensions: list[str],
    metric: str,
    search_type: str,
    row_limit: int,
    start_row: int,
    dimension_filter_groups: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    rows = query_search_analytics(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=dimensions,
        row_limit=max(row_limit + start_row, 1000),
        start_row=0,
        dimension_filter_groups=dimension_filter_groups,
        search_type=search_type,
    )
    sorted_rows = sort_rows_by_metric(rows, metric)
    return sorted_rows[start_row : start_row + row_limit]


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


def get_site_summary_by_device(
    service,
    *,
    property_uri: str,
    start_date: str,
    end_date: str,
    search_type: str = "web",
    row_limit: int = 10,
    start_row: int = 0,
) -> list[dict[str, object]]:
    return query_search_analytics(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=["device"],
        row_limit=row_limit,
        start_row=start_row,
        search_type=search_type,
    )


def get_site_summary_by_country(
    service,
    *,
    property_uri: str,
    start_date: str,
    end_date: str,
    search_type: str = "web",
    row_limit: int = 50,
    start_row: int = 0,
) -> list[dict[str, object]]:
    return query_search_analytics(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=["country"],
        row_limit=row_limit,
        start_row=start_row,
        search_type=search_type,
    )


def get_top_pages(
    service,
    *,
    property_uri: str,
    start_date: str,
    end_date: str,
    metric: str = "clicks",
    search_type: str = "web",
    row_limit: int = 50,
    start_row: int = 0,
) -> list[dict[str, object]]:
    return _top_rows(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=["page"],
        metric=metric,
        search_type=search_type,
        row_limit=row_limit,
        start_row=start_row,
    )


def get_page_trend(
    service,
    *,
    property_uri: str,
    page: str,
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
        dimension_filter_groups=_equals_filter("page", page),
        search_type=search_type,
    )


def get_pages_by_path_prefix(
    service,
    *,
    property_uri: str,
    path_prefix: str,
    start_date: str,
    end_date: str,
    metric: str = "clicks",
    search_type: str = "web",
    row_limit: int = 100,
    start_row: int = 0,
) -> list[dict[str, object]]:
    rows = query_search_analytics(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=["page"],
        row_limit=25000,
        start_row=0,
        search_type=search_type,
    )
    filtered = [row for row in rows if str(urlsplit(str(row.get("page", ""))).path).startswith(path_prefix)]
    sorted_rows = sort_rows_by_metric(filtered, metric)
    return sorted_rows[start_row : start_row + row_limit]


def get_page_queries(
    service,
    *,
    property_uri: str,
    page: str,
    start_date: str,
    end_date: str,
    metric: str = "clicks",
    search_type: str = "web",
    row_limit: int = 100,
    start_row: int = 0,
) -> list[dict[str, object]]:
    return _top_rows(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=["query"],
        metric=metric,
        search_type=search_type,
        row_limit=row_limit,
        start_row=start_row,
        dimension_filter_groups=_equals_filter("page", page),
    )


def get_page_query_pairs(
    service,
    *,
    property_uri: str,
    page: str,
    start_date: str,
    end_date: str,
    search_type: str = "web",
    row_limit: int = 200,
    start_row: int = 0,
) -> list[dict[str, object]]:
    return query_search_analytics(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=["page", "query"],
        row_limit=row_limit,
        start_row=start_row,
        dimension_filter_groups=_equals_filter("page", page),
        search_type=search_type,
    )


def get_top_queries(
    service,
    *,
    property_uri: str,
    start_date: str,
    end_date: str,
    metric: str = "clicks",
    search_type: str = "web",
    row_limit: int = 100,
    start_row: int = 0,
) -> list[dict[str, object]]:
    return _top_rows(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=["query"],
        metric=metric,
        search_type=search_type,
        row_limit=row_limit,
        start_row=start_row,
    )


def get_query_trend(
    service,
    *,
    property_uri: str,
    query: str,
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
        dimension_filter_groups=_equals_filter("query", query),
        search_type=search_type,
    )


def get_query_pages(
    service,
    *,
    property_uri: str,
    query: str,
    start_date: str,
    end_date: str,
    metric: str = "clicks",
    search_type: str = "web",
    row_limit: int = 100,
    start_row: int = 0,
) -> list[dict[str, object]]:
    return _top_rows(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=["page"],
        metric=metric,
        search_type=search_type,
        row_limit=row_limit,
        start_row=start_row,
        dimension_filter_groups=_equals_filter("query", query),
    )


def get_query_page_pairs(
    service,
    *,
    property_uri: str,
    query: str,
    start_date: str,
    end_date: str,
    search_type: str = "web",
    row_limit: int = 200,
    start_row: int = 0,
) -> list[dict[str, object]]:
    return query_search_analytics(
        service,
        property_uri=property_uri,
        start_date=start_date,
        end_date=end_date,
        dimensions=["query", "page"],
        row_limit=row_limit,
        start_row=start_row,
        dimension_filter_groups=_equals_filter("query", query),
        search_type=search_type,
    )
