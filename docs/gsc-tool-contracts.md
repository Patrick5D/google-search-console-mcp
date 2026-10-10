# GSC 工具协议

当前服务注册 30 个工具。
20 个工具读取账号与 Google 数据。
7 个工具计算观测差异与候选。
3 个工具写入、列举与读取本地快照。

## Search Analytics 输出

Search Analytics 工具统一返回 `{"rows": [...], "meta": {...}}`。
旧客户端直接遍历顶层数组时，改为读取 `rows`。
Python 内部查询保留列表行为，并携带 `meta`。
站点列表、URL 检查与 sitemap 输出保持原结构。

日期采用 `America/Los_Angeles`，包含起止日。
CTR 为 0–1 比例，`0.02` 表示 2%。
平均排名按曝光计算，不等于独立排名追踪结果。
Google 未提供排名时，`average_position` 为 `null`。
默认 `data_state=final`。
`all` 与 `hourly_all` 保留 Google 新鲜度元信息。
`hourly_all` 必须与 `hour` 维度一起使用。

`meta` 包含站点、日期、搜索类型、维度与过滤条件。
`response_aggregation_types` 保存实际聚合方式。
`api_metadata` 保存各页的 Google 元信息。
`captured_at_utc` 记录完成取数的时间。

## 分页与排序

通用查询默认读取一页。
`row_limit` 为 1–25,000，`start_row` 为 API 行偏移。
启用 `fetch_all` 后，每页最多读取 25,000 行。
此时 `max_rows` 控制总预算，`row_limit` 不控制页大小。
预算默认为 100,000，上限为 1,000,000。
到达预算后，额外读取一行探测是否截断。

`truncated` 表示存在更多行，或单页满页尚未确认穷尽。
`next_start_row` 是下一次 API 查询的偏移。
`pagination_complete` 表示从零开始且已穷尽该查询返回的行。
它不保证完整关键词覆盖。
Google 会省略匿名查询及其他受 API 限制的数据。

Top 和路径筛选工具先获取最多 100,000 行，再排序和筛选。
它们的 `start_row` 是本地结果偏移。
`selection_offset`、`matched_rows`、`selection_truncated` 描述本地选择。
该偏移与 `next_start_row` 的 API 偏移不同。
排序仅覆盖已获取的行。
输入数据被截断时，不能称其为全站完整排名。
大站可用通用查询收窄范围或提高取数预算。

## 快照

新路径：`gsc/site_daily/{property}/{search_type}/{date}.csv`。
同站同日的不同搜索类型独立保存。
重复写同一身份会覆盖该快照。
旧路径仍可列举与读取，不自动搬迁。
旧文件中的 `search_type` 决定其数据口径。
无返回行时，不保存虚构的零值快照。

## 分析工具

所有分析工具返回 `items/meta`。
`meta.sources` 保留每个输入窗口的查询元信息。
每次查询预算为 100,000 行。
`source_truncated` 表示输入查询被截断。
`output_truncated` 表示候选数量超过输出上限。
候选不足不能证明全站没有问题。

| 工具 | 口径 |
| --- | --- |
| `compare_periods` | 当前窗口与紧邻的等长窗口比较。支持 page、query、site。site 直接查询汇总。仅两期都有行时计算差值。零基线的变化率为 null。 |
| `find_ctr_opportunities` | 按曝光下限与 CTR 上限筛选，按曝光降序输出。不使用行业 CTR 曲线，不预测流量收益。 |
| `find_declining_pages` | 三个连续等长窗口内点击严格下降。要求每期都有行。报告缺少窗口的页面数量，不将缺失填零。 |
| `get_query_overlap` | 同一查询至少两个页面达到曝光阈值。输出页面证据。页面曝光之和不是去重的站点查询曝光。 |

CTR 候选不是已证实的标题问题。
连续下降不证明内容质量下降。
查询重叠不证明有害内耗。
缺少返回行不证明页面被移出索引。

## 请求错误

网络超时、连接失败、429、限速 403 与 5xx 最多请求三次。
默认等待 1 秒、2 秒。
数值型 `Retry-After` 参与等待，上限为 30 秒。
每日配额耗尽、普通权限错误与无效参数不重试。
批量 URL 检查在配额耗尽时保留部分结果并停止。

## 本地验证

运行 `.venv/bin/python -m pytest -q`。
回归覆盖跨页排序、预算截断和快照身份。
协议回归通过 FastMCP 实际调用工具。
Google API 由模拟对象替代，不消费真实配额。
这些检查不代表真实账号认证或线上验收。
已运行的旧进程需要重启才能加载新工具。

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md


## 公共筛选

七个分析工具接收可选 `filters` 对象。
字段统一使用 AND 组合，并传给每个查询窗口。

| 字段 | 语义 |
| --- | --- |
| `country` | ISO alpha-3 国家码，例如 usa。 |
| `device` | MOBILE、DESKTOP、TABLET；输入可用小写。 |
| `page_prefix` | 以 / 开头的字面路径前缀。查询字符串不参与匹配。 |
| `query_include` | Google RE2 包含正则，例如 shoe\|boot。 |
| `query_exclude` | Google RE2 排除正则，可用于排除品牌词。 |

品牌词由调用者给出，不自动猜测品牌。
Discover/Google News 不允许查询词筛选。
非法 RE2 表达式由 Google 返回明确参数错误。

## 多站摘要与图片对照

`get_multi_site_summary` 接收 1–20 个 property。
重复 property 去重，按点击损失从大到小排序。
增长站点跟随其后，缺少对比与错误站点置后。
单站错误保留错误类型，不丢弃其他站结果。
域名与 URL 前缀属性会重叠，结果不提供跨站总和。
每站汇总直接读取 Google 聚合，不累加查询明细。

`compare_search_types` 按 page 或 query 关联 Web/Image。
两侧指标并列返回，缺失侧为 null。
按 Image 曝光降序排列，缺少 Image 行的实体置后。
它不获取图片文件 URL、alt 或图片尺寸。
图片低 CTR 与连续下降复用既有工具的 image 参数。

## 本站 CTR 基准

`benchmark_page_ctr` 仅查询 Web 页面—查询词明细。
排名区间依次为 (0,3]、(3,10]、(10,20]、(20,50]、(50,+∞)。
每个区间以参考点击之和除以参考曝光之和。
评估目标页面时，从各区间剔除该页面全部行。
再按目标页面各区间的曝光权重计算参考 CTR。
同一查询词仍出现在其他页面时，计入参考查询数。

`filters` 同时限定目标与参考页面。
`page` 只选择评估对象，不排除其他参考页面。
实际 CTR 来自已返回查询明细，不等于页面总 CTR。
匿名查询、API 截断及平均排名混合仍影响对照。

每个参考区间默认至少满足：
- 500 次曝光；
- 5 个不同查询词；
- 3 个其他页面。

门槛可配置，属于样本门槛，不代表统计置信度。
任一目标区间样本不足，整体基准及差值为 null。
仍返回各区间样本与 reference_coverage_ratio。
目标页面未返回时，状态为 not_returned。
不使用行业曲线回退，不预测新增点击。

## 2026-10-10 验收记录

本地回归：60 项测试通过，差异空白检查通过。
真实查询窗口：2026-09-28 至 2026-10-04（PT）。
Control Resonant 与 Motiofy 的站点汇总已独立核对。
壁纸页的 Web/Image 数据已按页面分别查询核对。
CTR 抽查使用 645 条页面—查询词明细。
目标页面为 Control Resonant 的 control-resonant-vs-control。
剔除目标后，参考区间的点击、曝光与样本数量均匹配。

本地服务已通过既有 mcp-manager 启动。
HTTP MCP tools/list 返回 30 个有描述的工具。
三个新增工具均通过 HTTP 真实调用。
客户端仍需重新连接才能刷新旧的工具列表。
本次未提交或推送 Git 变更。
