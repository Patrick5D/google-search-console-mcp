> Historical design document. For current installation and supported behavior, see [README](../../README.md). Paths are illustrative.

# GSC Agent Query Commands Design

**目标**

在现有 `google-search-console-mcp` 只读骨架上，补一套主要给 AI agent 使用的高频查询命令面。命令优先表达任务语义，而不是暴露底层 API mode；全部围绕单个 `property_uri` 工作，不做多站点聚合。

> **Canonical Note:** 从本设计稿获批起，agent 查询命令面以本文为准。`2026-04-11-google-search-console-mcp-design.md` 与 `2026-04-11-google-search-console-mcp.md` 中旧的工具清单仅保留为骨架阶段历史记录，不再作为命令面真相源。

## 1. 设计约束

- 主要使用者是 AI agent，不以人类终端输入体验为中心。
- 单个命令只回答一个稳定问题，不做“万能超级命令”。
- 仍保留 `query_search_analytics` 作为底层兜底能力。
- 所有模板命令都是只读，不产生写操作副作用。
- 所有模板命令默认只服务单个 `property_uri`。
- 不新增任何内置分析结论，不做“低 CTR 页面”“掉量页面”判定。

## 2. 统一命名与参数约定

### 2.1 命名

- 发现类使用 `list_*` / `get_*`
- 趋势类使用 `*_trend`
- 关系类使用 `page_queries` / `query_pages`
- 批量 URL 检查使用 `inspect_*_batch`

### 2.2 统一参数

除站点发现命令与 inspection 命令外，所有查询命令都要求：

- `property_uri`
- `start_date`
- `end_date`

高频可选参数：

- `search_type="web"`
- `row_limit`
- `start_row`
- `metric`

`metric` 仅允许：

- `clicks`
- `impressions`
- `ctr`
- `average_position`

排序契约固定如下：

- `clicks`、`impressions`、`ctr` 按降序排序
- `average_position` 按升序排序

## 3. 命令分层

### 3.1 站点发现

- `get_account_status()`
  检查 OAuth client、token 和 ready 状态。

- `list_properties()`
  返回当前账号可访问的全部 Search Console properties。

- `get_property(property_uri)`
  校验某个 property 是否存在且可访问。

### 3.2 站点整体表现

- `get_site_daily_summary(property_uri, start_date, end_date, search_type="web")`
  返回按 `date` 聚合的站点整体表现。

- `get_site_summary_by_device(property_uri, start_date, end_date, search_type="web", row_limit=10, start_row=0)`
  返回按 `device` 聚合的站点表现。

- `get_site_summary_by_country(property_uri, start_date, end_date, search_type="web", row_limit=50, start_row=0)`
  返回按 `country` 聚合的站点表现。

**明确不做**

- `get_site_summary_by_date_and_country`
- `get_site_summary_by_date_and_device`

这两个命令价值不够高，而且容易和底层 `query_search_analytics` 重复。保留它们只会膨胀命令面，不会显著降低 agent 负担。

### 3.3 页面相关

- `get_top_pages(property_uri, start_date, end_date, metric="clicks", search_type="web", row_limit=50, start_row=0)`
  返回站点在时间窗口内表现最强的页面列表。

- `get_page_trend(property_uri, page, start_date, end_date, search_type="web")`
  返回单个页面按 `date` 聚合的表现趋势。

- `get_pages_by_path_prefix(property_uri, path_prefix, start_date, end_date, metric="clicks", search_type="web", row_limit=100, start_row=0)`
  返回匹配某个路径前缀的页面表现。

- `get_page_queries(property_uri, page, start_date, end_date, metric="clicks", search_type="web", row_limit=100, start_row=0)`
  返回某个页面对应的查询词列表。

- `get_page_query_pairs(property_uri, page, start_date, end_date, search_type="web", row_limit=200, start_row=0)`
  返回页面固定条件下的 `page + query` 组合结果。

### 3.4 查询词相关

- `get_top_queries(property_uri, start_date, end_date, metric="clicks", search_type="web", row_limit=100, start_row=0)`
  返回站点在时间窗口内的高价值 query 列表。

- `get_query_trend(property_uri, query, start_date, end_date, search_type="web")`
  返回单个 query 按 `date` 聚合的趋势。

- `get_query_pages(property_uri, query, start_date, end_date, metric="clicks", search_type="web", row_limit=100, start_row=0)`
  返回某个 query 主要由哪些页面承接。

- `get_query_page_pairs(property_uri, query, start_date, end_date, search_type="web", row_limit=200, start_row=0)`
  返回 query 固定条件下的 `query + page` 组合结果。

### 3.5 URL 检查

- `inspect_url(property_uri, inspection_url)`
  返回单个 URL 的索引状态、canonical、crawl 时间和 verdict。

- `inspect_urls_batch(property_uri, inspection_urls, stop_on_error=false)`
  对一批 URL 执行 inspection，返回：
  - `property_uri`
  - `results`
  - `errors`
  - `success_count`
  - `error_count`
  - `total_count`
  - `processed_count`
  - `halted`
  - `halt_reason`

批量命令约束：

- 单次最多允许 `50` 个 URL；这是实现内硬常量，不是公开可调参数
- 默认串行执行，不做无限并发
- 必须对单个 URL 的失败单独记录，不把失败静默吞掉
- 必须显式区分参数过大、配额耗尽、单 URL inspection 失败
- `quota exhausted` 视为整批执行环境失效，必须立即停止，不受 `stop_on_error=false` 影响
- `quota exhausted` 触发停止时，也必须返回停止前已收集到的部分结果；此时：
  - `halted=true`
  - `halt_reason=quota_exhausted`
  - `processed_count < total_count`
- `stop_on_error=false` 时，继续处理剩余 URL，并在 `errors` 中逐项返回失败
- `stop_on_error=true` 时，命令在首个失败点停止，但仍返回已经完成的 `results/errors` 与计数；此时：
  - `halted=true`
  - `halt_reason` 写明触发中止的错误类型
  - `processed_count < total_count`
- 参数级错误（如 URL 数量超过 50）直接整批拒绝，不进入部分执行

### 3.6 低频命令处理

以下命令保留在底层骨架中，但不属于 agent 的一线高频命令面：

- `list_sitemaps`
- `get_sitemap`

理由：这两者是技术排障时的低频命令，不值得和站点/页面/query 主路径放在同一优先级。

### 3.7 底层兜底命令

- `query_search_analytics(property_uri, start_date, end_date, dimensions=None, row_limit=1000, start_row=0, dimension_filter_groups=None, search_type="web", data_state=None, aggregation_type=None)`

这是模板命令之外的万能刀。模板命令应当尽量覆盖高频任务，但不追求穷尽。凡是模板没有覆盖到的组合查询，都应该回到这把刀。

### 3.8 快照命令

这批命令不是本轮新增重点，但仍然保留在 agent 命令面内：

- `snapshot_site_day(property_uri, date, search_type="web")`
- `list_snapshots(property_uri=None)`
- `read_snapshot(snapshot_path)`

## 4. 返回结构规范

为了让 agent 可以稳定串联结果，约束如下：

- 站点趋势类结果必须带 `date`
- 页面列表类结果必须带 `page`
- 查询词列表类结果必须带 `query`
- 页面-查询关系类结果必须同时带 `page` 与 `query`
- URL inspection 结果必须带 `inspection_url`
- 批量 inspection 结果必须提供 `success_count`、`error_count`、`total_count`

禁止在命令层返回面向人类阅读的表格字符串。返回结构必须保持 JSON 友好、字段名稳定、可继续被 agent 消费。

## 5. 为什么按这种方式拆

### 5.0 `path_prefix` 语义

`get_pages_by_path_prefix` 的 `path_prefix` 必须按 URL 的 `path` 部分做前缀匹配，而不是对完整 URL 做 `contains`。

在 `sc-domain:*` property 下：

- 匹配应跨协议与跨子域进行
- 仅比较解析后的 URL path，例如 `/blog/`、`/tools/`
- `https://a.example.com/blog/x` 与 `http://example.com/blog/y` 都应匹配 `/blog/`
- `https://example.com/not-blog/?redirect=/blog/` 不应误匹配

这条语义必须写死，否则实现极易退化成脏的字符串包含匹配。

### 5.1 现象层

agent 日常会反复问这些问题：

- 这个站最近整体怎么样？
- 哪些页面在撑流量？
- 某个页面对应哪些 query？
- 某个 query 被哪些页面吃掉？
- 某个 URL 是否被索引？

这些都是任务问题，不是 API mode 问题。

### 5.2 本质层

如果只给 `query_search_analytics`，agent 每次都要自己拼维度、排序、过滤条件，重复劳动太多。  
如果把一切都做成结论型工具，又会把分析偏见硬塞进协议层。

正确做法是：

- 一把底层万能刀兜底
- 一组高频任务模板降摩擦
- 不在协议层内置结论

### 5.3 哲学层

好的命令面不是“越少越高级”，也不是“越多越贴心”。  
好的命令面是：**每个命令都像一句清晰的问题。**

当命令名本身就接近 agent 的自然任务语言，系统复杂度会下降，因为调用层不需要再翻译一遍语义。

## 6. 明确不做

本轮命令面设计明确不包含：

- 多站点聚合查询
- 自动对比上周/上月
- 自动识别掉量页面
- 自动识别低 CTR 页面
- 排名机会评估
- 建议型或结论型输出
- `get_site_summary_by_date_and_country`
- `get_site_summary_by_date_and_device`
- 把 `list_sitemaps` / `get_sitemap` 提升为一线高频命令

这些都属于更高一层的分析逻辑，而不是 MCP 查询协议层。

## 7. 推荐实现顺序

建议实现顺序：

1. `get_site_summary_by_device`
2. `get_site_summary_by_country`
3. `get_top_pages`
4. `get_page_trend`
5. `get_page_queries`
6. `get_pages_by_path_prefix`
7. `get_top_queries`
8. `get_query_trend`
9. `get_query_pages`
10. `get_query_page_pairs`
11. `get_page_query_pairs`
12. `inspect_urls_batch`

先把单维度高频模板补齐，再补关系型命令，最后补 batch inspection。
