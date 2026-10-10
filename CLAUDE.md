# google-search-console-mcp - 面向多站点的 Google Search Console MCP 读取与分析层
Python 3.12 + FastMCP/MCP SDK + Google APIs OAuth + Search Console API + CSV snapshots + pytest

<directory>
config/ - 认证与运行配置目录，承载 OAuth client、token 与服务配置说明 (0子目录)
</directory>

<directory>
docs/ - 设计与计划文档目录，沉淀系统地图与实现路线 (1子目录: plans)
</directory>

<directory>
src/ - Python 源码目录，承载 MCP server、有界取数、确定性分析与快照逻辑 (1子目录: google_search_console_mcp)
</directory>

<directory>
tests/ - pytest 测试目录，验证配置、认证、工具注册与 CSV 快照行为 (0子目录)
</directory>

<config>
CLAUDE.md - 项目 L1 宪法，定义目录骨架、技术栈与模块边界
</config>

<config>
.gitignore - 本地环境、凭据、缓存与快照忽略规则，保持仓库输出干净
</config>

<config>
.env.example - 本地环境变量模板，声明 OAuth 与配置路径入口
</config>

<config>
pyproject.toml - Python 项目元数据与依赖定义，提供 uv/pytest 运行基础
</config>

法则: 极简·稳定·导航·版本精确

接口约定：Search Analytics 工具返回 rows/meta。分析工具返回 items/meta。
数据约定：日期采用 PT，CTR 采用比例。缺失行不等于零。
运行边界：默认绑定本机，只读 Google 数据；快照显式写入本地。
