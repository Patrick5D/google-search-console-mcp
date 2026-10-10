# tools/
> L2 | 父级: ../CLAUDE.md

成员清单
CLAUDE.md: 工具层地图，约束注册函数只做协议装配不做业务判断
__init__.py: 工具子包入口，暴露命名边界
read_tools.py: 只读工具服务与注册器，连接认证层、GSC 模板查询与 batch inspection
snapshot_tools.py: 快照工具服务与注册器，连接日汇总查询与 CSV 写入

analysis_tools.py: 分析工具装配器，复用读取服务的认证与审计，注册七个分析命令，共享筛选参数
contracts.py: MCP 协议契约，提供参数约束、工具说明与 rows/meta 输出转换

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
