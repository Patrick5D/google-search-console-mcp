"""
[INPUT]: 依赖有界查询、公共筛选与 PT 日期校验
[OUTPUT]: 提供周期对比、低 CTR 候选、连续下降与查询重叠分析
[POS]: 主包的确定性分析层；输出观测差异，不推断流量变化原因
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from datetime import timedelta

from .errors import ValidationError
from .gsc.filters import build_filter_groups
from .gsc.query import query_search_analytics
from .gsc.validation import parse_date, validate_window, validate_selection

ANALYSIS_NOTE = "Observed API data only. Missing rows are not zeros or proof of deindexing. Correlation does not identify a cause."


def _result(items, sources, *, row_limit, **extra):
    return {"items": items[:row_limit], "meta": {
        "sources": [source.meta for source in sources],
        "source_truncated": any(source.meta.get("truncated", False) for source in sources),
        "candidate_count": len(items), "returned_count": min(len(items), row_limit),
        "output_truncated": len(items) > row_limit, "ctr_unit": "ratio_0_1",
        "note": ANALYSIS_NOTE, **extra,
    }}


def _rows(service, *, property_uri, start_date, end_date, dimensions, search_type, filters=None):
    return query_search_analytics(service, property_uri=property_uri, start_date=start_date,
                                  end_date=end_date, dimensions=dimensions,
                                  search_type=search_type, data_state="final", fetch_all=True,
                                  dimension_filter_groups=build_filter_groups(filters))


def _percent(current, previous):
    return (current - previous) / previous if previous else None


def compare_periods(service, *, property_uri, start_date, end_date, dimension="page", search_type="web", row_limit=50, filters=None):
    """比较相邻等长窗口；不把未返回行转换为零。"""
    validate_selection("clicks", row_limit, 0)
    if dimension not in {"page", "query", "site"}:
        raise ValidationError("dimension must be page, query or site")
    start, end = validate_window(start_date, end_date)
    days = (end - start).days + 1
    previous_end = start - timedelta(days=1)
    previous_start = start - timedelta(days=days)
    dimensions = [] if dimension == "site" else [dimension]
    shared = dict(property_uri=property_uri, dimensions=dimensions, search_type=search_type, filters=filters)
    previous = _rows(service, start_date=previous_start.isoformat(), end_date=previous_end.isoformat(), **shared)
    current = _rows(service, start_date=start_date, end_date=end_date, **shared)
    key = lambda row: property_uri if dimension == "site" else row[dimension]
    before = {key(row): row for row in previous}
    after = {key(row): row for row in current}
    items = []
    for entity in sorted(before.keys() | after.keys()):
        old, new = before.get(entity), after.get(entity)
        item = {"entity": entity, "previous": old, "current": new,
                "status": "both" if old is not None and new is not None else (
                    "not_returned_current" if new is None else "not_returned_previous")}
        if old is not None and new is not None:
            item["click_change"] = new["clicks"] - old["clicks"]
            item["click_change_ratio"] = _percent(new["clicks"], old["clicks"])
            item["impression_change"] = new["impressions"] - old["impressions"]
            item["ctr_change"] = new["ctr"] - old["ctr"]
            item["position_change"] = (new["average_position"] - old["average_position"]
                                       if new["average_position"] is not None and old["average_position"] is not None else None)
        items.append(item)
    items.sort(key=lambda item: (-abs(item.get("click_change", 0)), item["entity"]))
    return _result(items, [previous, current], row_limit=row_limit, dimension=dimension,
                   ordering="absolute observed click change descending; missing-period rows follow")


def find_ctr_opportunities(service, *, property_uri, start_date, end_date, dimension="page", search_type="web",
                           min_impressions=100, max_ctr=0.02, row_limit=50, filters=None):
    validate_selection("clicks", row_limit, 0)
    if dimension not in {"page", "query"} or min_impressions < 1 or not 0 <= max_ctr <= 1:
        raise ValidationError("dimension must be page/query; min_impressions >= 1; max_ctr in 0..1")
    rows = _rows(service, property_uri=property_uri, start_date=start_date, end_date=end_date,
                 dimensions=[dimension], search_type=search_type, filters=filters)
    items = [dict(row) for row in rows if row["impressions"] >= min_impressions and row["ctr"] <= max_ctr]
    items.sort(key=lambda row: (-row["impressions"], row[dimension]))
    return _result(items, [rows], row_limit=row_limit,
                   thresholds={"min_impressions": min_impressions, "max_ctr": max_ctr},
                   interpretation="Threshold-based review candidates, not benchmark failures or predicted traffic gains.")


def find_declining_pages(service, *, property_uri, end_date, period_days=28, search_type="web",
                         min_initial_clicks=10, min_decline_ratio=0.2, row_limit=50, filters=None):
    validate_selection("clicks", row_limit, 0)
    if not 1 <= period_days <= 120 or min_initial_clicks < 1 or not 0 <= min_decline_ratio <= 1:
        raise ValidationError("period_days must be 1..120; min_initial_clicks >= 1; min_decline_ratio in 0..1")
    end = parse_date(end_date)
    windows, sources = [], []
    for index in (2, 1, 0):
        window_end = end - timedelta(days=index * period_days)
        window_start = window_end - timedelta(days=period_days - 1)
        window = {"start_date": window_start.isoformat(), "end_date": window_end.isoformat()}
        windows.append(window)
        sources.append(_rows(service, property_uri=property_uri, dimensions=["page"],
                             search_type=search_type, filters=filters, **window))
    maps = [{row["page"]: row for row in source} for source in sources]
    complete = maps[0].keys() & maps[1].keys() & maps[2].keys()
    all_pages = maps[0].keys() | maps[1].keys() | maps[2].keys()
    items = []
    for page in complete:
        values = [mapping[page] for mapping in maps]
        first, middle, last = [row["clicks"] for row in values]
        if first < min_initial_clicks or not first > middle > last:
            continue
        decline = (first - last) / first
        if decline < min_decline_ratio:
            continue
        items.append({"page": page, "periods": values, "click_loss": first - last, "decline_ratio": decline})
    items.sort(key=lambda item: (-item["click_loss"], item["page"]))
    return _result(items, sources, row_limit=row_limit, windows=windows,
                   excluded_missing_period_pages=len(all_pages - complete),
                   thresholds={"min_initial_clicks": min_initial_clicks, "min_decline_ratio": min_decline_ratio},
                   interpretation="Clicks fell across three equal windows; seasonal or other causes are not established.")


def get_query_overlap(service, *, property_uri, start_date, end_date, search_type="web",
                      min_page_impressions=10, row_limit=50, filters=None):
    validate_selection("clicks", row_limit, 0)
    if min_page_impressions < 1:
        raise ValidationError("min_page_impressions must be >= 1")
    rows = _rows(service, property_uri=property_uri, start_date=start_date, end_date=end_date,
                 dimensions=["query", "page"], search_type=search_type, filters=filters)
    queries = {}
    for row in rows:
        if row["impressions"] >= min_page_impressions:
            queries.setdefault(row["query"], []).append(dict(row))
    items = []
    for query, pages in queries.items():
        if len(pages) < 2:
            continue
        pages.sort(key=lambda row: (-row["impressions"], row["page"]))
        items.append({"query": query, "page_count": len(pages),
                      "summed_page_impressions": sum(row["impressions"] for row in pages), "pages": pages})
    items.sort(key=lambda item: (-item["summed_page_impressions"], item["query"]))
    return _result(items, [rows], row_limit=row_limit,
                   thresholds={"min_page_impressions": min_page_impressions},
                   interpretation="Multiple pages received impressions for the same query. This is not proof of harmful cannibalization. Page impressions can overlap and are not property-level query totals.")
