"""
[INPUT]: 依赖内建 Exception 体系定义项目错误边界
[OUTPUT]: 对外提供 ConfigError、AuthError、AuthorizationError、ValidationError、UpstreamApiError、QuotaError、SnapshotError
[POS]: google_search_console_mcp 的异常分层，被配置、认证、客户端与快照模块共享
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""


class ConfigError(Exception):
    """配置文件缺失、格式错误或路径不可用。"""


class AuthError(Exception):
    """OAuth 凭据缺失、失效或刷新失败。"""


class AuthorizationError(Exception):
    """当前账号无权访问目标 property。"""


class ValidationError(Exception):
    """输入参数不合法。"""


class UpstreamApiError(Exception):
    """Google 上游 API 调用失败。"""


class SnapshotError(Exception):
    """本地快照写入或读取失败。"""


class QuotaError(UpstreamApiError):
    """Google 每日或站点配额耗尽。"""
