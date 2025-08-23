from __future__ import annotations

try:
    import markdown as _md
except Exception:  # pragma: no cover
    _md = None


def markdown_to_html(markdown_text: str) -> str:
    """Convert markdown to minimal HTML. Falls back to pre-wrapped text if markdown package missing."""
    if not markdown_text:
        return ""
    if _md is None:
        # Fallback: wrap in <div> with simple newline conversions
        safe = markdown_text.replace("<", "&lt;").replace(">", "&gt;")
        safe = safe.replace("\n\n", "</p><p>").replace("\n", "<br/>")
        return f"<div><p>{safe}</p></div>"
    return _md.markdown(markdown_text)

