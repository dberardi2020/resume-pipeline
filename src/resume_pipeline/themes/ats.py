"""`ats` — single-column, parser-first. The theme you submit through a portal.

Every choice here is subordinate to one question: will a parser read this
correctly? So: one column, real headings in document order, 10pt floor, no
tables, no chips, no icons, no background art, and locally-resolved system fonts
so nothing depends on a network fetch at render time.

It is not ugly, but it is not trying to be striking. `designed` is for that.
"""
from __future__ import annotations

from . import Theme, esc
from ..model import date_range

# No @import / no webfont. A font stack that resolves on macOS, Windows, and
# Linux, in a serif-free family that parsers and humans both handle well.
CSS = """
@page { size: Letter; margin: 0.6in 0.7in; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: Calibri, Carlito, "Helvetica Neue", Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.42;
  color: #111;
  background: #fff;
}
.resume { max-width: 7.1in; margin: 0 auto; }
h1 { font-size: 20pt; font-weight: 700; letter-spacing: -0.2px; }
.label { font-size: 11pt; font-weight: 600; color: #333; margin-top: 2px; }
.contact { font-size: 10pt; color: #222; margin-top: 6px; }
.contact a { color: #111; text-decoration: none; }
h2 {
  font-size: 11pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin: 16px 0 6px;
  padding-bottom: 3px;
  border-bottom: 1px solid #999;
}
.summary { margin-top: 10px; }
.entry { margin-bottom: 11px; }
/* Keep a role and its first bullets together across a page break. */
.entry { break-inside: avoid-page; }
.entry-head { font-size: 10.5pt; font-weight: 700; }
.entry-meta { font-size: 10pt; color: #333; }
.entry-note { font-size: 10pt; font-style: italic; color: #333; }
ul { margin: 4px 0 0 18px; }
li { margin-bottom: 3px; }
.skill-line { margin-bottom: 3px; }
.skill-line strong { font-weight: 700; }
"""


def _contact(resume) -> str:
    bits = []
    if phone := resume.basics.get("phone"):
        bits.append(esc(phone))
    if location := resume.location:
        bits.append(esc(location))
    line1 = " | ".join(bits)

    links = []
    if email := resume.basics.get("email"):
        links.append(f'<a href="mailto:{esc(email)}">{esc(email)}</a>')
    for profile in resume.profiles:
        url = profile.get("url")
        if url:
            # Show the bare URL: a parser reads the text, not the href.
            shown = url.replace("https://", "").replace("http://", "")
            links.append(f'<a href="{esc(url)}">{esc(shown)}</a>')
    line2 = " | ".join(links)

    out = ""
    if line1:
        out += f'<div class="contact">{line1}</div>'
    if line2:
        out += f'<div class="contact">{line2}</div>'
    return out


def _bullets(entry) -> str:
    highlights = entry.get("highlights") or []
    if not highlights:
        return ""
    items = "".join(f"<li>{esc(h)}</li>" for h in highlights)
    return f"<ul>{items}</ul>"


def _work(resume) -> str:
    if not resume.work:
        return ""
    out = ["<h2>Experience</h2>"]
    for entry in resume.work:
        position = esc(entry.get("position", ""))
        name = esc(entry.get("name", ""))
        head = " - ".join(p for p in (position, name) if p)
        meta_bits = [entry.get("location"), date_range(entry.get("startDate"),
                                                       entry.get("endDate"))]
        meta = " | ".join(esc(m) for m in meta_bits if m)
        note = entry.get("note")
        out.append('<div class="entry">')
        out.append(f'<div class="entry-head">{head}</div>')
        out.append(f'<div class="entry-meta">{meta}</div>')
        if note:
            out.append(f'<div class="entry-note">{esc(note)}</div>')
        out.append(_bullets(entry))
        out.append("</div>")
    return "".join(out)


def _skills(resume) -> str:
    if not resume.skills:
        return ""
    out = ["<h2>Skills</h2>"]
    for group in resume.skills:
        keywords = group.get("keywords") or []
        if not keywords:
            continue
        # Comma-separated inline text, not chips: a parser reads this as a list.
        out.append(
            f'<div class="skill-line"><strong>{esc(group.get("name", ""))}:</strong> '
            f'{esc(", ".join(keywords))}</div>'
        )
    return "".join(out)


def _projects(resume) -> str:
    if not resume.projects:
        return ""
    out = ["<h2>Projects</h2>"]
    for entry in resume.projects:
        head = esc(entry.get("name", ""))
        if url := entry.get("url"):
            shown = url.replace("https://", "")
            head += f' - <a href="{esc(url)}">{esc(shown)}</a>'
        out.append('<div class="entry">')
        out.append(f'<div class="entry-head">{head}</div>')
        if description := entry.get("description"):
            out.append(f'<div class="entry-meta">{esc(description)}</div>')
        out.append(_bullets(entry))
        out.append("</div>")
    return "".join(out)


def _education(resume) -> str:
    if not resume.education:
        return ""
    out = ["<h2>Education</h2>"]
    for entry in resume.education:
        institution = esc(entry.get("institution", ""))
        study = " ".join(esc(v) for v in (entry.get("studyType"),
                                          entry.get("area")) if v)
        meta_bits = [study, entry.get("location")]
        if end := entry.get("endDate"):
            meta_bits.append(f"Graduated {date_range(end, end).split(' - ')[0]}")
        if score := entry.get("score"):
            meta_bits.append(f"GPA {score}")
        meta = ", ".join(esc(m) for m in meta_bits if m)
        out.append('<div class="entry">')
        out.append(f'<div class="entry-head">{institution}</div>')
        out.append(f'<div class="entry-meta">{meta}</div>')
        out.append("</div>")
    return "".join(out)


def render(resume) -> str:
    summary = (f'<div class="summary">{esc(resume.summary)}</div>'
               if resume.summary else "")
    label = f'<div class="label">{esc(resume.label)}</div>' if resume.label else ""
    body = "".join((
        f"<h1>{esc(resume.name)}</h1>",
        label,
        _contact(resume),
        summary,
        _skills(resume),
        _work(resume),
        _projects(resume),
        _education(resume),
    ))
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        f"<title>{esc(resume.name)} - Resume</title>"
        f"<style>{CSS}</style></head><body>"
        f'<div class="resume">{body}</div>'
        "</body></html>\n"
    )


THEME = Theme(
    name="ats",
    description="Single-column, parser-first. Submit this one through portals.",
    render=render,
    columns=1,
    min_font_pt=10.0,
    remote_assets=False,
    ats_safe=True,
)
