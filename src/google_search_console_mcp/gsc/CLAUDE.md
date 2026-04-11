# gsc/
> L2 | 父级: /Users/celeste/Documents/GitHub/google-search-console-mcp/src/CLAUDE.md

成员清单
CLAUDE.md: GSC API 包装层地图，约束各文件只做薄封装不做分析判断
__init__.py: GSC 子包入口，暴露子模块命名边界
client.py: Google Search Console service 创建器，连接 OAuth token 与 discovery client
sites.py: property 列表与访问校验读取器
performance.py: Search Analytics 查询与原始行归一化逻辑
inspection.py: URL Inspection 读取器
sitemaps.py: sitemap 列表与详情读取器

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
