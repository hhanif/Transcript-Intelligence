from __future__ import annotations

import html
from collections import Counter
from pathlib import Path

from .config import topics as taxonomy_topics


def svg_bar_chart(path: Path, title: str, values: list[tuple[str, float]], x_label: str = "Count") -> None:
    width, height = 900, 520
    left, top, bar_h, gap = 260, 70, 34, 18
    max_value = max((value for _, value in values), default=1)
    rows = []
    for i, (label, value) in enumerate(values):
        y = top + i * (bar_h + gap)
        bar_w = 560 * value / max_value if max_value else 0
        rows.append(f'<text x="24" y="{y + 23}" class="label">{html.escape(label)}</text>')
        rows.append(f'<rect x="{left}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="4" fill="#2f6f73"/>')
        rows.append(f'<text x="{left + bar_w + 10}" y="{y + 23}" class="value">{value:g}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>.title{{font:700 26px Arial;fill:#172426}}.label{{font:14px Arial;fill:#27383a}}.value{{font:700 14px Arial;fill:#172426}}.axis{{font:12px Arial;fill:#5e7073}}</style>
<rect width="100%" height="100%" fill="#f7f4ef"/>
<text x="24" y="38" class="title">{html.escape(title)}</text>
<text x="{left}" y="{height - 28}" class="axis">{html.escape(x_label)}</text>
{''.join(rows)}
</svg>'''
    path.write_text(svg, encoding="utf-8")


def svg_sentiment(path: Path, rows: list[dict[str, object]]) -> None:
    values = [(str(row["call_type"]).title(), float(row["avg_sentiment"])) for row in rows]
    width, height = 900, 420
    mid = 470
    rows_svg = []
    for i, (label, value) in enumerate(values):
        y = 95 + i * 80
        bar_w = abs(value) * 330
        x = mid if value >= 0 else mid - bar_w
        fill = "#3a7d44" if value >= 0 else "#ad3f32"
        rows_svg.append(f'<text x="60" y="{y + 24}" class="label">{html.escape(label)}</text>')
        rows_svg.append(f'<rect x="{x:.1f}" y="{y}" width="{bar_w:.1f}" height="34" rx="4" fill="{fill}"/>')
        rows_svg.append(f'<text x="{mid + 350}" y="{y + 24}" class="value">{value:.2f}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>.title{{font:700 26px Arial;fill:#172426}}.label{{font:15px Arial;fill:#27383a}}.value{{font:700 15px Arial;fill:#172426}}.axis{{font:12px Arial;fill:#5e7073}}</style>
<rect width="100%" height="100%" fill="#f7f4ef"/>
<text x="24" y="38" class="title">Average sentiment by call type</text>
<line x1="{mid}" x2="{mid}" y1="72" y2="340" stroke="#87979a" stroke-width="2"/>
<text x="{mid - 330}" y="365" class="axis">Negative</text><text x="{mid + 285}" y="365" class="axis">Positive</text>
{''.join(rows_svg)}
</svg>'''
    path.write_text(svg, encoding="utf-8")


def svg_heatmap(path: Path, rows: list[dict[str, str]]) -> None:
    topics = list(taxonomy_topics().keys())
    call_types = sorted(set(row["call_type"] for row in rows))
    counts = Counter((row["topic"], row["call_type"]) for row in rows)
    max_count = max(counts.values(), default=1)
    cell_w, cell_h = 150, 42
    width, height = 1120, 520
    cells = []
    for i, topic in enumerate(topics):
        y = 80 + i * cell_h
        cells.append(f'<text x="24" y="{y + 26}" class="label">{html.escape(topic)}</text>')
        for j, call_type in enumerate(call_types):
            x = 430 + j * cell_w
            count = counts[(topic, call_type)]
            opacity = 0.12 + 0.88 * (count / max_count if max_count else 0)
            cells.append(f'<rect x="{x}" y="{y}" width="{cell_w - 8}" height="{cell_h - 7}" rx="4" fill="#2f6f73" opacity="{opacity:.2f}"/>')
            cells.append(f'<text x="{x + 62}" y="{y + 24}" class="value">{count}</text>')
    headers = "".join(f'<text x="{430 + j * cell_w + 34}" y="64" class="header">{html.escape(ct.title())}</text>' for j, ct in enumerate(call_types))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>.title{{font:700 26px Arial;fill:#172426}}.label{{font:14px Arial;fill:#27383a}}.header{{font:700 14px Arial;fill:#172426}}.value{{font:700 13px Arial;fill:#172426;text-anchor:middle}}</style>
<rect width="100%" height="100%" fill="#f7f4ef"/>
<text x="24" y="38" class="title">Topic mix by call type</text>
{headers}{''.join(cells)}
</svg>'''
    path.write_text(svg, encoding="utf-8")

