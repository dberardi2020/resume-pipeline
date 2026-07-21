"""`designed` — the styled two-column look, for direct sends and the web.

This preserves the sidebar aesthetic of the original hand-written `resume.html`,
with two faults repaired: type no longer drops below 10pt, and the webfont
`@import` is gone in favour of a locally-resolved stack, so the layout cannot
silently reflow when a render-time network fetch fails.

The two-column layout itself is *not* repaired, because it is the whole point of
the design. So the theme declares `columns = 2` and `ats_safe = False`, and the
linter will flag it every time. That is intended: use this for a human reader who
opens the PDF — a recruiter you email, a hiring manager, your own site — and use
`ats` for anything that goes through a portal.
"""
from __future__ import annotations

from . import Theme, esc
from ..model import date_range

CSS = """
@page { size: Letter; margin: 0; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.45;
  color: #1a1a2e;
  background: #fff;
}
.page { width: 8.5in; min-height: 11in; margin: 0 auto;
        display: grid; grid-template-columns: 2.5in 1fr; grid-template-rows: auto 1fr; }
.header { grid-column: 1 / -1; background: #0f172a; color: #fff;
          padding: 0.42in 0.45in 0.34in; display: flex; align-items: flex-end; gap: 0.3in; }
.header-name { flex: 1; }
h1 { font-size: 24pt; font-weight: 700; letter-spacing: -0.4px; line-height: 1.1; color: #fff; }
.title-bar { margin-top: 5px; font-size: 10pt; color: #b6c2d4; }
.contact-strip { display: flex; flex-direction: column; align-items: flex-end;
                 gap: 2px; font-size: 10pt; color: #d3dbe6; text-align: right; }
.contact-strip a { color: #8ed6fb; text-decoration: none; }
.sidebar { background: #f6f8fb; border-right: 1px solid #e2e8f0;
           padding: 0.3in 0.25in 0.3in 0.34in; display: flex; flex-direction: column; gap: 0.2in; }
.main { padding: 0.3in 0.4in 0.3in 0.28in; display: flex; flex-direction: column; gap: 0.16in; }
.section-title { font-size: 10pt; font-weight: 700; letter-spacing: 0.8px;
                 text-transform: uppercase; color: #0b6fa4; margin-bottom: 7px;
                 padding-bottom: 3px; border-bottom: 1.5px solid #dceefb; }
.skill-group { margin-bottom: 8px; }
.skill-label { font-size: 10pt; font-weight: 600; color: #3d4a5c; margin-bottom: 2px; }
.skill-body { font-size: 10pt; color: #1a1a2e; }
.entry { margin-bottom: 10px; break-inside: avoid-page; }
.entry-head { font-size: 10.5pt; font-weight: 700; }
.entry-meta { font-size: 10pt; color: #46536b; }
.entry-note { font-size: 10pt; font-style: italic; color: #46536b; }
.summary { font-size: 10pt; }
ul { margin: 4px 0 0 16px; }
li { margin-bottom: 3px; }
.edu-school { font-weight: 600; font-size: 10pt; }
.edu-meta { font-size: 10pt; color: #46536b; margin-top: 1px; }
"""


def _header(resume) -> str:
    links = []
    if email := resume.basics.get("email"):
        links.append(f'<a href="mailto:{esc(email)}">{esc(email)}</a>')
    for profile in resume.profiles:
        if url := profile.get("url"):
            shown = url.replace("https://", "").replace("http://", "")
            links.append(f'<a href="{esc(url)}">{esc(shown)}</a>')
    meta = [resume.basics.get("phone"), resume.location]
    strip = "".join(f"<div>{esc(m)}</div>" for m in meta if m)
    strip += "".join(f"<div>{link}</div>" for link in links)
    label = f'<div class="title-bar">{esc(resume.label)}</div>' if resume.label else ""
    return (
        '<header class="header"><div class="header-name">'
        f"<h1>{esc(resume.name)}</h1>{label}</div>"
        f'<div class="contact-strip">{strip}</div></header>'
    )


def _sidebar(resume) -> str:
    out = []
    if resume.skills:
        groups = []
        for group in resume.skills:
            keywords = group.get("keywords") or []
            if not keywords:
                continue
            groups.append(
                f'<div class="skill-group">'
                f'<div class="skill-label">{esc(group.get("name", ""))}</div>'
                f'<div class="skill-body">{esc(", ".join(keywords))}</div></div>'
            )
        if groups:
            out.append('<section><div class="section-title">Skills</div>'
                       + "".join(groups) + "</section>")

    if resume.education:
        entries = []
        for entry in resume.education:
            study = " ".join(esc(v) for v in (entry.get("studyType"),
                                              entry.get("area")) if v)
            meta = [study, entry.get("location")]
            if end := entry.get("endDate"):
                meta.append(f"Graduated {date_range(end, end).split(' - ')[0]}")
            if score := entry.get("score"):
                meta.append(f"GPA {score}")
            entries.append(
                f'<div class="entry"><div class="edu-school">'
                f'{esc(entry.get("institution", ""))}</div>'
                f'<div class="edu-meta">{", ".join(esc(m) for m in meta if m)}</div></div>'
            )
        out.append('<section><div class="section-title">Education</div>'
                   + "".join(entries) + "</section>")
    return f'<aside class="sidebar">{"".join(out)}</aside>'


def _bullets(entry) -> str:
    highlights = entry.get("highlights") or []
    if not highlights:
        return ""
    return "<ul>" + "".join(f"<li>{esc(h)}</li>" for h in highlights) + "</ul>"


def _main(resume) -> str:
    out = []
    if resume.summary:
        out.append('<section><div class="section-title">Summary</div>'
                   f'<div class="summary">{esc(resume.summary)}</div></section>')

    if resume.work:
        entries = []
        for entry in resume.work:
            head = " - ".join(p for p in (esc(entry.get("position", "")),
                                          esc(entry.get("name", ""))) if p)
            meta = " | ".join(esc(m) for m in (
                entry.get("location"),
                date_range(entry.get("startDate"), entry.get("endDate")),
            ) if m)
            note = (f'<div class="entry-note">{esc(entry["note"])}</div>'
                    if entry.get("note") else "")
            entries.append(
                f'<div class="entry"><div class="entry-head">{head}</div>'
                f'<div class="entry-meta">{meta}</div>{note}{_bullets(entry)}</div>'
            )
        out.append('<section><div class="section-title">Experience</div>'
                   + "".join(entries) + "</section>")

    if resume.projects:
        entries = []
        for entry in resume.projects:
            head = esc(entry.get("name", ""))
            if url := entry.get("url"):
                head += (f' - <a href="{esc(url)}">'
                         f'{esc(url.replace("https://", ""))}</a>')
            description = (f'<div class="entry-meta">{esc(entry["description"])}</div>'
                           if entry.get("description") else "")
            entries.append(f'<div class="entry"><div class="entry-head">{head}</div>'
                           f"{description}{_bullets(entry)}</div>")
        out.append('<section><div class="section-title">Projects</div>'
                   + "".join(entries) + "</section>")
    return f'<main class="main">{"".join(out)}</main>'


def render(resume) -> str:
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        f"<title>{esc(resume.name)} - Resume</title>"
        f"<style>{CSS}</style></head><body>"
        f'<div class="page">{_header(resume)}{_sidebar(resume)}{_main(resume)}</div>'
        "</body></html>\n"
    )


THEME = Theme(
    name="designed",
    description="Two-column styled layout. For humans, not portals.",
    render=render,
    columns=2,
    min_font_pt=10.0,
    remote_assets=False,
    ats_safe=False,
)
