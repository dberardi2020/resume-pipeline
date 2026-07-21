"""`slate` — the styled look, single-column. The bridge theme.

`designed` gets its impact from a sidebar, which is exactly the thing that breaks
parsers. This theme keeps the visual language — dark full-bleed header band, an
accent colour, confident type hierarchy — and drops the two-column grid.

The result reads as designed rather than plain, while staying a single top-to-bottom
column that extracts in the right order. If a theme is going to be the default, it
should be this one.
"""
from __future__ import annotations

from . import Theme, esc
from ..model import date_range

ACCENT = "#0b6fa4"
INK = "#0f172a"

CSS = f"""
@page {{ size: Letter; margin: 0; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif;
  font-size: 10.5pt; line-height: 1.45; color: #1e2430; background: #fff;
}}
.header {{
  background: {INK}; color: #fff; padding: 0.44in 0.62in 0.36in;
}}
h1 {{ font-size: 25pt; font-weight: 700; letter-spacing: -0.4px; line-height: 1.08; color: #fff; }}
.label {{ margin-top: 5px; font-size: 11pt; font-weight: 600; color: #8ed6fb; letter-spacing: 0.2px; }}
.contact {{ margin-top: 9px; font-size: 10pt; color: #cbd5e1; }}
.contact a {{ color: #cbd5e1; text-decoration: none; }}
.contact .sep {{ color: #64748b; padding: 0 5px; }}
/* Never let a line break land inside "a city, ST" or an email address. */
.contact .bit {{ white-space: nowrap; }}
.body {{ padding: 0.3in 0.62in 0.45in; }}
h2 {{
  font-size: 10.5pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1.1px;
  color: {ACCENT}; margin: 15px 0 7px; padding-bottom: 4px;
  border-bottom: 2px solid #e3eef6;
}}
.summary {{ margin-top: 12px; font-size: 10.5pt; color: #2a3140; }}
.skill-row {{ display: flex; align-items: baseline; gap: 8px; margin-bottom: 6px; }}
.skill-label {{
  flex: 0 0 8.6em; font-size: 9.6pt; font-weight: 700; color: {INK};
  text-align: right; padding-top: 1px;
}}
.pills {{ display: flex; flex-wrap: wrap; gap: 4px; }}
.pill {{
  background: #eaf4fa; color: #0a5b87; border: 0.5pt solid #cfe6f3;
  border-radius: 3pt; padding: 1.2pt 5.5pt; font-size: 9.6pt; font-weight: 600;
}}
/* Verified 2026-07-21 with PyMuPDF: Chrome emits each pill as its own text run,
   so extraction yields one skill per line. No delimiter hack needed. (An earlier
   zero-size separator span was dropped from the PDF entirely and did nothing.) */
.entry {{ margin-bottom: 11px; break-inside: avoid-page; }}
.entry-head {{ font-size: 11pt; font-weight: 700; color: {INK}; }}
.entry-meta {{ font-size: 10pt; color: #5b6577; margin-top: 1px; }}
.entry-note {{ font-size: 10pt; font-style: italic; color: #5b6577; }}
ul {{ margin: 5px 0 0 17px; }}
li {{ margin-bottom: 3.5px; padding-left: 2px; }}
li::marker {{ color: {ACCENT}; }}
a {{ color: {ACCENT}; text-decoration: none; }}
"""


def _contact(resume) -> str:
    bits = [esc(resume.basics.get("phone")), esc(resume.location)]
    if email := resume.basics.get("email"):
        bits.append(f'<a href="mailto:{esc(email)}">{esc(email)}</a>')
    for profile in resume.profiles:
        if url := profile.get("url"):
            shown = url.replace("https://", "").replace("http://", "").replace("www.", "")
            bits.append(f'<a href="{esc(url)}">{esc(shown)}</a>')
    # Literal spaces around the separator are load-bearing: each `.bit` is nowrap,
    # so without whitespace between them the line has no break opportunity at all
    # and overflows the page instead of wrapping.
    sep = ' <span class="sep">·</span> '
    wrapped = [f'<span class="bit">{b}</span>' for b in bits if b]
    return f'<div class="contact">{sep.join(wrapped)}</div>'


def _bullets(entry) -> str:
    highlights = entry.get("highlights") or []
    if not highlights:
        return ""
    return "<ul>" + "".join(f"<li>{esc(h)}</li>" for h in highlights) + "</ul>"


def _entries(items, head_fn, meta_fn) -> str:
    out = []
    for entry in items:
        note = (f'<div class="entry-note">{esc(entry["note"])}</div>'
                if entry.get("note") else "")
        out.append(
            f'<div class="entry"><div class="entry-head">{head_fn(entry)}</div>'
            f'<div class="entry-meta">{meta_fn(entry)}</div>{note}{_bullets(entry)}</div>'
        )
    return "".join(out)


def render(resume) -> str:
    parts = []

    if resume.summary:
        parts.append(f'<div class="summary">{esc(resume.summary)}</div>')

    if resume.skills:
        rows = []
        for group in resume.skills:
            keywords = group.get("keywords") or []
            if not keywords:
                continue
            pills = "".join(
                f'<span class="pill">{esc(k)}</span>'
                for k in keywords
            )
            rows.append(f'<div class="skill-row">'
                        f'<div class="skill-label">{esc(group.get("name",""))}</div>'
                        f'<div class="pills">{pills}</div></div>')
        if rows:
            parts.append("<h2>Skills</h2>" + "".join(rows))

    if resume.work:
        parts.append("<h2>Experience</h2>" + _entries(
            resume.work,
            lambda e: " - ".join(x for x in (esc(e.get("position", "")), esc(e.get("name", ""))) if x),
            lambda e: " | ".join(x for x in (esc(e.get("location")),
                                             date_range(e.get("startDate"), e.get("endDate"))) if x),
        ))

    if resume.projects:
        parts.append("<h2>Projects</h2>" + _entries(
            resume.projects,
            lambda e: esc(e.get("name", "")),
            lambda e: esc(e.get("description", "")),
        ))

    if resume.education:
        rows = []
        for entry in resume.education:
            study = " ".join(esc(v) for v in (entry.get("studyType"), entry.get("area")) if v)
            meta = [study, esc(entry.get("location"))]
            if end := entry.get("endDate"):
                meta.append(f"Graduated {date_range(end, end).split(' - ')[0]}")
            if score := entry.get("score"):
                meta.append(f"GPA {esc(score)}")
            rows.append(
                f'<div class="entry"><div class="entry-head">{esc(entry.get("institution",""))}</div>'
                f'<div class="entry-meta">{", ".join(m for m in meta if m)}</div></div>'
            )
        parts.append("<h2>Education</h2>" + "".join(rows))

    label = f'<div class="label">{esc(resume.label)}</div>' if resume.label else ""
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        f"<title>{esc(resume.name)} - Resume</title><style>{CSS}</style></head><body>"
        f'<div class="header"><h1>{esc(resume.name)}</h1>{label}{_contact(resume)}</div>'
        f'<div class="body">{"".join(parts)}</div>'
        "</body></html>\n"
    )


THEME = Theme(
    name="slate",
    description="Styled dark header, accent rules - single-column. Best default.",
    render=render,
    columns=1,
    min_font_pt=10.0,
    remote_assets=False,
    ats_safe=True,
)
