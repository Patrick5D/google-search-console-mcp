"""
[INPUT]: 依赖 Search Console URL Inspection API 的 inspect() 能力
[OUTPUT]: 对外提供 inspect_url 与 inspect_urls_batch
[POS]: gsc 的 URL 检查读取器，负责单 URL 与 batch inspection 查询
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from ..errors import ValidationError


def inspect_url(service, *, property_uri: str, inspection_url: str) -> dict[str, object]:
    body = {"inspectionUrl": inspection_url, "siteUrl": property_uri}
    return service.urlInspection().index().inspect(body=body).execute()


def inspect_urls_batch(
    service,
    *,
    property_uri: str,
    inspection_urls: list[str],
    stop_on_error: bool = False,
) -> dict[str, object]:
    if len(inspection_urls) > 50:
        raise ValidationError("inspect_urls_batch supports at most 50 URLs per call")

    results: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    halted = False
    halt_reason = ""

    for inspection_url in inspection_urls:
        try:
            result = inspect_url(service, property_uri=property_uri, inspection_url=inspection_url)
            results.append({"inspection_url": inspection_url, "ok": True, "result": result})
            continue
        except Exception as exc:
            error_name = "quota_exhausted" if _is_quota_exhausted(exc) else type(exc).__name__
            errors.append({"inspection_url": inspection_url, "ok": False, "error": error_name})
            if error_name == "quota_exhausted" or stop_on_error:
                halted = True
                halt_reason = error_name
                break

    return {
        "property_uri": property_uri,
        "results": results,
        "errors": errors,
        "success_count": len(results),
        "error_count": len(errors),
        "total_count": len(inspection_urls),
        "processed_count": len(results) + len(errors),
        "halted": halted,
        "halt_reason": halt_reason,
    }


def _is_quota_exhausted(exc: Exception) -> bool:
    text = f"{type(exc).__name__}:{exc}".lower()
    return "quota" in text
