> Historical design document. For current installation and supported behavior, see [README](../../README.md). Paths are illustrative.

# GSC Agent Query Commands Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the approved AI-agent-focused GSC query command surface on top of the existing read-only MCP skeleton.

**Architecture:** Extend the existing Search Analytics wrapper with explicit template queries for site, page, and query use cases, keeping `query_search_analytics` as the raw escape hatch. Add batch URL inspection with hard guardrails, then wire everything through `ReadToolService` and MCP tool registration without changing the read-only boundary.

**Tech Stack:** Python 3.13 runtime via uv, FastMCP/MCP SDK, Google Search Console API client, pytest

### Task 1: Extend performance query templates

**Files:**
- Modify: `src/google_search_console_mcp/gsc/performance.py`
- Modify: `src/google_search_console_mcp/gsc/CLAUDE.md`
- Test: `tests/test_gsc_client.py`

**Step 1: Write the failing tests**

Add tests for:
- `average_position` sorts ascending while other metrics sort descending
- `get_pages_by_path_prefix()` filters by URL path rather than raw substring
- page/query trend helpers build the expected dimensions and filters

**Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_gsc_client.py -v`
Expected: FAIL because the new helpers do not exist yet.

**Step 3: Write minimal implementation**

Implement:
- site summaries by `device` and `country`
- `get_top_pages`, `get_page_trend`, `get_pages_by_path_prefix`, `get_page_queries`, `get_page_query_pairs`
- `get_top_queries`, `get_query_trend`, `get_query_pages`, `get_query_page_pairs`
- shared metric sorting and exact-filter helpers

**Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_gsc_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/gsc/performance.py src/google_search_console_mcp/gsc/CLAUDE.md tests/test_gsc_client.py
git commit -m "feat: add agent query performance templates"
```

### Task 2: Add batch URL inspection contract

**Files:**
- Modify: `src/google_search_console_mcp/gsc/inspection.py`
- Modify: `src/google_search_console_mcp/gsc/CLAUDE.md`
- Test: `tests/test_gsc_client.py`

**Step 1: Write the failing tests**

Add tests for:
- hard batch limit of 50 URLs
- `quota exhausted` forces global halt with partial results
- `stop_on_error=true` halts on first ordinary inspection failure

**Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_gsc_client.py -v`
Expected: FAIL because batch inspection does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- `inspect_urls_batch()`
- quota-exhaustion detection
- stable return contract with `results`, `errors`, `processed_count`, `halted`, `halt_reason`

**Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_gsc_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/gsc/inspection.py src/google_search_console_mcp/gsc/CLAUDE.md tests/test_gsc_client.py
git commit -m "feat: add batch url inspection"
```

### Task 3: Wire new commands into the MCP tool layer

**Files:**
- Modify: `src/google_search_console_mcp/tools/read_tools.py`
- Modify: `src/google_search_console_mcp/tools/CLAUDE.md`
- Test: `tests/test_tools.py`

**Step 1: Write the failing tests**

Add tests for:
- expanded `build_read_tool_names()` list
- batch inspection tool name present
- low-frequency sitemap tools still retained

**Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_tools.py -v`
Expected: FAIL because tool registration list is still the old skeleton surface.

**Step 3: Write minimal implementation**

Implement:
- service methods for the new performance/query/page helpers
- service method for `inspect_urls_batch`
- MCP tool registration for all new commands

**Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_tools.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/tools/read_tools.py src/google_search_console_mcp/tools/CLAUDE.md tests/test_tools.py
git commit -m "feat: register agent query command tools"
```

### Task 4: Sync canonical docs and run full verification

**Files:**
- Modify: `docs/plans/2026-04-12-gsc-agent-query-commands-design.md`
- Modify: `src/google_search_console_mcp/CLAUDE.md`
- Modify: `src/google_search_console_mcp/gsc/CLAUDE.md`
- Modify: `src/google_search_console_mcp/tools/CLAUDE.md`
- Modify: `tests/CLAUDE.md`

**Step 1: Write the failing test**

Add or update tests only if implementation forced contract changes. Otherwise keep this task doc-only.

**Step 2: Run verification commands**

Run:
- `uv run --extra dev pytest -v`
- `uv run python -m google_search_console_mcp.cli auth status --help`

Expected:
- all tests pass
- CLI help renders without import errors

**Step 3: Sync docs**

Update module maps and, only if needed, the design doc wording so the terrain still matches the map.

**Step 4: Commit**

```bash
git add docs/plans/2026-04-12-gsc-agent-query-commands-design.md src/google_search_console_mcp/CLAUDE.md src/google_search_console_mcp/gsc/CLAUDE.md src/google_search_console_mcp/tools/CLAUDE.md tests/CLAUDE.md
git commit -m "docs: sync agent query command maps"
```
