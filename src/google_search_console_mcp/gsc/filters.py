"""
[INPUT]: 依赖 Pydantic 与正则转义
[OUTPUT]: 提供 AnalysisFilters 与 build_filter_groups
[POS]: gsc 的分析筛选契约；各分析工具共享 AND 语义
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalysisFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    country: str | None = Field(default=None, pattern=r"^[A-Za-z]{3}$", description="ISO alpha-3 country, e.g. usa.")
    device: Literal["MOBILE", "DESKTOP", "TABLET"] | None = None
    page_prefix: str | None = Field(default=None, pattern=r"^/", max_length=1000, description="Literal URL path prefix; query strings excluded.")
    query_include: str | None = Field(default=None, min_length=1, max_length=4096, description="RE2 regex of queries to include; supports brand alternatives.")
    query_exclude: str | None = Field(default=None, min_length=1, max_length=4096, description="RE2 regex of queries to exclude; combined with other filters using AND.")

    @field_validator("device", mode="before")
    @classmethod
    def upper_device(cls, value):
        return value.upper() if isinstance(value, str) else value


def build_filter_groups(filters: AnalysisFilters | dict | None):
    selected = AnalysisFilters.model_validate(filters or {})
    values = []
    for dimension, value in [("country", selected.country.lower() if selected.country else None), ("device", selected.device)]:
        if value:
            values.append({"dimension": dimension, "operator": "equals", "expression": value})
    if selected.page_prefix:
        values.append({"dimension": "page", "operator": "includingRegex",
                       "expression": r"^https?://[^/?#]+" + re.escape(selected.page_prefix)})
    for operator, value in [("includingRegex", selected.query_include), ("excludingRegex", selected.query_exclude)]:
        if value:
            values.append({"dimension": "query", "operator": operator, "expression": value})
    return [{"groupType": "and", "filters": values}] if values else []
