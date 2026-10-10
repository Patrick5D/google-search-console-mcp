"""
[INPUT]: 依赖标准库日期与 URL 解析、统一 ValidationError
[OUTPUT]: 提供查询枚举、日期与参数校验函数
[POS]: gsc 的输入边界；API 查询与分析工具共享相同口径
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from datetime import date
from typing import Literal, get_args
from urllib.parse import urlsplit

from ..errors import ValidationError

SearchType = Literal["web", "image", "video", "news", "discover", "googleNews"]
DataState = Literal["final", "all", "hourly_all"]
AggregationType = Literal["auto", "byPage", "byProperty", "byNewsShowcasePanel"]
Metric = Literal["clicks", "impressions", "ctr", "average_position"]
DIMENSIONS = {"page", "query", "country", "device", "date", "hour", "searchAppearance"}
FILTER_DIMENSIONS = DIMENSIONS - {"date", "hour"}
OPERATORS = {"equals", "notEquals", "contains", "notContains", "includingRegex", "excludingRegex"}


def parse_date(value: str) -> date:
    try:
        result = date.fromisoformat(value)
        if result.isoformat() != value:
            raise ValueError
        return result
    except (TypeError, ValueError) as exc:
        raise ValidationError("date must be YYYY-MM-DD in America/Los_Angeles") from exc


def validate_window(start_date: str, end_date: str):
    start, end = parse_date(start_date), parse_date(end_date)
    if start > end:
        raise ValidationError("start_date must not exceed end_date")
    return start, end


def validate_selection(metric: str, row_limit: int, start_row: int):
    if metric not in get_args(Metric):
        raise ValidationError("unsupported metric")
    if not 1 <= row_limit <= 25000 or start_row < 0:
        raise ValidationError("row_limit must be 1..25000; start_row must be non-negative")


def validate_query(*, property_uri, start_date, end_date, dimensions, row_limit, start_row,
                   search_type, data_state, aggregation_type, dimension_filter_groups, max_rows):
    validate_window(start_date, end_date)
    url = urlsplit(property_uri)
    if not (property_uri.startswith("sc-domain:") and len(property_uri) > 10) and not (
        url.scheme in {"https", "http"} and url.netloc
    ):
        raise ValidationError("property_uri must be a sc-domain: property or HTTP(S) URL prefix")
    if property_uri != property_uri.strip():
        raise ValidationError("property_uri must not contain surrounding whitespace")
    validate_selection("clicks", row_limit, start_row)
    if not 1 <= max_rows <= 1000000:
        raise ValidationError("max_rows must be 1..1000000")
    if search_type not in get_args(SearchType):
        raise ValidationError("unsupported search_type")
    if data_state is not None and data_state not in get_args(DataState):
        raise ValidationError("unsupported data_state")
    if aggregation_type is not None and aggregation_type not in get_args(AggregationType):
        raise ValidationError("unsupported aggregation_type")
    if len(set(dimensions)) != len(dimensions) or set(dimensions) - DIMENSIONS:
        raise ValidationError("dimensions must be supported and unique")
    if data_state == "hourly_all" and "hour" not in dimensions:
        raise ValidationError("hourly_all requires the hour dimension")
    if "hour" in dimensions and data_state != "hourly_all":
        raise ValidationError("hour dimension requires hourly_all")
    filter_dimensions = set()
    for group in dimension_filter_groups or []:
        if group.get("groupType", "and") != "and":
            raise ValidationError("only AND filter groups are supported")
        filters = group.get("filters")
        if not isinstance(filters, list) or not filters:
            raise ValidationError("filter groups require a non-empty filters list")
        for item in filters:
            if not isinstance(item, dict) or item.get("dimension") not in FILTER_DIMENSIONS:
                raise ValidationError("unsupported filter dimension")
            if item.get("operator", "equals") not in OPERATORS:
                raise ValidationError("unsupported filter operator")
            if not isinstance(item.get("expression"), str) or len(item["expression"]) > 4096:
                raise ValidationError("filter expression must be a string of at most 4096 characters")
            filter_dimensions.add(item["dimension"])
    if search_type in {"discover", "googleNews"} and "query" in set(dimensions) | filter_dimensions:
        raise ValidationError("Discover and Google News do not expose query-level data")
    if aggregation_type == "byProperty" and (
        "page" in set(dimensions) | filter_dimensions or search_type in {"discover", "googleNews"}
    ):
        raise ValidationError("byProperty is incompatible with page grouping/filtering or this search type")
