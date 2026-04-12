# tests/
> L2 | 父级: /Users/celeste/Documents/GitHub/google-search-console-mcp/CLAUDE.md

成员清单
CLAUDE.md: 测试目录地图，约束配置、认证、工具与快照测试的分层策略
test_bootstrap.py: 启动骨架测试，验证项目最小元数据文件是否已建立
test_config.py: 配置层测试，验证 server 与 paths YAML 能被合并为 Settings
test_auth.py: 认证层测试，约束 OAuth 配置存在但 token 缺失时的状态表达
test_gsc_client.py: GSC 包装层测试，约束模板查询、排序契约、path_prefix 语义与 batch inspection 行为
test_snapshot_csv.py: 快照层测试，约束 property URI 到 CSV 路径的规范化规则
test_audit.py: 审计层测试，验证 JSONL 记录能稳定落盘
test_tools.py: 工具层测试，约束站点、页面、查询词与 inspection 命令名集合不漂移
test_server.py: server 层测试，验证 FastMCP 入口能被正确组装
test_cli.py: CLI 层测试，验证 auth 子命令结构与解析行为
test_review_fixes.py: review 修复测试，覆盖快照读取边界、空数据快照、审计接线与认证状态收紧

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
