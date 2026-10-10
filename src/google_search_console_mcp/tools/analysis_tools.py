"""
[INPUT]: 依赖确定性分析函数、ReadToolService 审计与 MCP 参数契约
[OUTPUT]: 提供 register_analysis_tools 注册七类只读分析工具
[POS]: tools 的分析装配器，复用认证与审计，不在协议层计算指标
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
from typing import Annotated, Literal

from mcp.types import ToolAnnotations
from pydantic import Field

from .. import analysis, portfolio_analysis, ctr_benchmark
from ..gsc.validation import SearchType
from ..gsc.filters import AnalysisFilters
from .contracts import RowLimit
from .read_tools import ReadToolService

PositiveCount = Annotated[int, Field(ge=1)]
Ratio = Annotated[float, Field(ge=0, le=1)]
PeriodDays = Annotated[int, Field(ge=1, le=120)]
ANALYSIS_NOTE = (
    " Returns {items, meta}; meta.sources contains query coverage for each window. "
    "Each query fetches at most 100000 rows. Metrics use finalized data, PT dates, and CTR ratios. "
    "Missing rows are not zeros or evidence of deindexing. "
    "Optional filters apply country/device/path and query RE2 include/exclude rules using AND."
)


def register_analysis_tools(mcp, *, read_service: ReadToolService):
    def run(name, fn, params):
        return read_service._run(name, params, lambda: fn(read_service._service(), **params))

    @mcp.tool(name="compare_periods", description=(
        "Compare an inclusive date window with the immediately preceding equal-length window. "
        "dimension=site queries ungrouped totals directly; page/query compare entities. "
        "Only entities present in both windows receive deltas. click_change_ratio is null for a zero baseline. "
        "Sort by absolute click change; no causal diagnosis." + ANALYSIS_NOTE),
        annotations=ToolAnnotations(readOnlyHint=True))
    def compare_periods(property_uri: str, start_date: str, end_date: str,
                        dimension: Literal["page", "query", "site"] = "page",
                        search_type: SearchType = "web", row_limit: RowLimit = 50, filters: AnalysisFilters | None = None):
        return run("compare_periods", analysis.compare_periods, dict(
            property_uri=property_uri,
            start_date=start_date,
            end_date=end_date,
            dimension=dimension,
            search_type=search_type,
            row_limit=row_limit,
            filters=filters.model_dump(exclude_none=True) if filters else None,
        ))

    @mcp.tool(name="find_ctr_opportunities", description=(
        "Find high-impression rows with CTR at or below max_ctr, ordered by impressions. "
        "max_ctr=0.02 means 2%. These are review candidates, not industry benchmark failures or traffic forecasts."
        + ANALYSIS_NOTE), annotations=ToolAnnotations(readOnlyHint=True))
    def find_ctr_opportunities(property_uri: str, start_date: str, end_date: str,
                              dimension: Literal["page", "query"] = "page", search_type: SearchType = "web",
                              min_impressions: PositiveCount = 100, max_ctr: Ratio = 0.02, row_limit: RowLimit = 50, filters: AnalysisFilters | None = None):
        return run("find_ctr_opportunities", analysis.find_ctr_opportunities, dict(
            property_uri=property_uri,
            start_date=start_date,
            end_date=end_date,
            dimension=dimension,
            search_type=search_type,
            min_impressions=min_impressions,
            max_ctr=max_ctr,
            row_limit=row_limit,
            filters=filters.model_dump(exclude_none=True) if filters else None,
        ))

    @mcp.tool(name="find_declining_pages", description=(
        "Find pages with strictly declining clicks over three consecutive equal-length windows ending on end_date. "
        "Require a row in every window; report excluded missing-period pages. min_decline_ratio=0.2 means a 20% "
        "decline from oldest to newest. This does not establish content quality or the cause of decline."
        + ANALYSIS_NOTE), annotations=ToolAnnotations(readOnlyHint=True))
    def find_declining_pages(property_uri: str, end_date: str, period_days: PeriodDays = 28,
                             search_type: SearchType = "web", min_initial_clicks: PositiveCount = 10,
                             min_decline_ratio: Ratio = 0.2, row_limit: RowLimit = 50, filters: AnalysisFilters | None = None):
        return run("find_declining_pages", analysis.find_declining_pages, dict(
            property_uri=property_uri,
            end_date=end_date,
            period_days=period_days,
            search_type=search_type,
            min_initial_clicks=min_initial_clicks,
            min_decline_ratio=min_decline_ratio,
            row_limit=row_limit,
            filters=filters.model_dump(exclude_none=True) if filters else None,
        ))

    @mcp.tool(name="get_query_overlap", description=(
        "Find queries where at least two pages each meet min_page_impressions. Return per-page evidence; "
        "overlap does not prove harmful cannibalization. summed_page_impressions is not a deduplicated "
        "property-level query total." + ANALYSIS_NOTE), annotations=ToolAnnotations(readOnlyHint=True))
    def get_query_overlap(property_uri: str, start_date: str, end_date: str, search_type: SearchType = "web",
                          min_page_impressions: PositiveCount = 10, row_limit: RowLimit = 50, filters: AnalysisFilters | None = None):
        return run("get_query_overlap", analysis.get_query_overlap, dict(
            property_uri=property_uri,
            start_date=start_date,
            end_date=end_date,
            search_type=search_type,
            min_page_impressions=min_page_impressions,
            row_limit=row_limit,
            filters=filters.model_dump(exclude_none=True) if filters else None,
        ))


    @mcp.tool(name="get_multi_site_summary", description=(
        "Compare 1..20 explicit GSC properties over the same current/prior windows. "
        "Sort largest click loss first; keep per-property errors and missing data. "
        "Never sum overlapping domain and URL-prefix properties." + ANALYSIS_NOTE),
        annotations=ToolAnnotations(readOnlyHint=True))
    def get_multi_site_summary(
        property_uris: Annotated[list[str], Field(min_length=1, max_length=20)],
        start_date: str, end_date: str, search_type: SearchType = "web", filters: AnalysisFilters | None = None,
    ):
        return run("get_multi_site_summary", portfolio_analysis.get_multi_site_summary, dict(
            property_uris=property_uris, start_date=start_date, end_date=end_date,
            search_type=search_type, filters=filters.model_dump(exclude_none=True) if filters else None,
        ))

    @mcp.tool(name="compare_search_types", description=(
        "Join Web and Image metrics by page or query, sorted by Image impressions. "
        "Absent sides remain null, not zero. Use existing CTR/decline tools with search_type=image for image candidates."
        + ANALYSIS_NOTE), annotations=ToolAnnotations(readOnlyHint=True))
    def compare_search_types(
        property_uri: str, start_date: str, end_date: str, dimension: Literal["page", "query"] = "page",
        row_limit: RowLimit = 50, filters: AnalysisFilters | None = None,
    ):
        return run("compare_search_types", portfolio_analysis.compare_search_types, dict(
            property_uri=property_uri, start_date=start_date, end_date=end_date, dimension=dimension,
            row_limit=row_limit, filters=filters.model_dump(exclude_none=True) if filters else None,
        ))

    @mcp.tool(name="benchmark_page_ctr", description=(
        "Build a Web-only, same-property CTR benchmark from page-query rows by average-position buckets. "
        "Exclude each target page from its reference, then weight reference CTRs by the target's impression mix. "
        "Samples below thresholds return null benchmarks; no industry fallback. page selects a target after "
        "fetching peers; filters scope both targets and peers. actual_ctr covers observed query rows, not all page traffic."
        + ANALYSIS_NOTE), annotations=ToolAnnotations(readOnlyHint=True))
    def benchmark_page_ctr(
        property_uri: str, start_date: str, end_date: str, page: str | None = None,
        min_reference_impressions: PositiveCount = 500, min_reference_queries: PositiveCount = 5,
        min_reference_pages: PositiveCount = 3, row_limit: RowLimit = 50, filters: AnalysisFilters | None = None,
    ):
        return run("benchmark_page_ctr", ctr_benchmark.benchmark_page_ctr, dict(
            property_uri=property_uri, start_date=start_date, end_date=end_date, page=page,
            min_reference_impressions=min_reference_impressions, min_reference_queries=min_reference_queries,
            min_reference_pages=min_reference_pages, row_limit=row_limit,
            filters=filters.model_dump(exclude_none=True) if filters else None,
        ))
