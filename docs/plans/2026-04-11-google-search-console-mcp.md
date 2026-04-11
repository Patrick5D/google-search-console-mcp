# Google Search Console MCP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a read-only Google Search Console MCP that supports multi-property access under one OAuth account and manual site-day CSV snapshots.

**Architecture:** Keep the system split into five thin layers: config, auth, GSC client wrappers, MCP tool registration, and CSV snapshot persistence. Reuse the clean parts of the existing Google Ads MCP shape, but delete write-approval concepts entirely so the code stays read-only and branch-light.

**Tech Stack:** Python 3.12, FastMCP/MCP SDK, Google API Python client + OAuth, python-dotenv, PyYAML, pydantic, pytest

### Task 1: Bootstrap project metadata and runtime layout

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `config/server.example.yaml`
- Create: `config/paths.example.yaml`
- Modify: `CLAUDE.md`
- Modify: `config/CLAUDE.md`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_project_metadata_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "pyproject.toml").exists()
    assert (root / ".gitignore").exists()
    assert (root / ".env.example").exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_bootstrap.py::test_project_metadata_files_exist -v`
Expected: FAIL because the metadata files do not exist yet.

**Step 3: Write minimal implementation**

Create the runtime metadata files with:

- package name `google-search-console-mcp`
- Python requirement `>=3.12`
- dependencies for MCP, Google API auth/client, dotenv, pydantic, PyYAML
- dev dependency `pytest`
- `.gitignore` entries for `.env`, OAuth tokens, `.venv`, caches, snapshots
- `.env.example` documenting `GSC_OAUTH_CLIENT_PATH`, `GSC_TOKEN_PATH`, config paths

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_bootstrap.py::test_project_metadata_files_exist -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml .gitignore .env.example config/server.example.yaml config/paths.example.yaml CLAUDE.md config/CLAUDE.md tests/test_bootstrap.py
git commit -m "chore: bootstrap gsc mcp project metadata"
```

### Task 2: Implement config loading and validation

**Files:**
- Create: `src/google_search_console_mcp/__init__.py`
- Create: `src/google_search_console_mcp/errors.py`
- Create: `src/google_search_console_mcp/config.py`
- Create: `tests/test_config.py`
- Modify: `src/CLAUDE.md`
- Modify: `tests/CLAUDE.md`
- Modify: `CLAUDE.md`

**Step 1: Write the failing test**

```python
from pathlib import Path

from google_search_console_mcp.config import load_settings


def test_load_settings_reads_server_and_paths(tmp_path: Path):
    server = tmp_path / "server.yaml"
    paths = tmp_path / "paths.yaml"
    server.write_text("server:\n  host: 127.0.0.1\n  port: 8766\n", encoding="utf-8")
    paths.write_text(
        "paths:\n"
        "  oauth_client_path: ./config/oauth_client.json\n"
        "  token_path: ./config/token.json\n"
        "  snapshot_root: ./snapshots\n",
        encoding="utf-8",
    )

    settings = load_settings(server, paths)

    assert settings.server.port == 8766
    assert settings.paths.snapshot_root == "./snapshots"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_load_settings_reads_server_and_paths -v`
Expected: FAIL with import or missing function errors.

**Step 3: Write minimal implementation**

Implement:

- `ConfigError`
- `ServerSettings`, `PathSettings`, `Settings`
- YAML readers for two config files
- sane defaults for host, port, audit log path, OAuth paths, snapshot root

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/__init__.py src/google_search_console_mcp/errors.py src/google_search_console_mcp/config.py tests/test_config.py src/CLAUDE.md tests/CLAUDE.md CLAUDE.md
git commit -m "feat: add configuration loading"
```

### Task 3: Implement OAuth credential loading and status checks

**Files:**
- Create: `src/google_search_console_mcp/auth.py`
- Create: `tests/test_auth.py`
- Modify: `src/CLAUDE.md`
- Modify: `tests/CLAUDE.md`

**Step 1: Write the failing test**

```python
from pathlib import Path

from google_search_console_mcp.auth import get_auth_status


def test_get_auth_status_reports_missing_token(tmp_path: Path):
    client = tmp_path / "oauth_client.json"
    client.write_text("{}", encoding="utf-8")

    status = get_auth_status(client_path=client, token_path=tmp_path / "token.json")

    assert status.client_config_exists is True
    assert status.token_exists is False
    assert status.ready is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_auth.py::test_get_auth_status_reports_missing_token -v`
Expected: FAIL because auth helpers do not exist.

**Step 3: Write minimal implementation**

Implement:

- `AuthStatus` model
- `get_auth_status()`
- credential loader
- refresh path with clear `AuthError` on failure
- no implicit browser launch inside read operations

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_auth.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/auth.py tests/test_auth.py src/CLAUDE.md tests/CLAUDE.md
git commit -m "feat: add oauth status and credential loading"
```

### Task 4: Build the Search Console client wrappers

**Files:**
- Create: `src/google_search_console_mcp/gsc/CLAUDE.md`
- Create: `src/google_search_console_mcp/gsc/__init__.py`
- Create: `src/google_search_console_mcp/gsc/client.py`
- Create: `src/google_search_console_mcp/gsc/sites.py`
- Create: `src/google_search_console_mcp/gsc/performance.py`
- Create: `src/google_search_console_mcp/gsc/inspection.py`
- Create: `src/google_search_console_mcp/gsc/sitemaps.py`
- Create: `tests/test_gsc_client.py`
- Modify: `src/CLAUDE.md`
- Modify: `tests/CLAUDE.md`
- Modify: `CLAUDE.md`

**Step 1: Write the failing test**

```python
from google_search_console_mcp.gsc.performance import normalize_search_analytics_row


def test_normalize_search_analytics_row_flattens_metrics():
    row = {"keys": ["2026-04-10"], "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 3.2}

    result = normalize_search_analytics_row(["date"], row)

    assert result["date"] == "2026-04-10"
    assert result["clicks"] == 10
    assert result["average_position"] == 3.2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_gsc_client.py::test_normalize_search_analytics_row_flattens_metrics -v`
Expected: FAIL because the GSC wrapper modules do not exist.

**Step 3: Write minimal implementation**

Implement:

- Google API service builder in `client.py`
- site list and property access checks
- raw Search Analytics query wrapper
- URL Inspection wrapper
- sitemap list/detail wrappers
- row normalization helper for performance responses

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_gsc_client.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/gsc tests/test_gsc_client.py src/CLAUDE.md tests/CLAUDE.md CLAUDE.md
git commit -m "feat: add gsc api wrappers"
```

### Task 5: Add CSV snapshot persistence

**Files:**
- Create: `src/google_search_console_mcp/snapshots/CLAUDE.md`
- Create: `src/google_search_console_mcp/snapshots/__init__.py`
- Create: `src/google_search_console_mcp/snapshots/csv_writer.py`
- Create: `tests/test_snapshot_csv.py`
- Modify: `src/CLAUDE.md`
- Modify: `tests/CLAUDE.md`
- Modify: `CLAUDE.md`

**Step 1: Write the failing test**

```python
from pathlib import Path

from google_search_console_mcp.snapshots.csv_writer import snapshot_csv_path


def test_snapshot_csv_path_normalizes_property_uri(tmp_path: Path):
    result = snapshot_csv_path(
        snapshot_root=tmp_path,
        property_uri="sc-domain:example.com",
        date="2026-04-11",
    )

    assert result == tmp_path / "gsc" / "site_daily" / "sc-domain_example.com" / "2026-04-11.csv"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_snapshot_csv.py::test_snapshot_csv_path_normalizes_property_uri -v`
Expected: FAIL because the snapshot module does not exist.

**Step 3: Write minimal implementation**

Implement:

- property path normalization
- snapshot file path builder
- single-row CSV overwrite writer for site/day facts
- snapshot listing helper
- snapshot reader helper

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_snapshot_csv.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/snapshots tests/test_snapshot_csv.py src/CLAUDE.md tests/CLAUDE.md CLAUDE.md
git commit -m "feat: add csv snapshot persistence"
```

### Task 6: Add audit logging

**Files:**
- Create: `src/google_search_console_mcp/audit.py`
- Create: `tests/test_audit.py`
- Modify: `src/CLAUDE.md`
- Modify: `tests/CLAUDE.md`

**Step 1: Write the failing test**

```python
from pathlib import Path

from google_search_console_mcp.audit import AuditLogger


def test_audit_logger_writes_jsonl_record(tmp_path: Path):
    path = tmp_path / "audit.jsonl"
    logger = AuditLogger(path)

    logger.log({"tool_name": "list_properties", "status": "ok"})

    assert path.exists()
    assert '"tool_name":"list_properties"' in path.read_text(encoding="utf-8")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_audit.py::test_audit_logger_writes_jsonl_record -v`
Expected: FAIL because the logger does not exist.

**Step 3: Write minimal implementation**

Implement JSONL append logging with:

- directory auto-create
- one-record-per-line writes
- compact JSON serialization

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_audit.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/audit.py tests/test_audit.py src/CLAUDE.md tests/CLAUDE.md
git commit -m "feat: add audit logging"
```

### Task 7: Register read-only MCP tools

**Files:**
- Create: `src/google_search_console_mcp/tools/CLAUDE.md`
- Create: `src/google_search_console_mcp/tools/__init__.py`
- Create: `src/google_search_console_mcp/tools/read_tools.py`
- Create: `src/google_search_console_mcp/tools/snapshot_tools.py`
- Create: `tests/test_tools.py`
- Modify: `src/CLAUDE.md`
- Modify: `tests/CLAUDE.md`
- Modify: `CLAUDE.md`

**Step 1: Write the failing test**

```python
from google_search_console_mcp.tools.read_tools import build_read_tool_names


def test_build_read_tool_names_matches_design():
    assert build_read_tool_names() == [
        "get_account_status",
        "list_properties",
        "get_property",
        "query_search_analytics",
        "get_site_daily_summary",
        "inspect_url",
        "list_sitemaps",
        "get_sitemap",
    ]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py::test_build_read_tool_names_matches_design -v`
Expected: FAIL because the tool modules do not exist.

**Step 3: Write minimal implementation**

Implement:

- read tool service objects
- tool argument validation
- read tool registration
- snapshot tool registration
- pure helper that exposes tool names for testing

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/tools tests/test_tools.py src/CLAUDE.md tests/CLAUDE.md CLAUDE.md
git commit -m "feat: add mcp read and snapshot tools"
```

### Task 8: Assemble the FastMCP server and CLI entrypoint

**Files:**
- Create: `src/google_search_console_mcp/server.py`
- Create: `tests/test_server.py`
- Modify: `src/CLAUDE.md`
- Modify: `tests/CLAUDE.md`

**Step 1: Write the failing test**

```python
from google_search_console_mcp.server import create_server


def test_create_server_uses_expected_name(settings_factory):
    server = create_server(settings=settings_factory())
    assert server.name == "google-search-console-mcp"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_server.py::test_create_server_uses_expected_name -v`
Expected: FAIL because the server module does not exist.

**Step 3: Write minimal implementation**

Implement:

- `create_server()`
- request metadata extraction
- audit logger wiring
- tool registration
- CLI `main()` that loads `.env`, config YAML, then runs `transport="streamable-http"`

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_server.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/server.py tests/test_server.py src/CLAUDE.md tests/CLAUDE.md
git commit -m "feat: add gsc mcp server entrypoint"
```

### Task 9: Add authentication helper CLI for first-time login

**Files:**
- Create: `src/google_search_console_mcp/cli.py`
- Create: `tests/test_cli.py`
- Modify: `src/CLAUDE.md`
- Modify: `tests/CLAUDE.md`

**Step 1: Write the failing test**

```python
from google_search_console_mcp.cli import build_parser


def test_build_parser_has_login_command():
    parser = build_parser()
    args = parser.parse_args(["auth", "login"])
    assert args.command == "auth"
    assert args.auth_command == "login"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_build_parser_has_login_command -v`
Expected: FAIL because the CLI helper does not exist.

**Step 3: Write minimal implementation**

Implement:

- parser with `auth login` and `auth status`
- login flow delegated to auth module
- no MCP tool side effects for browser launch

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/google_search_console_mcp/cli.py tests/test_cli.py src/CLAUDE.md tests/CLAUDE.md
git commit -m "feat: add auth cli helpers"
```

### Task 10: Verify the full read-only skeleton and sync docs

**Files:**
- Modify: `docs/plans/2026-04-11-google-search-console-mcp-design.md`
- Modify: `CLAUDE.md`
- Modify: `docs/CLAUDE.md`
- Modify: `docs/plans/CLAUDE.md`
- Modify: `src/CLAUDE.md`
- Modify: `tests/CLAUDE.md`

**Step 1: Write the failing test**

```python
def test_placeholder():
    assert False, "Replace with final smoke verification command"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_placeholder.py -v`
Expected: FAIL, proving the final verification task is still active.

**Step 3: Write minimal implementation**

Replace the placeholder with a real smoke path:

- run the full pytest suite
- run the CLI help command
- confirm all CLAUDE.md maps reflect the real file tree
- update the design doc only if implementation forced a justified change

**Step 4: Run test to verify it passes**

Run: `pytest -v`
Expected: PASS

Run: `python -m google_search_console_mcp.cli auth status --help`
Expected: help text renders without import errors

**Step 5: Commit**

```bash
git add docs/plans/2026-04-11-google-search-console-mcp-design.md CLAUDE.md docs/CLAUDE.md docs/plans/CLAUDE.md src/CLAUDE.md tests/CLAUDE.md
git commit -m "docs: sync gsc mcp maps and verification notes"
```
