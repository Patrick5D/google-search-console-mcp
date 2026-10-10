# google_search_console_mcp/
> L2 | 父级: ../CLAUDE.md

成员清单
CLAUDE.md: 主包地图，约束配置、认证、server、GSC API、快照与工具层的职责边界
__init__.py: 包入口，导出版本信息与顶层命名空间
auth.py: OAuth 认证层，负责状态探测、凭据加载、刷新与交互式登录
analysis.py: 确定性分析层，按观测值生成对比与候选，保留各窗口取数范围
audit.py: 审计层，负责 MCP 调用摘要的 JSONL 记录与运行时可追踪性
cli.py: CLI 入口，负责 auth login/status 命令面
config.py: 配置层，负责读取 server/paths YAML 并生成 Settings
errors.py: 异常边界层，统一定义配置、认证、权限、上游与快照错误
server.py: FastMCP 入口，组装 30 个工具，覆盖读取、分析与本地快照
gsc/: Google Search Console API 薄封装层
snapshots/: CSV 快照层
tools/: MCP 工具装配层，装配读取、分析与快照命令，输出协议描述和元信息

portfolio_analysis.py: 跨站与搜索类型对照，保留逐站错误与缺失侧，不合计重叠站点
ctr_benchmark.py: 本站 CTR 对照，按排名区间剔除目标页面，报告样本门槛与覆盖率

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
