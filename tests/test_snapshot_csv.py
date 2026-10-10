"""
[INPUT]: 依赖 pathlib 与 snapshots.csv_writer 的路径构造器
[OUTPUT]: 验证站点、搜索类型、日期到 CSV 路径的映射
[POS]: tests 的快照层入口，锁定搜索类型隔离后的默认 Web 路径
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path

from google_search_console_mcp.snapshots.csv_writer import snapshot_csv_path


def test_snapshot_csv_path_normalizes_property_uri(tmp_path: Path) -> None:
    result = snapshot_csv_path(
        snapshot_root=tmp_path,
        property_uri="sc-domain:example.com",
        date="2026-04-11",
    )

    assert result == tmp_path / "gsc" / "site_daily" / "sc-domain_example.com" / "web" / "2026-04-11.csv"
