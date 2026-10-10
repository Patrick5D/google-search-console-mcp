"""
[INPUT]: 依赖 Google HttpError、网络异常、标准库等待与项目错误类型
[OUTPUT]: 提供 execute_read，统一只读 API 错误与有限重试
[POS]: gsc 的请求执行边界；网络异常、429、限速 403 与 5xx 最多重试两次
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
import json
import time

from googleapiclient.errors import HttpError
from httplib2 import HttpLib2Error

from ..errors import AuthError, AuthorizationError, QuotaError, UpstreamApiError, ValidationError

MAX_ATTEMPTS = 3
RATE_REASONS = {"rateLimitExceeded", "userRateLimitExceeded"}
QUOTA_REASONS = {"quotaExceeded", "dailyLimitExceeded", "dailyLimitExceededUnreg"}


def execute_read(request):
    for attempt in range(MAX_ATTEMPTS):
        try:
            return request.execute()
        except HttpError as exc:
            status = int(exc.resp.status)
            try:
                payload = json.loads(exc.content)
                reasons = {item.get("reason") for item in payload.get("error", {}).get("errors", [])}
            except (ValueError, TypeError, AttributeError):
                reasons = set()
            if reasons & QUOTA_REASONS:
                raise QuotaError("Google daily/property quota exhausted; retry after quota reset") from exc
            retryable = status == 429 or 500 <= status <= 599 or bool(reasons & RATE_REASONS)
            if retryable and attempt < MAX_ATTEMPTS - 1:
                delay = 2 ** attempt
                try:
                    delay = min(30, max(delay, float(exc.resp.get("retry-after", 0))))
                except (ValueError, TypeError):
                    pass
                time.sleep(delay)
                continue
            message = f"Google API HTTP {status}: {exc.reason}"
            if status == 401:
                raise AuthError(message) from exc
            if retryable:
                raise UpstreamApiError(message + "; transient retries exhausted") from exc
            if status == 403:
                raise AuthorizationError(message) from exc
            if status == 400:
                raise ValidationError(message) from exc
            raise UpstreamApiError(message) from exc
        except (TimeoutError, ConnectionError, HttpLib2Error) as exc:
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(2 ** attempt)
                continue
            raise UpstreamApiError(f"Google API transport failure: {type(exc).__name__}; retries exhausted") from exc
