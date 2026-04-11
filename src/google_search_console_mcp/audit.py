"""
[INPUT]: 依赖 json、datetime 与 pathlib，接收工具调用摘要字典
[OUTPUT]: 对外提供 AuditLogger
[POS]: google_search_console_mcp 的审计层，被 server 与工具服务共享
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class AuditLogger:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def log(self, record: dict[str, object]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **record}
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))
            handle.write("\n")
