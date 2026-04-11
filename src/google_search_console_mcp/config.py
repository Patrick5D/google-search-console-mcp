"""
[INPUT]: 依赖 pathlib、yaml 与 pydantic，读取 server/paths YAML 配置
[OUTPUT]: 对外提供 ServerSettings、PathSettings、Settings 与 load_settings
[POS]: google_search_console_mcp 的配置入口，负责把分散配置折叠成统一 Settings
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from .errors import ConfigError


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8765
    agent_header_name: str = "x-agent-id"


class PathSettings(BaseModel):
    oauth_client_path: str = "./config/oauth_client.json"
    token_path: str = "./config/token.json"
    audit_log_path: str = "./logs/audit.jsonl"
    snapshot_root: str = "./snapshots"


class Settings(BaseModel):
    server: ServerSettings = Field(default_factory=ServerSettings)
    paths: PathSettings = Field(default_factory=PathSettings)


def _read_yaml(path: Path) -> dict[str, object]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except FileNotFoundError as exc:
        raise ConfigError(f"missing config file: {path}") from exc


def load_settings(server_path: str | Path, paths_path: str | Path) -> Settings:
    server_data = _read_yaml(Path(server_path))
    paths_data = _read_yaml(Path(paths_path))
    return Settings(**server_data, **paths_data)
