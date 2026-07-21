"""A static, browsable catalogue of layouts.

`serve` is the richer tool — it steers, and it keeps state. But it needs a running
process, and plenty of people (reasonably) prefer to open a file in a browser and
flip through it. A catalogue is also the thing you can commit, link, or hand to
someone else; a localhost URL is not.

Previews are HTML in iframes, not pre-rendered PDFs. That is the difference between
a catalogue that builds instantly and one that costs a second per variant, which is
what made an earlier version cap out at eighteen options.

The output is self-contained and works from `file://` — no server, no build step.
"""
from __future__ import annotations

import html
from pathlib import Path

from . import compose, space


def build(resume, count: int, out_dir: Path, seed: int = 0) -> tuple[Path, list]:
    """Render `count` layouts plus an index. Returns (index path, specs)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = space.diverse(count, seed=seed)

    for spec in specs:
        (out_dir / f"{spec.name}.html").write_text(
            compose.render(resume, spec), encoding="utf-8")

    index = out_dir / "index.html"
    index.write_text(_index(specs, resume), encoding="utf-8")
    return index, specs


def _index(specs, resume) -> str:
    cards = []
    for n, spec in enumerate(specs, 1):
        axes = "".join(
            f'<span class="chip">{html.escape(v)}</span>' for v in (
                compose.PALETTES[spec.palette][0],
                compose.TYPEFACES[spec.typeface][0],
                spec.header,
                spec.skills,
                spec.promo,
                compose.DENSITIES[spec.density][0],
            ))
        cards.append(f"""
      <figure id="{spec.name}">
        <div class="shot"><iframe src="{spec.name}.html" loading="lazy"
             title="{spec.name}" scrolling="no"></iframe></div>
        <figcaption>
          <div class="row"><span class="num">{n}</span>
            <code class="nm">{spec.name}</code></div>
          <div class="chips">{axes}</div>
          <div class="row">
            <a href="{spec.name}.html" target="_blank">Open full size</a>
            <button data-name="{spec.name}">Copy publish command</button>
          </div>
        </figcaption>
      </figure>""")

    name = html.escape(resume.name or "Resume")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} - layout catalogue</title>
<style>
  :root{{--bg:#f2f4f7;--card:#fff;--ink:#12151a;--muted:#69707c;--line:#e0e4ea;--accent:#0b6fa4}}
  @media (prefers-color-scheme:dark){{
    :root{{--bg:#0e1014;--card:#181b21;--ink:#e8eaef;--muted:#98a0ad;--line:#282d36;--accent:#63b3e0}}}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);
        font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif}}
  header{{padding:22px 24px 6px}}
  h1{{margin:0 0 4px;font-size:19px;letter-spacing:-.2px}}
  p.sub{{margin:0;color:var(--muted);max-width:68ch}}
  code{{font:12px ui-monospace,Menlo,monospace;background:var(--bg);
        border:1px solid var(--line);border-radius:5px;padding:1px 6px}}
  .grid{{display:grid;gap:20px;padding:20px 24px 60px;
         grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}}
  figure{{margin:0;background:var(--card);border:1px solid var(--line);border-radius:12px;
          overflow:hidden;box-shadow:0 1px 2px rgba(16,24,40,.05),0 6px 16px rgba(16,24,40,.05)}}
  /* A real render, scaled. Not a screenshot - identical to what publishes. */
  .shot{{height:390px;overflow:hidden;background:#fff;border-bottom:1px solid var(--line)}}
  .shot iframe{{width:816px;height:1056px;border:0;transform:scale(.42);
                transform-origin:top left;pointer-events:none}}
  figcaption{{padding:10px 12px;display:flex;flex-direction:column;gap:8px}}
  .row{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
  .num{{font-size:11px;font-weight:700;color:#fff;background:var(--accent);
        border-radius:20px;min-width:20px;text-align:center;padding:1px 6px}}
  .nm{{font-weight:600}}
  .chips{{display:flex;flex-wrap:wrap;gap:4px}}
  .chip{{font-size:10.5px;color:var(--muted);background:var(--bg);
         border:1px solid var(--line);border-radius:20px;padding:1px 7px}}
  a,button{{font:inherit;font-size:12.5px;color:var(--accent);background:none;
            border:0;padding:0;cursor:pointer;text-decoration:none}}
  a:hover,button:hover{{text-decoration:underline}}
  .toast{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--ink);
          color:var(--bg);padding:9px 15px;border-radius:8px;font-size:13px;opacity:0;
          transition:opacity .2s;pointer-events:none}}
  .toast.on{{opacity:1}}
</style></head><body>
<header>
  <h1>{name} — layout catalogue</h1>
  <p class="sub">{len(specs)} of {space.TOTAL:,} possible layouts, spread across the design
  space. Every preview is a live render, identical to what publishes. Pick one, then run
  <code>resume-pipeline publish --theme &lt;name&gt;</code> — or use
  <code>resume-pipeline serve</code> to browse interactively and steer toward what you like.</p>
</header>
<div class="grid">{"".join(cards)}
</div>
<div class="toast" id="t"></div>
<script>
document.querySelectorAll("button[data-name]").forEach(b => b.onclick = () => {{
  const cmd = `resume-pipeline publish --theme ${{b.dataset.name}}`;
  navigator.clipboard.writeText(cmd).then(() => {{
    const t = document.getElementById("t");
    t.textContent = "Copied: " + cmd; t.classList.add("on");
    setTimeout(() => t.classList.remove("on"), 2200);
  }});
}});
</script>
</body></html>
"""
