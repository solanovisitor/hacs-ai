from __future__ import annotations

from typing import Dict, Any, List


def summarize_diagnostic_report(report: Dict[str, Any]) -> str:
    if report.get("conclusion"):
        return str(report["conclusion"]).strip()
    results = report.get("result", [])
    if results:
        return f"Report contains {len(results)} observation results"
    presented = report.get("presentedForm", [])
    if presented:
        return f"Report contains {len(presented)} attached documents"
    return "No summary available"


def link_report_observations(report: Dict[str, Any]) -> List[str]:
    return [str(r) for r in report.get("result", [])]


def attach_report_media(report: Dict[str, Any], media_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    media = report.get("media") or []
    media.extend(media_entries or [])
    report["media"] = media
    return report


def validate_report_completeness(report: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
    for req in ("status", "code", "subject"):
        if not report.get(req):
            issues.append(f"missing {req}")
    if not report.get("result") and not report.get("presentedForm"):
        issues.append("missing results or presentedForm")
    return {"complete": len(issues) == 0, "issues": issues}


