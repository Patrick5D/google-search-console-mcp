"""
[INPUT]: 依赖 MCP 参数契约、工具描述与站点日汇总查询与 CSV 快照写入器
[OUTPUT]: 对外提供 SnapshotToolService 与 register_snapshot_tools
[POS]: tools 的快照装配器，把 site/day 汇总折叠成显式快照动作
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..audit import AuditLogger
from ..config import Settings
from ..gsc.validation import SearchType
from .contracts import DESCRIPTIONS
from mcp.types import ToolAnnotations
from ..errors import SnapshotError
from ..snapshots.csv_writer import (
    list_snapshot_files,
    read_snapshot_rows,
    write_site_day_snapshot,
)
from .read_tools import ReadToolService


@dataclass
class SnapshotToolService:
    settings: Settings
    read_service: ReadToolService
    audit_logger: AuditLogger | None = None

    def _audit(self, *, tool_name: str, status: str, args_summary: dict[str, object], error_type: str | None = None):
        if self.audit_logger is None:
            return
        record: dict[str, object] = {
            "tool_name": tool_name,
            "status": status,
            "args_summary": args_summary,
        }
        if error_type is not None:
            record["error_type"] = error_type
        self.audit_logger.log(record)

    def _assert_snapshot_path_is_within_root(self, snapshot_path: str | Path) -> Path:
        root = Path(self.settings.paths.snapshot_root).resolve()
        path = Path(snapshot_path).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise SnapshotError(f"snapshot path outside snapshot root: {path}") from exc
        return path

    def snapshot_site_day(self, *, property_uri: str, date: str, search_type: SearchType = "web"):
        args_summary = {"property_uri": property_uri, "date": date, "search_type": search_type}
        try:
            rows = self.read_service.get_site_daily_summary(
                property_uri=property_uri,
                start_date=date,
                end_date=date,
                search_type=search_type,
            )
            if not rows:
                raise SnapshotError(f"no site-day data returned for {property_uri} on {date}")
            row = rows[0]
            payload = {
                "snapshot_date": date,
                "property_uri": property_uri,
                "search_type": search_type,
                "data_state": "final",
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": row.get("ctr", 0.0),
                "average_position": row.get("average_position", 0.0),
                "api_start_date": date,
                "api_end_date": date,
                "captured_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            path = write_site_day_snapshot(
                snapshot_root=self.settings.paths.snapshot_root,
                property_uri=property_uri,
                date=date,
                row=payload,
            )
        except Exception as exc:
            self._audit(tool_name="snapshot_site_day", status="error", args_summary=args_summary, error_type=type(exc).__name__)
            raise
        self._audit(tool_name="snapshot_site_day", status="ok", args_summary={**args_summary, "snapshot_path": str(path)})
        return str(path)

    def list_snapshots(self, property_uri: str | None = None):
        args_summary = {"property_uri": property_uri}
        try:
            result = [str(path) for path in list_snapshot_files(self.settings.paths.snapshot_root, property_uri)]
        except Exception as exc:
            self._audit(tool_name="list_snapshots", status="error", args_summary=args_summary, error_type=type(exc).__name__)
            raise
        self._audit(tool_name="list_snapshots", status="ok", args_summary=args_summary)
        return result

    def read_snapshot(self, snapshot_path: str):
        args_summary = {"snapshot_path": snapshot_path}
        try:
            safe_path = self._assert_snapshot_path_is_within_root(snapshot_path)
            result = read_snapshot_rows(safe_path)
        except Exception as exc:
            self._audit(tool_name="read_snapshot", status="error", args_summary=args_summary, error_type=type(exc).__name__)
            raise
        self._audit(tool_name="read_snapshot", status="ok", args_summary=args_summary)
        return result


def register_snapshot_tools(mcp, *, snapshot_service: SnapshotToolService):
    @mcp.tool(name="snapshot_site_day", description=DESCRIPTIONS["snapshot_site_day"], annotations=ToolAnnotations(readOnlyHint=False))
    def _snapshot_site_day(property_uri: str, date: str, search_type: SearchType = "web"):
        return snapshot_service.snapshot_site_day(property_uri=property_uri, date=date, search_type=search_type)

    @mcp.tool(name="list_snapshots", description=DESCRIPTIONS["list_snapshots"], annotations=ToolAnnotations(readOnlyHint=True))
    def _list_snapshots(property_uri: str | None = None):
        return snapshot_service.list_snapshots(property_uri)

    @mcp.tool(name="read_snapshot", description=DESCRIPTIONS["read_snapshot"], annotations=ToolAnnotations(readOnlyHint=True))
    def _read_snapshot(snapshot_path: str):
        return snapshot_service.read_snapshot(snapshot_path)
