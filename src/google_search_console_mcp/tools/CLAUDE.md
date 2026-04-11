# tools/
> L2 | 父级: /Users/celeste/Documents/GitHub/google-search-console-mcp/src/CLAUDE.md

成员清单
CLAUDE.md: 工具层地图，约束注册函数只做协议装配不做业务判断
__init__.py: 工具子包入口，暴露命名边界
read_tools.py: 只读工具服务与注册器，连接认证层与 GSC 包装层
snapshot_tools.py: 快照工具服务与注册器，连接日汇总查询与 CSV 写入

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
