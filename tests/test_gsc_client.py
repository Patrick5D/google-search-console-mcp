"""
[INPUT]: 依赖未来的 google_search_console_mcp.gsc.performance 模块
[OUTPUT]: 对外提供 Search Analytics 行归一化测试
[POS]: tests 的 GSC API 包装层入口，先锁定原始响应到稳定字段的折叠规则
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from google_search_console_mcp.gsc.performance import normalize_search_analytics_row


def test_normalize_search_analytics_row_flattens_metrics() -> None:
    row = {
        "keys": ["2026-04-10"],
        "clicks": 10,
        "impressions": 100,
        "ctr": 0.1,
        "position": 3.2,
    }

    result = normalize_search_analytics_row(["date"], row)

    assert result["date"] == "2026-04-10"
    assert result["clicks"] == 10
    assert result["average_position"] == 3.2
