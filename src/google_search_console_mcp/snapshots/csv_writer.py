"""
[INPUT]: 依赖 csv、pathlib、共享日期校验与本地字典行数据
[OUTPUT]: 对外提供 snapshot_csv_path、write_site_day_snapshot、list_snapshot_files、read_snapshot_rows
[POS]: snapshots 的核心写入器，按站点、搜索类型、日期隔离 CSV；递归读取旧快照
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import csv
from typing import get_args
from pathlib import Path

from ..errors import SnapshotError, ValidationError
from ..gsc.validation import SearchType, parse_date

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


def snapshot_csv_path(*, snapshot_root: str | Path, property_uri: str, date: str, search_type: str = "web") -> Path:
    if search_type not in get_args(SearchType):
        raise SnapshotError("unsupported search_type")
    try:
        parse_date(date)
    except ValidationError as exc:
        raise SnapshotError("date must be YYYY-MM-DD") from exc
    root = Path(snapshot_root).resolve()
    target = root / "gsc" / "site_daily" / normalize_property_uri(property_uri) / search_type / f"{date}.csv"
    if not target.resolve().is_relative_to(root):
        raise SnapshotError("snapshot path outside snapshot root")
    return target


def write_site_day_snapshot(
    *,
    snapshot_root: str | Path,
    property_uri: str,
    date: str,
    row: dict[str, object],
) -> Path:
    target = snapshot_csv_path(snapshot_root=snapshot_root, property_uri=property_uri, date=date, search_type=str(row.get("search_type", "web")))
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
