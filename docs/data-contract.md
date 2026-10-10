# Data contract

## Queries

Search Analytics tools return `rows` and `meta`. Dates are inclusive PT dates. CTR is a ratio, and average position is an impression-weighted observation rather than a rank-tracker result. Missing positions remain null.

`meta` retains the property, window, filters, search type, actual aggregation types, capture time, and Google's freshness metadata. `data_state=final` is the default. Hourly queries require both `data_state=hourly_all` and the `hour` dimension.

Single-page queries use `row_limit` and `start_row`. Set `fetch_all=true` to paginate with a `max_rows` budget (default 100,000, maximum 1,000,000). Top and analysis tools use a 100,000-row budget per query.

- `truncated`: more rows exist, or a full single page has not established exhaustion.
- `pagination_complete`: the request started at zero and exhausted API-returned rows within its budget.
- `next_start_row`: API continuation offset.
- `selection_offset` / `selection_truncated`: local slicing after a Top query's sorting/filtering; these are different from API offsets.

Pagination completion never means a complete keyword inventory. Google can omit anonymized queries and other rows. See [Google's query reference](https://developers.google.com/webmaster-tools/v1/searchanalytics/query).

## Analysis

Analysis tools return `items` and `meta.sources`. Each source describes the input query. Most analyses report `source_truncated`, candidate counts, and output truncation. Multi-site summaries instead report requested/unique property counts and per-site errors.

- Period comparison uses the immediately preceding equal-length window. Deltas require rows in both periods. Percentage changes from zero are null.
- Low-CTR candidates use explicit volume and CTR thresholds, not a promised traffic opportunity.
- Decline detection requires rows in three consecutive windows and strictly falling clicks.
- Query overlap identifies multiple observed pages, not proven harmful cannibalization. Summed page impressions are not deduplicated property impressions.
- Multi-site summaries retain failures and do not combine overlapping properties into a portfolio total.
- Web/Image comparison joins on a page or query; an absent side stays null.

All seven tools accept AND-combined country, device, literal path-prefix, and RE2 query include/exclude filters. These filters apply to every queried window/surface. Query filters cannot be used with Discover or Google News.

## Same-property CTR benchmark

The Web-only benchmark uses page-query rows. Average-position intervals are `(0,3]`, `(3,10]`, `(10,20]`, `(20,50]`, and `(50,+∞)`.

Each reference interval excludes the entire target page. Reference CTR is summed clicks divided by summed impressions. The overall baseline weights interval CTRs by the target page's observed impression distribution.

Default reference requirements per interval are 500 impressions, 5 distinct queries, and 3 other pages. They are configurable sample gates, not confidence levels. If any target interval lacks enough reference data, the overall benchmark is null; per-interval evidence remains available. There is no industry fallback or predicted-click estimate.

`filters` scope both targets and peers. `page` chooses a target after fetching peers. Actual CTR is based on observed ranked query rows, not all traffic to the page. Truncation and withheld queries can affect the comparison.

## Local outputs and compatibility

Snapshots are separate by property, search type, and date. Existing legacy CSVs remain readable. Empty API data does not create a fabricated zero snapshot.

Clients that previously consumed Search Analytics as a top-level array must now read `rows`. Property lists, URL inspection, sitemap tools, and snapshot tools retain their existing shapes. Reconnect a running MCP client after updating the server to refresh tool schemas.
