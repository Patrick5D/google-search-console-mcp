> Historical design document. For current installation and supported behavior, see [README](../../README.md). Paths are illustrative.

# Google Search Console MCP Design

> **Historical Note:** 本文仍是项目骨架、认证、快照与模块边界设计来源；但从 `2026-04-12-gsc-agent-query-commands-design.md` 获批起，agent 查询命令面不再以本文第 4 节工具清单为准。

**目标**

构建一个面向同一 Google 账号下多个站点复用的 Google Search Console MCP。第一版严格只读，直接使用 `property_uri` 访问站点，暴露原始数据优先的查询工具，并支持手动触发 `site/day` 级 CSV 快照。

## 1. 定位

这个系统不是分析平台，不是调度器，也不是写操作控制台。它只做三件事：

1. 用本地 OAuth 用户身份访问 Google Search Console。
2. 以 MCP 工具形式暴露 GSC 的原始读取能力。
3. 在手动触发时把站点日汇总沉淀为本地 CSV。

分析结论、发布策略和内容决策属于上层使用者，不固化进 MCP 协议层。

## 2. 设计原则

- 多站点复用，单账号认证一次，按 `property_uri` 切换站点。
- 原始数据优先，保留一把通用查询刀，再补少量高频模板工具。
- 严格只读，不做 `submit_sitemap`、URL 提交或任何审批 token 机制。
- 快照显式触发，不做定时器，不做后台任务。
- CSV 只保存一种事实，不让格式承担数据库职责。

## 3. 模块骨架

建议源码模块如下：

- `src/google_search_console_mcp/server.py`
  组装 FastMCP、注册工具、注入配置与审计。
- `src/google_search_console_mcp/config.py`
  读取服务配置、OAuth 路径、快照路径和默认参数。
- `src/google_search_console_mcp/auth.py`
  加载 OAuth client 与 token，处理刷新和登录状态检查。
- `src/google_search_console_mcp/errors.py`
  定义配置、认证、参数、上游 API 和快照异常。
- `src/google_search_console_mcp/audit.py`
  写 JSONL 审计日志。
- `src/google_search_console_mcp/gsc/client.py`
  Google API 薄封装，统一创建 Search Console service。
- `src/google_search_console_mcp/gsc/sites.py`
  列 property、校验 property。
- `src/google_search_console_mcp/gsc/performance.py`
  Search Analytics 查询与站点日汇总模板查询。
- `src/google_search_console_mcp/gsc/inspection.py`
  URL Inspection 查询。
- `src/google_search_console_mcp/gsc/sitemaps.py`
  Sitemap 列表与详情读取。
- `src/google_search_console_mcp/tools/read_tools.py`
  注册读取类 MCP 工具。
- `src/google_search_console_mcp/tools/snapshot_tools.py`
  注册快照工具。
- `src/google_search_console_mcp/snapshots/csv_writer.py`
  规范化路径并落盘 CSV。

## 4. MCP 工具清单

### 4.1 站点与认证

- `get_account_status()`
  返回 token 是否存在、是否可刷新、OAuth 配置路径是否有效。
- `list_properties()`
  列出当前账号下可访问的全部 Search Console properties。
- `get_property(property_uri)`
  校验某个 property 是否存在且当前账号有权限。

### 4.2 性能查询

- `query_search_analytics(property_uri, start_date, end_date, dimensions, row_limit, start_row, dimension_filter_groups, search_type, data_state, aggregation_type)`
  对应 Search Analytics 的通用原始查询入口。
- `get_site_daily_summary(property_uri, start_date, end_date, search_type="web")`
  固定按日期聚合的站点日汇总读取工具。

### 4.3 URL 与 Sitemap

- `inspect_url(property_uri, inspection_url)`
  查询单 URL 的索引状态、canonical 与覆盖信息。
- `list_sitemaps(property_uri)`
  读取某个 property 的 sitemap 列表。
- `get_sitemap(property_uri, sitemap_url)`
  读取单个 sitemap 的状态与元数据。

### 4.4 快照

- `snapshot_site_day(property_uri, date, search_type="web")`
  拉取单天站点汇总并写入 CSV。
- `list_snapshots(property_uri | null = null)`
  查看本地已存在的快照文件。
- `read_snapshot(snapshot_path, limit | null = null)`
  读取某个快照文件的内容，便于 MCP 客户端继续分析。

## 5. CSV 快照设计

### 5.1 目录布局

快照目录固定为：

`snapshots/gsc/site_daily/<normalized_property>/<date>.csv`

示例：

- `snapshots/gsc/site_daily/sc-domain_example.com/2026-04-11.csv`
- `snapshots/gsc/site_daily/https_www.example.com/2026-04-11.csv`

`normalized_property` 使用稳定规则将 `:`、`/`、`.` 等字符转为路径安全形式。

### 5.2 字段

CSV 字段固定为：

- `snapshot_date`
- `property_uri`
- `search_type`
- `data_state`
- `clicks`
- `impressions`
- `ctr`
- `average_position`
- `api_start_date`
- `api_end_date`
- `captured_at_utc`

### 5.3 写入策略

- 每个 `property_uri + date + search_type` 对应一个独立文件。
- 默认覆盖写入，保证一次快照动作对应一个可审计结果。
- 不做全局大表 append，避免时间与站点事实混成泥团。

## 6. OAuth 认证设计

### 6.1 文件

- `config/oauth_client.json`
  Google OAuth client 配置。
- `config/token.json`
  用户 token 与 refresh token。
- `.env`
  可选覆盖路径，例如 `GSC_OAUTH_CLIENT_PATH`、`GSC_TOKEN_PATH`。

### 6.2 流程

1. CLI 或显式认证入口读取 `oauth_client.json`。
2. 检查 `token.json` 是否存在。
3. 不存在则走浏览器 OAuth 授权。
4. 写入 `token.json`。
5. 查询时只负责加载、刷新或在失败时抛出明确认证错误。

认证副作用与查询工具解耦，不在首次查询时隐式弹浏览器。

## 7. 错误与审计

### 7.1 异常类型

- `ConfigError`
- `AuthError`
- `AuthorizationError`
- `ValidationError`
- `UpstreamApiError`
- `SnapshotError`

原则是：参数错、认证错、权限错、上游错各自归位，避免“Google API error”一锅炖。

### 7.2 审计日志

保留本地 `JSONL` 审计日志，字段至少包括：

- `timestamp`
- `request_id`
- `tool_name`
- `property_uri`
- `args_summary`
- `status`
- `error_type`
- `snapshot_path`
- `agent_id`

记录摘要，不保存 token，不保存无必要的大响应正文。

## 8. 测试策略

第一版测试覆盖：

- `test_config.py`：配置解析与默认值。
- `test_auth.py`：token 存在、刷新与失效。
- `test_gsc_client.py`：Google API 封装的 mock 行为。
- `test_tools.py`：MCP 工具注册、参数校验、错误映射。
- `test_snapshot_csv.py`：CSV 字段、路径规范化与覆盖写入。
- `test_server.py`：FastMCP 组装与工具挂载。

不做真实在线 OAuth E2E，不做自动调度测试，不做分析型工具测试。

## 9. 明确不做

- 不做 `submit_sitemap`
- 不做单 URL 请求收录
- 不做自动快照调度
- 不做 `page/day`、`query/day`、`page-query/day` 快照
- 不做内置分析工具
- 不做数据库存储

## 10. 演进顺序

正确的扩展顺序应当是：

1. 增加 `page/day` 快照
2. 增加 query 相关快照
3. 引入 DuckDB 或 SQLite 作为分析层
4. 最后才考虑结论型 MCP 工具

先把事实稳定下来，再谈分析。反过来做，只会让协议层长出偏见和坏味道。
