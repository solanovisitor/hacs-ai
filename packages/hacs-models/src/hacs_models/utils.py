from __future__ import annotations

from typing import Any


def set_nested_field(obj: Any, path: str, value: Any) -> None:
    parts = path.split(".")
    cur = obj
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        if is_last:
            try:
                setattr(cur, part, value)
            except Exception:
                if isinstance(cur, dict):
                    cur[part] = value
                else:
                    try:
                        if hasattr(cur, "agent_context") and isinstance(
                            value, (str, int, float, bool, dict, list)
                        ):
                            ctx = cur.agent_context or {}
                            ctx[path] = value
                            cur.agent_context = ctx
                        elif hasattr(cur, "note") and isinstance(value, str):
                            notes = list(cur.note or [])
                            notes.append(value)
                            cur.note = notes
                        else:
                            raise
                    except Exception:
                        raise
        else:
            try:
                nxt = getattr(cur, part, None)
            except Exception:
                nxt = None
            if nxt is None:
                nxt = {}
                try:
                    setattr(cur, part, nxt)
                except Exception:
                    if isinstance(cur, dict):
                        cur[part] = nxt
                    else:
                        raise
            cur = nxt
