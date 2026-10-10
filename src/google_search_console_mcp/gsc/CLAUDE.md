# gsc/
> L2 | 父级: /Users/celeste/Documents/GitHub/google-search-console-mcp/src/google_search_console_mcp/CLAUDE.md

成员清单
CLAUDE.md: GSC API 包装层地图，约束各文件只做薄封装不做分析判断
__init__.py: GSC 子包入口，暴露子模块命名边界
client.py: Google Search Console service 创建器，连接 OAuth token 与 discovery client
sites.py: property 列表与访问校验读取器
performance.py: 查询模板层，对有界分页结果排序与筛选，传递取数范围
query.py: Search Analytics 分页边界，保留聚合与新鲜度元信息，标明截断与覆盖限制
inspection.py: URL Inspection 读取器，负责单 URL 与 batch inspection 契约
sitemaps.py: sitemap 列表与详情读取器

validation.py: 输入边界，校验 PT 日期、查询枚举、过滤组合与分页范围
request.py: 只读执行边界，统一错误分类，网络异常、限速与 5xx 最多重试两次

filters.py: 分析筛选契约，统一国家、设备、路径及查询词 RE2 包含排除条件

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
