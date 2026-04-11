"""
[INPUT]: 依赖 pathlib 与未来的 google_search_console_mcp.audit 模块
[OUTPUT]: 对外提供审计日志 JSONL 写入测试
[POS]: tests 的审计层入口，先锁定一行一记录的日志契约
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path

from google_search_console_mcp.audit import AuditLogger


def test_audit_logger_writes_jsonl_record(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    logger = AuditLogger(path)

    logger.log({"tool_name": "list_properties", "status": "ok"})

    assert path.exists()
    assert '"tool_name":"list_properties"' in path.read_text(encoding="utf-8")
