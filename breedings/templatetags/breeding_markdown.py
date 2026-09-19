import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe


register = template.Library()

_STRONG_RE = re.compile(r"\\*\\*([^*\\n]+)\\*\\*")
_EMPHASIS_RE = re.compile(r"(?<!\\*)\\*([^*\\n]+)\\*(?!\\*)")


def _render_inline(value):
    escaped = escape(value)
    escaped = _STRONG_RE.sub(r"<strong>\\1</strong>", escaped)
    escaped = _EMPHASIS_RE.sub(r"<em>\\1</em>", escaped)
    return escaped


def render_limited_markdown(value):
    if not value:
        return ""

    output = []
    paragraph_lines = []
    list_items = []

    def flush_paragraph():
        if paragraph_lines:
            output.append("<p>" + "<br>".join(paragraph_lines) + "</p>")
            paragraph_lines.clear()

    def flush_list():
        if list_items:
            output.append(
                '<ul class="mb-3">'
                + "".join(f"<li>{item}</li>" for item in list_items)
                + "</ul>"
            )
            list_items.clear()

    for raw_line in str(value).splitlines():
        if not raw_line.strip():
            flush_paragraph()
            flush_list()
            continue

        if raw_line.startswith("# ") and raw_line[2:].strip():
            flush_paragraph()
            flush_list()
            output.append(
                '<h3 class="h5 mt-3 mb-2">'
                + _render_inline(raw_line[2:].strip())
                + "</h3>"
            )
            continue

        if raw_line.startswith("- ") and raw_line[2:].strip():
            flush_paragraph()
            list_items.append(_render_inline(raw_line[2:].strip()))
            continue

        flush_list()
        paragraph_lines.append(_render_inline(raw_line))

    flush_paragraph()
    flush_list()
    return mark_safe("\\n".join(output))


@register.filter(name="limited_markdown")
def limited_markdown(value):
    return render_limited_markdown(value)
