"""
[INPUT]: 依赖页面/查询词有界取数、公共筛选与标准库计数器
[OUTPUT]: 提供 benchmark_page_ctr 与 rank_bucket
[POS]: 主包的本站 CTR 对照；按排名区间留出目标页面，报告参考样本
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from collections import Counter, defaultdict

from .analysis import _rows, _result
from .errors import ValidationError
from .gsc.validation import validate_selection

BUCKETS = ((3, "1-3"), (10, "4-10"), (20, "11-20"), (50, "21-50"), (float("inf"), "51+"))


def rank_bucket(position):
    if position is None or position <= 0:
        return None
    return next(label for maximum, label in BUCKETS if position <= maximum)


def _sample():
    return {"clicks": 0, "impressions": 0, "queries": Counter()}


def benchmark_page_ctr(service, *, property_uri, start_date, end_date, page=None, filters=None,
                       min_reference_impressions=500, min_reference_queries=5,
                       min_reference_pages=3, row_limit=50):
    validate_selection("clicks", row_limit, 0)
    if min(min_reference_impressions, min_reference_queries, min_reference_pages) < 1:
        raise ValidationError("reference thresholds must be positive")
    rows = _rows(service, property_uri=property_uri, start_date=start_date, end_date=end_date,
                 dimensions=["page", "query"], search_type="web", filters=filters)
    totals = defaultdict(_sample)
    pages = defaultdict(lambda: defaultdict(_sample))
    bucket_pages = defaultdict(set)
    unranked = defaultdict(float)
    for row in rows:
        if row["impressions"] <= 0:
            continue
        bucket = rank_bucket(row["average_position"])
        if bucket is None:
            unranked[row["page"]] += row["impressions"]
            continue
        for sample in (totals[bucket], pages[row["page"]][bucket]):
            sample["clicks"] += row["clicks"]
            sample["impressions"] += row["impressions"]
            sample["queries"][row["query"]] += 1
        bucket_pages[bucket].add(row["page"])
    items = []
    targets = [page] if page else sorted(pages.keys() | unranked.keys())
    for target in targets:
        details = []
        for _, bucket in BUCKETS:
            sample = pages.get(target, {}).get(bucket)
            if sample is None:
                continue
            total = totals[bucket]
            ref_impressions = total["impressions"] - sample["impressions"]
            ref_clicks = total["clicks"] - sample["clicks"]
            ref_queries = len(total["queries"]) - sum(
                total["queries"][q] == count for q, count in sample["queries"].items())
            ref_pages = len(bucket_pages[bucket]) - 1
            sufficient = (ref_impressions >= min_reference_impressions and ref_queries >= min_reference_queries
                          and ref_pages >= min_reference_pages)
            details.append({"rank_bucket": bucket, "target_impressions": sample["impressions"],
                            "target_clicks": sample["clicks"], "reference_impressions": ref_impressions,
                            "reference_clicks": ref_clicks, "reference_queries": ref_queries,
                            "reference_pages": ref_pages, "reference_ctr": ref_clicks / ref_impressions if sufficient else None,
                            "status": "available" if sufficient else "insufficient_sample"})
        impressions = sum(item["target_impressions"] for item in details)
        clicks = sum(item["target_clicks"] for item in details)
        supported = sum(item["target_impressions"] for item in details if item["reference_ctr"] is not None)
        missing_position = unranked.get(target, 0)
        complete = bool(impressions) and supported == impressions and not missing_position
        baseline = (sum(item["reference_ctr"] * item["target_impressions"] for item in details) / impressions
                    if complete else None)
        actual = clicks / impressions if impressions else None
        items.append({"page": target, "status": "available" if complete else (
            "not_returned" if not details and not missing_position else "insufficient_sample"),
            "actual_ctr": actual, "benchmark_ctr": baseline,
            "ctr_gap": actual - baseline if complete else None,
            "observed_ranked_impressions": impressions, "unranked_impressions": missing_position,
            "reference_coverage_ratio": supported / (impressions + missing_position) if impressions + missing_position else None,
            "buckets": details})
    items.sort(key=lambda item: (item["ctr_gap"] is None, item["ctr_gap"] or 0, item["page"]))
    return _result(items, [rows], row_limit=row_limit,
                   thresholds={"min_reference_impressions": min_reference_impressions,
                               "min_reference_queries": min_reference_queries, "min_reference_pages": min_reference_pages},
                   interpretation="Web only. CTRs use observed page-query rows, not page totals. Every reference bucket excludes the target page. The baseline is weighted by the target's observed rank mix. Thresholds are sample gates, not statistical confidence. No industry fallback or traffic forecast. Filters scope both targets and peers; page selects a target without removing peers.")
