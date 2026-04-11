"""
[INPUT]: 依赖 csv、pathlib 与本地字典行数据
[OUTPUT]: 对外提供 snapshot_csv_path、write_site_day_snapshot、list_snapshot_files、read_snapshot_rows
[POS]: snapshots 的核心写入器，负责把站点日事实稳定落成单文件 CSV
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import csv
from pathlib import Path

from ..errors import SnapshotError

SITE_DAY_FIELDS = [
    "snapshot_date",
    "property_uri",
    "search_type",
    "data_state",
    "clicks",
    "impressions",
    "ctr",
    "average_position",
    "api_start_date",
    "api_end_date",
    "captured_at_utc",
]


def normalize_property_uri(property_uri: str) -> str:
    normalized = property_uri.strip()
    for old, new in (("://", "_"), (":", "_"), ("/", "_"), (".", ".")):
        normalized = normalized.replace(old, new)
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized


def snapshot_csv_path(*, snapshot_root: str | Path, property_uri: str, date: str) -> Path:
    root = Path(snapshot_root)
    return root / "gsc" / "site_daily" / normalize_property_uri(property_uri) / f"{date}.csv"


def write_site_day_snapshot(
    *,
    snapshot_root: str | Path,
    property_uri: str,
    date: str,
    row: dict[str, object],
) -> Path:
    target = snapshot_csv_path(snapshot_root=snapshot_root, property_uri=property_uri, date=date)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=SITE_DAY_FIELDS)
            writer.writeheader()
            writer.writerow({field: row.get(field, "") for field in SITE_DAY_FIELDS})
    except OSError as exc:
        raise SnapshotError(f"failed to write snapshot: {target}") from exc
    return target


def list_snapshot_files(snapshot_root: str | Path, property_uri: str | None = None) -> list[Path]:
    root = Path(snapshot_root) / "gsc" / "site_daily"
    if property_uri is not None:
        root = root / normalize_property_uri(property_uri)
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.csv") if path.is_file())


def read_snapshot_rows(snapshot_path: str | Path) -> list[dict[str, str]]:
    path = Path(snapshot_path)
    if not path.exists():
        raise SnapshotError(f"missing snapshot file: {path}")
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError as exc:
        raise SnapshotError(f"failed to read snapshot: {path}") from exc
