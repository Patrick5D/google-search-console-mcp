# Google Search Console MCP

A local MCP server for querying Google Search Console and comparing search performance across sites, pages, and queries.

**30 tools · Read-only Google access · Python 3.12+ · Streamable HTTP**

This release uses MCP Python SDK 1.x (`mcp>=1.24,<2`). SDK 2.x migration is not included.

The server returns data with its query window, aggregation details, and pagination limits. Analysis tools surface observable changes and review candidates, without treating missing rows as zero traffic or diagnosing causes from metrics alone.

## What you can do

- Compare multiple properties over equal-length periods, keeping per-site errors.
- Find high-impression, low-CTR pages and pages with sustained click declines.
- Compare Web and Image search by page or query.
- Benchmark page CTR against other pages on the same property, excluding the target page from its reference samples.
- Inspect Google's indexed version of URLs, individually or in batches of up to 50.
- Read sitemaps and save local daily CSV snapshots.

This is an independent project, not an official Google product. It does not submit URLs for indexing, modify Search Console properties, or audit image files and HTML.

## Install from source

The commands below use a POSIX shell on macOS or Linux. You need Git, Python 3.12 or newer, and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```sh
git clone https://github.com/Patrick5D/google-search-console-mcp.git
cd google-search-console-mcp
uv venv --python 3.12
uv pip install -e '.[dev]'
cp config/server.example.yaml config/server.local.yaml
cp config/paths.example.yaml config/paths.local.yaml
```

Run commands from the repository root. Relative paths in YAML are resolved against the process working directory, not the YAML file's directory.

## Authorize your Google account

1. Create or select a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Google Search Console API**.
3. Configure the OAuth consent screen. If your external app is in testing, add your own account as a test user.
4. Create an OAuth client with application type **Desktop app**.
5. Download the client JSON to `config/oauth_client.json`.
6. Sign in with a Google account that already has access to your Search Console properties:

```sh
.venv/bin/python -m google_search_console_mcp.cli \
  --server-config config/server.local.yaml \
  --paths-config config/paths.local.yaml auth login
```

The browser-based flow uses a temporary localhost callback and stores credentials at the configured token path. The default is `config/token.json`. Never commit or share either credentials file.

The requested scope is `https://www.googleapis.com/auth/webmasters.readonly`. This gives the server read-only Search Console access. See [Google's authorization guide](https://developers.google.com/webmaster-tools/v1/how-tos/authorizing).

Check local credential readiness:

```sh
.venv/bin/python -m google_search_console_mcp.cli \
  --server-config config/server.local.yaml \
  --paths-config config/paths.local.yaml auth status
```

`ready: true` means locally usable credential material exists. It is not a live check of property permissions. Call `list_properties` after connecting to verify access.

## Start and connect

```sh
.venv/bin/python -m google_search_console_mcp.server \
  --server-config config/server.local.yaml \
  --paths-config config/paths.local.yaml
```

Keep this process running, then add a server in your MCP client's HTTP configuration:

| Setting | Value |
| --- | --- |
| Name | `gsc` |
| Transport | Streamable HTTP |
| URL | `http://127.0.0.1:8765/mcp` |
| HTTP authentication | None; intended for local use only |

Client configuration schemas differ; enter the URL in the client's Streamable HTTP server settings. This server does not currently provide a stdio mode. A client running in the cloud cannot reach your computer's loopback address.

The listener has no application-level authentication. Keep it bound to `127.0.0.1`; do not expose it directly to a network. Google OAuth authorizes upstream Google requests, not incoming MCP clients.

## Example requests

Ask your client to list accessible properties first. Domain properties look like `sc-domain:example.com`; URL-prefix properties use the exact URL shown by Search Console.

```text
List my Search Console properties.
Compare clicks for these two properties over the last complete 28-day period.
Find pages with at least 1,000 impressions and CTR below 2% on desktop.
Compare Web and Image search performance for my /guides/ pages.
Check whether Google has indexed these URLs.
```

An explicit tool call:

```json
{
  "tool": "find_ctr_opportunities",
  "arguments": {
    "property_uri": "sc-domain:example.com",
    "start_date": "2026-09-01",
    "end_date": "2026-09-28",
    "min_impressions": 1000,
    "max_ctr": 0.02,
    "filters": {
      "country": "usa",
      "device": "DESKTOP",
      "page_prefix": "/guides/",
      "query_exclude": "(?i)examplebrand"
    }
  }
}
```

Replace the property and dates with your own. Query include/exclude fields use Google's RE2 regex syntax; all supplied filters are combined with AND.

## Tool groups

| Group | Tools |
| --- | --- |
| Account and properties | `get_account_status`, `list_properties`, `get_property` |
| Search data | `query_search_analytics`, `get_site_daily_summary`, `get_site_summary_by_device`, `get_site_summary_by_country`, `get_top_pages`, `get_page_trend`, `get_pages_by_path_prefix`, `get_page_queries`, `get_page_query_pairs`, `get_top_queries`, `get_query_trend`, `get_query_pages`, `get_query_page_pairs` |
| URL inspection and sitemaps | `inspect_url`, `inspect_urls_batch`, `list_sitemaps`, `get_sitemap` |
| Analysis | `compare_periods`, `find_ctr_opportunities`, `find_declining_pages`, `get_query_overlap`, `get_multi_site_summary`, `compare_search_types`, `benchmark_page_ctr` |
| Local snapshots | `snapshot_site_day`, `list_snapshots`, `read_snapshot` |

## Data and configuration

- Dates are inclusive and use `America/Los_Angeles` (PT). CTR is a 0–1 ratio.
- Finalized data is the default. Missing rows do not establish zero traffic or deindexing.
- Search Analytics tools return `{rows, meta}`. Analysis tools return `{items, meta}`. Other tools retain their own response shapes.
- Automatic pagination is bounded. Top/analysis queries fetch at most 100,000 rows per query. Even exhausted pagination does not include every query Google withholds.
- CTR benchmarks use observed page-query rows and sample thresholds, not an industry fallback or a forecast. Web and Image metrics remain separate.
- Snapshots use `gsc/site_daily/{property}/{search_type}/{date}.csv`. Writing the same identity replaces the previous snapshot.
- Configure server and file paths in YAML and select them with `--server-config` / `--paths-config`. The historical `GSC_*` environment variables are not supported configuration overrides.

See the [English data contract](docs/data-contract.md) and the [detailed Chinese protocol](docs/gsc-tool-contracts.md).

## Privacy

The server calls Google APIs using your credentials. Tool results are returned to your MCP client; that client or its model provider may receive the data. There is no project-operated relay or telemetry endpoint.

Local audit logs include tool names, arguments, timestamps, and errors. These can contain property names, page URLs, and query filters. Snapshots contain search metrics. Keep `logs/`, `snapshots/`, tokens, and local configurations private. The default ignored paths are listed in `.gitignore`; custom paths need equivalent protection.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Missing OAuth client or token | Confirm configured paths and working directory; run `auth login`. |
| Consent denied or `invalid_grant` | Check consent/test-user settings and reauthorize. |
| Property permission error | Call `list_properties`; use the exact property and authorized account. |
| Recent dates return no rows | Try an older finalized window; empty data is not an indexing diagnosis. |
| Client cannot connect | Confirm the process is running, port matches YAML, and the client supports local Streamable HTTP. |
| Google quota error | Read the error; daily quota errors stop immediately, while transient failures retry at most twice. |

## Development

```sh
.venv/bin/python -m pytest -q
.venv/bin/python tests/smoke_http.py
```

Both checks work without Google credentials. The smoke test starts an isolated localhost server, verifies the 30-tool HTTP interface, and shuts it down. It does not call Google or modify another running server.

See [CONTRIBUTING.md](CONTRIBUTING.md). Historical design plans under `docs/plans/` describe earlier work and are not installation instructions.

## License

[MIT](LICENSE). Dependencies retain their respective licenses.
