"""
[INPUT]: 依赖现有周期比较、有界查询与公共筛选
[OUTPUT]: 提供 get_multi_site_summary 与 compare_search_types
[POS]: 主包的跨站与跨搜索类型分析；保留逐站错误和缺失侧
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from .analysis import _rows, _result, compare_periods
from .errors import AuthError, AuthorizationError, UpstreamApiError, ValidationError
from .gsc.filters import build_filter_groups
from .gsc.validation import validate_window, validate_selection


def get_multi_site_summary(service, *, property_uris, start_date, end_date, search_type="web", filters=None):
    validate_window(start_date, end_date)
    build_filter_groups(filters)
    if not 1 <= len(property_uris) <= 20:
        raise ValidationError("provide 1..20 properties per call")
    items, sources = [], []
    properties = list(dict.fromkeys(property_uris))
    for property_uri in properties:
        try:
            result = compare_periods(service, property_uri=property_uri, start_date=start_date,
                                     end_date=end_date, dimension="site", search_type=search_type, filters=filters)
            sources.extend(result["meta"]["sources"])
            item = result["items"][0] if result["items"] else {
                "previous": None, "current": None, "status": "no_data"}
            items.append({"property_uri": property_uri, **item})
        except (AuthError, AuthorizationError, UpstreamApiError, ValidationError) as exc:
            items.append({"property_uri": property_uri, "status": "error", "error_type": type(exc).__name__,
                          "message": str(exc)})
    items.sort(key=lambda item: ("click_change" not in item, item.get("click_change", 0), item["property_uri"]))
    return {"items": items, "meta": {
        "sources": sources, "source_truncated": any(s["truncated"] for s in sources),
        "start_date": start_date, "end_date": end_date, "search_type": search_type,
        "filters": build_filter_groups(filters), "ctr_unit": "ratio_0_1", "timezone": "America/Los_Angeles",
        "requested_count": len(property_uris), "unique_count": len(properties),
        "error_count": sum(item["status"] == "error" for item in items),
        "ordering": "click change ascending (largest absolute loss first); unavailable comparisons follow",
        "note": "No cross-property totals: domain and URL-prefix properties can overlap. Missing rows are not zeros.",
    }}


def compare_search_types(service, *, property_uri, start_date, end_date, dimension="page", row_limit=50, filters=None):
    validate_selection("clicks", row_limit, 0)
    if dimension not in {"page", "query"}:
        raise ValidationError("dimension must be page or query")
    sources = [_rows(service, property_uri=property_uri, start_date=start_date, end_date=end_date,
                     dimensions=[dimension], search_type=kind, filters=filters) for kind in ("web", "image")]
    web, image = [{row[dimension]: row for row in source} for source in sources]
    items = [{"entity": key, "web": web.get(key), "image": image.get(key),
              "status": "both" if key in web and key in image else (
                  "not_returned_image" if key in web else "not_returned_web")}
             for key in sorted(web.keys() | image.keys())]
    items.sort(key=lambda item: (item["image"] is None, -(item["image"] or {}).get("impressions", 0), item["entity"]))
    return _result(items, sources, row_limit=row_limit, dimension=dimension,
                   ordering="image impressions descending; missing image rows follow",
                   interpretation="Web and Image metrics are separate surfaces; missing sides remain null. Image impressions do not identify individual image files.")
