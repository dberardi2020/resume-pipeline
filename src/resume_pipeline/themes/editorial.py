"""`editorial` — classic serif, centred masthead, quiet rules.

A deliberately different register from `slate`: no colour blocks, no accent, nothing
that reads as "designed in a browser". Impact comes from typography — a serif face,
generous leading, small-caps section rules — which tends to age better and reads as
more senior in conservative industries.

Single-column and 10pt+, so it is submittable anywhere.
"""
from __future__ import annotations

from . import Theme, esc
from ..model import date_range

CSS = """
@page { size: Letter; margin: 0.62in 0.7in; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: Charter, "Bitstream Charter", Georgia, "Times New Roman", serif;
  font-size: 10.5pt; line-height: 1.5; color: #1a1a1a; background: #fff;
}
.masthead { text-align: center; padding-bottom: 11px; border-bottom: 2px solid #1a1a1a; }
h1 { font-size: 23pt; font-weight: 600; letter-spacing: 1.4px; text-transform: uppercase; }
.label { margin-top: 5px; font-size: 10.5pt; font-style: italic; color: #444; }
.contact { margin-top: 7px; font-size: 9.8pt; color: #333; }
.contact a { color: #333; text-decoration: none; }
.contact .bit { white-space: nowrap; }
h2 {
  font-size: 10pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1.6px;
  margin: 16px 0 7px; padding-bottom: 3px; border-bottom: 1px solid #bbb; color: #1a1a1a;
}
.summary { margin-top: 13px; text-align: justify; }
.skill-line { margin-bottom: 3px; }
.entry { margin-bottom: 10px; break-inside: avoid-page; }
.entry-head { font-weight: 700; }
.entry-meta { font-size: 10pt; font-style: italic; color: #444; }
.entry-note { font-size: 10pt; font-style: italic; color: #444; }
ul { margin: 4px 0 0 18px; }
li { margin-bottom: 3px; }
a { color: #1a1a1a; }
"""


def _contact(resume) -> str:
    bits = [esc(resume.basics.get("phone")), esc(resume.location)]
    if email := resume.basics.get("email"):
        bits.append(f'<a href="mailto:{esc(email)}">{esc(email)}</a>')
    for profile in resume.profiles:
        if url := profile.get("url"):
            shown = url.replace("https://", "").replace("http://", "").replace("www.", "")
            bits.append(f'<a href="{esc(url)}">{esc(shown)}</a>')
    wrapped = [f'<span class="bit">{b}</span>' for b in bits if b]
    return f'<div class="contact">{" &middot; ".join(wrapped)}</div>'


def _bullets(entry) -> str:
    highlights = entry.get("highlights") or []
    if not highlights:
        return ""
    return "<ul>" + "".join(f"<li>{esc(h)}</li>" for h in highlights) + "</ul>"


def render(resume) -> str:
    parts = []
    if resume.summary:
        parts.append(f'<div class="summary">{esc(resume.summary)}</div>')

    if resume.skills:
        lines = [f'<div class="skill-line"><b>{esc(g.get("name",""))}:</b> '
                 f'{esc(", ".join(g.get("keywords") or []))}</div>'
                 for g in resume.skills if g.get("keywords")]
        if lines:
            parts.append("<h2>Skills</h2>" + "".join(lines))

    if resume.work:
        rows = []
        for entry in resume.work:
            head = " - ".join(x for x in (esc(entry.get("position", "")),
                                          esc(entry.get("name", ""))) if x)
            meta = " | ".join(x for x in (esc(entry.get("location")),
                                          date_range(entry.get("startDate"),
                                                     entry.get("endDate"))) if x)
            note = (f'<div class="entry-note">{esc(entry["note"])}</div>'
                    if entry.get("note") else "")
            rows.append(f'<div class="entry"><div class="entry-head">{head}</div>'
                        f'<div class="entry-meta">{meta}</div>{note}{_bullets(entry)}</div>')
        parts.append("<h2>Experience</h2>" + "".join(rows))

    if resume.projects:
        rows = []
        for entry in resume.projects:
            rows.append(f'<div class="entry"><div class="entry-head">{esc(entry.get("name",""))}</div>'
                        f'<div class="entry-meta">{esc(entry.get("description",""))}</div>'
                        f"{_bullets(entry)}</div>")
        parts.append("<h2>Projects</h2>" + "".join(rows))

    if resume.education:
        rows = []
        for entry in resume.education:
            study = " ".join(esc(v) for v in (entry.get("studyType"), entry.get("area")) if v)
            meta = [study, esc(entry.get("location"))]
            if end := entry.get("endDate"):
                meta.append(f"Graduated {date_range(end, end).split(' - ')[0]}")
            if score := entry.get("score"):
                meta.append(f"GPA {esc(score)}")
            rows.append(f'<div class="entry"><div class="entry-head">'
                        f'{esc(entry.get("institution",""))}</div>'
                        f'<div class="entry-meta">{", ".join(m for m in meta if m)}</div></div>')
        parts.append("<h2>Education</h2>" + "".join(rows))

    label = f'<div class="label">{esc(resume.label)}</div>' if resume.label else ""
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        f"<title>{esc(resume.name)} - Resume</title><style>{CSS}</style></head><body>"
        f'<div class="masthead"><h1>{esc(resume.name)}</h1>{label}{_contact(resume)}</div>'
        f'{"".join(parts)}'
        "</body></html>\n"
    )


THEME = Theme(
    name="editorial",
    description="Classic serif masthead, quiet rules - single-column.",
    render=render,
    columns=1,
    min_font_pt=10.0,
    remote_assets=False,
    ats_safe=True,
)
