"""
[INPUT]: 依赖站点日汇总查询与 CSV 快照写入器
[OUTPUT]: 对外提供 SnapshotToolService 与 register_snapshot_tools
[POS]: tools 的快照装配器，把 site/day 汇总折叠成显式快照动作
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Settings
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

    def snapshot_site_day(self, *, property_uri: str, date: str, search_type: str = "web"):
        rows = self.read_service.get_site_daily_summary(
            property_uri=property_uri,
            start_date=date,
            end_date=date,
            search_type=search_type,
        )
        row = rows[0] if rows else {}
        payload = {
            "snapshot_date": date,
            "property_uri": property_uri,
            "search_type": search_type,
            "data_state": "",
            "clicks": row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr": row.get("ctr", 0.0),
            "average_position": row.get("average_position", 0.0),
            "api_start_date": date,
            "api_end_date": date,
            "captured_at_utc": "",
        }
        return str(
            write_site_day_snapshot(
                snapshot_root=self.settings.paths.snapshot_root,
                property_uri=property_uri,
                date=date,
                row=payload,
            )
        )

    def list_snapshots(self, property_uri: str | None = None):
        return [str(path) for path in list_snapshot_files(self.settings.paths.snapshot_root, property_uri)]

    def read_snapshot(self, snapshot_path: str):
        return read_snapshot_rows(snapshot_path)


def register_snapshot_tools(mcp, *, snapshot_service: SnapshotToolService):
    @mcp.tool(name="snapshot_site_day")
    def _snapshot_site_day(property_uri: str, date: str, search_type: str = "web"):
        return snapshot_service.snapshot_site_day(property_uri=property_uri, date=date, search_type=search_type)

    @mcp.tool(name="list_snapshots")
    def _list_snapshots(property_uri: str | None = None):
        return snapshot_service.list_snapshots(property_uri)

    @mcp.tool(name="read_snapshot")
    def _read_snapshot(snapshot_path: str):
        return snapshot_service.read_snapshot(snapshot_path)
