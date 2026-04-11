"""
[INPUT]: 依赖 pathlib 与未来的 google_search_console_mcp.snapshots.csv_writer 模块
[OUTPUT]: 对外提供快照 CSV 路径规范化测试
[POS]: tests 的快照层入口，先锁定 property URI 到磁盘路径的映射
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

    assert result == tmp_path / "gsc" / "site_daily" / "sc-domain_example.com" / "2026-04-11.csv"
