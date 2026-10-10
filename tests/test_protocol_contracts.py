"""
[INPUT]: 依赖 FastMCP、查询校验与 Google 请求错误边界
[OUTPUT]: 验证协议描述、参数约束、元信息与重试分类
[POS]: tests 的 MCP 契约回归；模拟 Google 错误并禁止真实网络请求
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
import asyncio
import json

import httplib2
import pytest
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

from google_search_console_mcp.config import Settings
from google_search_console_mcp.errors import AuthorizationError, QuotaError, UpstreamApiError, ValidationError
from google_search_console_mcp.gsc.query import query_search_analytics
from google_search_console_mcp.gsc.request import execute_read
from google_search_console_mcp.server import create_server
from google_search_console_mcp.tools.read_tools import ReadToolService, register_read_tools
from test_query_integrity import ARGS, PagedService, raw


def test_all_tools_have_descriptions_and_query_constraints():
    tools = asyncio.run(create_server(settings=Settings()).list_tools())
    assert all(t.description and len(t.description) > 35 for t in tools)
    query = next(t for t in tools if t.name == "query_search_analytics")
    props = query.inputSchema["properties"]
    assert props["row_limit"]["maximum"] == 25000
    assert props["start_row"]["minimum"] == 0
    assert "discover" in props["search_type"]["enum"]
    assert "meta" in query.description


def test_mcp_query_returns_metadata_and_rejects_bad_input():
    service = PagedService([raw("https://example.com/a")])
    mcp = FastMCP("test")
    register_read_tools(mcp, read_service=ReadToolService(Settings(), service_factory=lambda **kw: service))
    async def run():
        blocks = await mcp.call_tool("query_search_analytics", {**ARGS, "dimensions": ["page"]})
        if isinstance(blocks, tuple):
            blocks = blocks[0]
        payload = json.loads(blocks[0].text)
        assert payload["rows"][0]["page"] == "https://example.com/a"
        assert payload["meta"]["timezone"] == "America/Los_Angeles"
        with pytest.raises(Exception, match="25000"):
            await mcp.call_tool("query_search_analytics", {**ARGS, "row_limit": 25001})
    asyncio.run(run())


@pytest.mark.parametrize("overrides", [
    {"start_date": "2026-10-01"}, {"row_limit": 0}, {"start_row": -1},
    {"search_type": "fake"}, {"dimensions": ["page", "page"]},
    {"dimensions": ["query"], "search_type": "discover"},
    {"data_state": "hourly_all"}, {"dimensions": ["page"], "aggregation_type": "byProperty"},
    {"dimension_filter_groups": [{"groupType": "or", "filters": []}]},
])
def test_invalid_query_fails_before_google(overrides):
    service = PagedService([])
    with pytest.raises(ValidationError):
        query_search_analytics(service, **{**ARGS, **overrides})
    assert not service.calls


def http_error(status, reason):
    return HttpError(httplib2.Response({"status": str(status)}),
                     json.dumps({"error": {"message": reason, "errors": [{"reason": reason}]}}).encode())


class Request:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.calls = 0

    def execute(self):
        self.calls += 1
        result = next(self.outcomes)
        if isinstance(result, Exception):
            raise result
        return result


def test_transient_errors_retry_and_success_is_returned(monkeypatch):
    sleeps = []
    monkeypatch.setattr("google_search_console_mcp.gsc.request.time.sleep", sleeps.append)
    request = Request([http_error(429, "rateLimitExceeded"), http_error(503, "backendError"), {"rows": []}])
    assert execute_read(request) == {"rows": []}
    assert request.calls == 3
    assert sleeps == [1, 2]


@pytest.mark.parametrize("status,reason,error", [
    (403, "dailyLimitExceeded", QuotaError), (403, "forbidden", AuthorizationError),
    (400, "invalidParameter", ValidationError),
])
def test_permanent_errors_do_not_retry(status, reason, error):
    request = Request([http_error(status, reason)])
    with pytest.raises(error):
        execute_read(request)
    assert request.calls == 1


def test_retry_budget_is_bounded(monkeypatch):
    monkeypatch.setattr("google_search_console_mcp.gsc.request.time.sleep", lambda _: None)
    request = Request([http_error(503, "backendError") for _ in range(3)])
    with pytest.raises(UpstreamApiError, match="retries exhausted"):
        execute_read(request)
    assert request.calls == 3


@pytest.mark.parametrize("failure", [TimeoutError, ConnectionError])
def test_transport_failures_have_bounded_retries_and_normalized_errors(monkeypatch, failure):
    monkeypatch.setattr("google_search_console_mcp.gsc.request.time.sleep", lambda _: None)
    request = Request([failure("network failed") for _ in range(3)])
    with pytest.raises(UpstreamApiError, match="transport failure"):
        execute_read(request)
    assert request.calls == 3
