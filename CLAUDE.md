# google-search-console-mcp - 面向多站点的 Google Search Console MCP 读取与分析层
Python 3.12 + FastMCP/MCP SDK 1.x + Google APIs OAuth + Search Console API + CSV snapshots + pytest

<directory>
.github/ - 持续集成目录，验证测试、HTTP 与构建 (1子目录: workflows)
</directory>

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
.env.example - 配置迁移说明，指向 YAML 与 CLI 参数
</config>

<config>
pyproject.toml - 包元数据与 SDK 1.x 依赖边界，声明 README、MIT 与测试依赖
</config>

法则: 极简·稳定·导航·版本精确

接口约定：Search Analytics 工具返回 rows/meta。分析工具返回 items/meta。
数据约定：日期采用 PT，CTR 采用比例。缺失行不等于零。
运行边界：默认绑定本机，只读 Google 数据；快照显式写入本地。

<config>
README.md - 英文安装、授权、连接与工具使用入口
LICENSE - MIT 使用与分发许可
CONTRIBUTING.md - 开发、测试、文档与贡献约定
</config>

<config>
MANIFEST.in - 源码包白名单，包含安装示例、测试与公开协议文档
</config>
