# google_search_console_mcp/
> L2 | 父级: /Users/celeste/Documents/GitHub/google-search-console-mcp/src/CLAUDE.md

成员清单
CLAUDE.md: 主包地图，约束配置、认证、server、GSC API、快照与工具层的职责边界
__init__.py: 包入口，导出版本信息与顶层命名空间
auth.py: OAuth 认证层，负责状态探测、凭据加载、刷新与交互式登录
audit.py: 审计层，负责 MCP 调用摘要的 JSONL 记录
cli.py: CLI 入口，负责 auth login/status 命令面
config.py: 配置层，负责读取 server/paths YAML 并生成 Settings
errors.py: 异常边界层，统一定义配置、认证、权限、上游与快照错误
server.py: FastMCP 入口，负责组装工具与运行服务
gsc/: Google Search Console API 薄封装层
snapshots/: CSV 快照层
tools/: MCP 工具装配层

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
