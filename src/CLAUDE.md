# src/
> L2 | 父级: /Users/celeste/Documents/GitHub/google-search-console-mcp/CLAUDE.md

成员清单
CLAUDE.md: 源码目录地图，定义 MCP 入口、GSC 客户端与快照写入层的未来边界
google_search_console_mcp/__init__.py: 包入口，导出版本信息与顶层模块边界
google_search_console_mcp/auth.py: 认证层，负责 OAuth 文件状态探测、token 加载与刷新边界
google_search_console_mcp/gsc/: GSC API 包装层，折叠站点、性能、URL 检查与 sitemap 读取能力
google_search_console_mcp/errors.py: 异常定义层，区分配置、认证、权限、上游 API 与快照错误
google_search_console_mcp/config.py: 配置入口，负责读取 server/paths YAML 并生成 Settings

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
