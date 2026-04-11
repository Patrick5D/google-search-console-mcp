# src/
> L2 | 父级: /Users/celeste/Documents/GitHub/google-search-console-mcp/CLAUDE.md

成员清单
CLAUDE.md: 源码目录地图，定义 MCP 入口、GSC 客户端与快照写入层的未来边界
google_search_console_mcp/: 主包目录，承载配置、认证、server、GSC API、快照与工具装配
google_search_console_mcp/__init__.py: 包入口，导出版本信息与顶层模块边界
google_search_console_mcp/auth.py: 认证层，负责 OAuth 文件状态探测、token 加载与刷新边界
google_search_console_mcp/audit.py: 审计层，负责 MCP 工具调用的本地 JSONL 记录
google_search_console_mcp/cli.py: 命令行入口，负责显式触发 auth login/status 等交互流程
google_search_console_mcp/server.py: MCP 入口，负责 FastMCP 组装、环境加载与工具注册
google_search_console_mcp/gsc/: GSC API 包装层，折叠站点、性能、URL 检查与 sitemap 读取能力
google_search_console_mcp/snapshots/: 快照层，负责 site/day CSV 的路径规范化与落盘
google_search_console_mcp/tools/: 工具层，负责把认证、GSC 读取与快照能力折叠成 MCP 工具
google_search_console_mcp/errors.py: 异常定义层，区分配置、认证、权限、上游 API 与快照错误
google_search_console_mcp/config.py: 配置入口，负责读取 server/paths YAML 并生成 Settings

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
