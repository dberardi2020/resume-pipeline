"""Copy/paste blocks for LinkedIn and job-application forms.

LinkedIn does not expose profile editing to third-party apps — headline, about,
experience and skills are all read-only over the official API — so keeping a
profile in sync with a resume is, unavoidably, manual. The same is true of most
application portals: they want text pasted into boxes, one field at a time.

Since the copying cannot be automated, the useful thing is to make it accurate.
Each destination field has a character limit, and text that silently overruns gets
truncated on paste — usually mid-sentence, usually unnoticed. So every block is
emitted pre-formatted for its field, with its length measured against the limit
before it leaves the page.

Limits were cross-checked against several third-party references in July 2026;
LinkedIn does not publish them. They are declared here so they are easy to correct.
"""
from __future__ import annotations

import html
from dataclasses import dataclass

from .model import date_range

# (field, limit, note). `None` means no meaningful limit.
LINKEDIN_LIMITS = {
    "headline": 220,
    "about": 2600,
    "experience": 2000,
    "skill": 80,
}

# The About section collapses behind "See more" well before its limit, so the
# first sentences carry disproportionate weight.
ABOUT_FOLD = 300


@dataclass
class Block:
    label: str
    text: str
    limit: int | None = None
    note: str = ""

    @property
    def length(self) -> int:
        return len(self.text)

    @property
    def over(self) -> bool:
        return self.limit is not None and self.length > self.limit


def build(resume) -> list[Block]:
    out: list[Block] = []

    if resume.label:
        out.append(Block("LinkedIn headline", resume.label,
                         LINKEDIN_LIMITS["headline"]))

    if resume.summary:
        fold = " — " + (f"first {ABOUT_FOLD} characters show before “See more”; "
                        f"front-load the specifics")
        out.append(Block("LinkedIn About", resume.summary,
                         LINKEDIN_LIMITS["about"], note=fold.strip(" —")))

    for entry in resume.work:
        title = entry.get("position", "")
        company = entry.get("name", "")
        # LinkedIn's description box takes plain text; bullets survive as "• ".
        body = "\n".join(f"• {h}" for h in (entry.get("highlights") or []))
        out.append(Block(
            f"{title} — {company}", body, LINKEDIN_LIMITS["experience"],
            note=f"{entry.get('location', '')} · "
                 f"{date_range(entry.get('startDate'), entry.get('endDate'))}".strip(" ·"),
        ))

    keywords = [k for g in resume.skills for k in (g.get("keywords") or [])]
    if keywords:
        long = [k for k in keywords if len(k) > LINKEDIN_LIMITS["skill"]]
        note = f"{len(keywords)} skills, one per line"
        if long:
            note += f" — {len(long)} exceed the {LINKEDIN_LIMITS['skill']}-char limit"
        out.append(Block("Skills", "\n".join(keywords), note=note))

    # Many portals have a single "paste your resume" box.
    from .markdown import render as md_render
    out.append(Block("Plain-text resume", md_render(resume),
                     note="for “paste your resume” boxes"))
    return out


def page(resume) -> str:
    blocks = build(resume)
    cards = []
    for i, b in enumerate(blocks):
        if b.limit:
            state = "over" if b.over else ("near" if b.length > b.limit * 0.9 else "ok")
            counter = f'<span class="count {state}">{b.length:,} / {b.limit:,}</span>'
        else:
            counter = f'<span class="count">{b.length:,} chars</span>'
        note = f'<div class="note">{html.escape(b.note)}</div>' if b.note else ""
        warn = ('<div class="warn">Over the limit — this will be truncated on paste.</div>'
                if b.over else "")
        cards.append(f"""
    <section>
      <div class="head">
        <b>{html.escape(b.label)}</b>{counter}
        <button data-i="{i}">Copy</button>
      </div>
      {note}{warn}
      <textarea id="b{i}" readonly rows="{min(16, max(3, b.text.count(chr(10)) + 2))}"
        >{html.escape(b.text)}</textarea>
    </section>""")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(resume.name)} — copy blocks</title>
<style>
  :root{{--bg:#f2f4f7;--card:#fff;--ink:#12151a;--muted:#69707c;--line:#e0e4ea;
         --accent:#0b6fa4;--ok:#1a7f42;--near:#a4700f;--over:#b3261e}}
  @media (prefers-color-scheme:dark){{
    :root{{--bg:#0e1014;--card:#181b21;--ink:#e8eaef;--muted:#98a0ad;--line:#282d36;
           --accent:#63b3e0;--ok:#5fd08b;--near:#e0b054;--over:#ff8f88}}}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);
        font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif}}
  .wrap{{max-width:820px;margin:0 auto;padding:26px 22px 70px}}
  h1{{font-size:19px;margin:0 0 4px}}
  p.sub{{margin:0 0 22px;color:var(--muted)}}
  section{{background:var(--card);border:1px solid var(--line);border-radius:11px;
           padding:13px 14px;margin-bottom:14px}}
  .head{{display:flex;align-items:center;gap:10px;margin-bottom:7px}}
  .count{{font:12px ui-monospace,Menlo,monospace;color:var(--muted);margin-left:auto}}
  .count.ok{{color:var(--ok)}} .count.near{{color:var(--near)}}
  .count.over{{color:var(--over);font-weight:700}}
  .note{{font-size:12.5px;color:var(--muted);margin-bottom:7px}}
  .warn{{font-size:12.5px;color:var(--over);font-weight:600;margin-bottom:7px}}
  textarea{{width:100%;font:12.5px/1.5 ui-monospace,Menlo,monospace;color:var(--ink);
            background:var(--bg);border:1px solid var(--line);border-radius:8px;
            padding:9px 10px;resize:vertical}}
  button{{font:inherit;font-size:12.5px;font-weight:600;color:#fff;background:var(--accent);
          border:0;border-radius:7px;padding:5px 12px;cursor:pointer}}
  button:hover{{filter:brightness(1.08)}}
  .toast{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--ink);
          color:var(--bg);padding:9px 15px;border-radius:8px;font-size:13px;opacity:0;
          transition:opacity .2s;pointer-events:none}}
  .toast.on{{opacity:1}}
</style></head><body><div class="wrap">
  <h1>{html.escape(resume.name)} — copy blocks</h1>
  <p class="sub">Pre-formatted for LinkedIn and application forms, measured against each
  field's limit. LinkedIn does not expose profile editing over its API, so this part is
  manual by necessity — the counts are here so nothing gets silently truncated on paste.</p>
  {"".join(cards)}
</div>
<div class="toast" id="t"></div>
<script>
document.querySelectorAll("button[data-i]").forEach(b => b.onclick = () => {{
  const ta = document.getElementById("b" + b.dataset.i);
  navigator.clipboard.writeText(ta.value).then(() => {{
    const t = document.getElementById("t");
    t.textContent = "Copied " + ta.value.length.toLocaleString() + " characters";
    t.classList.add("on"); setTimeout(() => t.classList.remove("on"), 1800);
  }});
}});
</script>
</body></html>
"""
