from __future__ import annotations

import html
import re
from typing import Any


_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_MARKDOWN_SPECIALS = re.compile(r"([\\`*_{}\[\]()#+.!|])")


def markdown_plain_text(value: Any, default: str = "UNKNOWN") -> str:
    """Render untrusted metadata as one literal Markdown-safe text fragment.

    External claim/report artifacts are Markdown, but values come from customer or
    operator-controlled evidence. Collapse control/newline characters, neutralize raw
    HTML and escape Markdown punctuation so a value cannot create headings, links,
    table columns, emphasis or other document structure.
    """
    if value is None:
        raw = default
    else:
        raw = str(value)
        if not raw.strip():
            raw = default

    raw = _CONTROL_CHARS.sub(" ", raw)
    raw = " ".join(raw.split())
    raw = html.escape(raw, quote=False)
    return _MARKDOWN_SPECIALS.sub(r"\\\1", raw)
