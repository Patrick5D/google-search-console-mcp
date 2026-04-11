"""
[INPUT]: 无运行时强依赖，仅作为包入口参与模块发现
[OUTPUT]: 对外提供 __version__ 常量
[POS]: google_search_console_mcp 包根，约束子模块从这里向外暴露
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

__version__ = "0.1.0"
