# google-search-console-mcp - 面向多站点复用的 Google Search Console MCP 读取层
Python 3.12 + FastMCP/MCP SDK + Google APIs OAuth + Search Console API + CSV snapshots + pytest

<directory>
config/ - 认证与运行配置目录，承载 OAuth client、token 与服务配置说明 (0子目录)
</directory>

<directory>
docs/ - 设计与计划文档目录，沉淀系统地图与实现路线 (1子目录: plans)
</directory>

<directory>
src/ - Python 源码目录，承载 MCP server、GSC API 封装与快照逻辑 (0子目录)
</directory>

<directory>
tests/ - pytest 测试目录，验证配置、认证、工具注册与 CSV 快照行为 (0子目录)
</directory>

<config>
CLAUDE.md - 项目 L1 宪法，定义目录骨架、技术栈与模块边界
</config>

法则: 极简·稳定·导航·版本精确
