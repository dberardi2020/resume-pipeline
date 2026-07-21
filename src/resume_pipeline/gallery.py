"""Build the theme gallery — a flip-through picker for rendered variants.

Comparing layouts by opening PDFs one at a time is the bottleneck on trying more
of them: the cost of *evaluating* an option is what limits how many you generate,
not the cost of producing it. So the gallery puts one large preview on screen and
makes moving between them a single keypress.

Deliberately stateless in what it renders — the page is regenerated from whatever
themes were built, and holds no opinion of its own. The one exception is the
favourite toggle, which lives in `localStorage`: it survives a rebuild, and never
leaves the browser.

Emits a self-contained file. No network, no build step, opens from `file://`.
"""
from __future__ import annotations

import json


def render(themes_, stem: str) -> str:
    items = [
        {
            "name": t.name,
            "desc": t.description,
            "pdf": f"{stem}.{t.name}.pdf",
            "html": f"{stem}.{t.name}.html",
            "ats": bool(t.ats_safe),
            "cols": t.columns,
        }
        for t in themes_
    ]
    data = json.dumps(items, indent=2)
    return _TEMPLATE.replace("__DATA__", data)


_TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Resume gallery</title>
<style>
  :root {
    --bg:#f4f5f7; --panel:#fff; --ink:#15181d; --muted:#6b7280;
    --line:#e2e5ea; --accent:#0b6fa4; --ok-bg:#e3f5ea; --ok-fg:#1a7f42;
    --warn-bg:#fdecec; --warn-fg:#b3261e; --star:#e8a92b;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#101216; --panel:#1b1e24; --ink:#e7e9ee; --muted:#9aa1ad;
            --line:#2a2f38; --accent:#63b3e0; --ok-bg:#12351f; --ok-fg:#63d18c;
            --warn-bg:#3a1614; --warn-fg:#ff8f88; }
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif; }
  header { display:flex; align-items:center; gap:14px; padding:14px 20px;
           border-bottom:1px solid var(--line); background:var(--panel);
           position:sticky; top:0; z-index:5; flex-wrap:wrap; }
  h1 { font-size:16px; margin:0; letter-spacing:-.2px; }
  .count { color:var(--muted); font-size:13px; }
  .spacer { flex:1; }
  button { font:inherit; color:var(--ink); background:var(--panel);
           border:1px solid var(--line); border-radius:8px; padding:6px 12px;
           cursor:pointer; }
  button:hover { border-color:var(--accent); }
  button.primary { background:var(--accent); color:#fff; border-color:var(--accent); }
  .stage { display:grid; grid-template-columns:230px 1fr; gap:0; height:calc(100vh - 59px); }
  nav { border-right:1px solid var(--line); background:var(--panel); overflow-y:auto; padding:10px; }
  .thumb { display:flex; align-items:center; gap:8px; width:100%; text-align:left;
           padding:9px 10px; border:1px solid transparent; border-radius:8px;
           background:none; cursor:pointer; margin-bottom:2px; }
  .thumb:hover { background:var(--bg); }
  .thumb.active { border-color:var(--accent); background:var(--bg); }
  .thumb .nm { font-weight:600; font-size:14px; }
  .thumb .fav { margin-left:auto; color:var(--star); font-size:13px; }
  main { display:flex; flex-direction:column; min-width:0; }
  .bar { display:flex; align-items:center; gap:10px; padding:10px 18px;
         border-bottom:1px solid var(--line); background:var(--panel); flex-wrap:wrap; }
  .nm-big { font-weight:700; font-size:15px; }
  .desc { color:var(--muted); font-size:13px; }
  .badge { font-size:11px; font-weight:700; padding:2px 8px; border-radius:20px; }
  .ok { background:var(--ok-bg); color:var(--ok-fg); }
  .warn { background:var(--warn-bg); color:var(--warn-fg); }
  a { color:var(--accent); font-size:13px; text-decoration:none; }
  iframe { flex:1; width:100%; border:0; background:#fff; }
  kbd { font:12px ui-monospace,Menlo,monospace; background:var(--bg);
        border:1px solid var(--line); border-bottom-width:2px; border-radius:5px;
        padding:1px 6px; color:var(--muted); }
  .hint { color:var(--muted); font-size:12px; display:flex; gap:6px; align-items:center; }
  @media (max-width:820px) { .stage { grid-template-columns:1fr; } nav { display:none; } }
</style></head><body>
<header>
  <h1>Resume gallery</h1>
  <span class="count" id="count"></span>
  <span class="spacer"></span>
  <span class="hint"><kbd>←</kbd><kbd>→</kbd> flip <kbd>F</kbd> favourite</span>
  <button id="favOnly">Favourites only</button>
</header>
<div class="stage">
  <nav id="nav"></nav>
  <main>
    <div class="bar">
      <span class="nm-big" id="nm"></span>
      <span class="badge" id="badge"></span>
      <span class="desc" id="desc"></span>
      <span class="spacer"></span>
      <button id="favBtn"></button>
      <a id="openPdf" href="#">PDF</a>
      <a id="openHtml" href="#">HTML</a>
    </div>
    <iframe id="view" title="preview"></iframe>
  </main>
</div>
<script>
const ALL = __DATA__;
const KEY = "resume-gallery-favourites";
let favs = new Set(JSON.parse(localStorage.getItem(KEY) || "[]"));
let favOnly = false, i = 0;

const list = () => favOnly ? ALL.filter(t => favs.has(t.name)) : ALL;
const saveFavs = () => localStorage.setItem(KEY, JSON.stringify([...favs]));

function draw() {
  const items = list();
  if (!items.length) { favOnly = false; return draw(); }
  i = (i + items.length) % items.length;
  const t = items[i];

  document.getElementById("count").textContent = `${i + 1} of ${items.length}`;
  document.getElementById("nm").textContent = t.name;
  document.getElementById("desc").textContent = t.desc;
  const badge = document.getElementById("badge");
  badge.textContent = t.ats ? "ATS-safe" : `not ATS-safe · ${t.cols}-col`;
  badge.className = "badge " + (t.ats ? "ok" : "warn");
  document.getElementById("openPdf").href = t.pdf;
  document.getElementById("openHtml").href = t.html;
  document.getElementById("favBtn").textContent =
    (favs.has(t.name) ? "★ Favourited" : "☆ Favourite");
  // #view=FitH so the whole page width is visible without manual zooming.
  document.getElementById("view").src = t.pdf + "#toolbar=0&navpanes=0&view=FitH";

  const nav = document.getElementById("nav");
  nav.innerHTML = "";
  items.forEach((x, n) => {
    const b = document.createElement("button");
    b.className = "thumb" + (n === i ? " active" : "");
    b.innerHTML = `<span class="nm">${x.name}</span>` +
      `<span class="badge ${x.ats ? "ok" : "warn"}">${x.ats ? "ATS" : "!"}</span>` +
      (favs.has(x.name) ? `<span class="fav">★</span>` : "");
    b.onclick = () => { i = n; draw(); };
    nav.appendChild(b);
  });
  document.getElementById("favOnly").className = favOnly ? "primary" : "";
}

function toggleFav() {
  const t = list()[i];
  if (!t) return;
  favs.has(t.name) ? favs.delete(t.name) : favs.add(t.name);
  saveFavs(); draw();
}

document.getElementById("favBtn").onclick = toggleFav;
document.getElementById("favOnly").onclick = () => { favOnly = !favOnly; i = 0; draw(); };
addEventListener("keydown", e => {
  if (e.key === "ArrowRight" || e.key === "j") { i++; draw(); }
  else if (e.key === "ArrowLeft" || e.key === "k") { i--; draw(); }
  else if (e.key.toLowerCase() === "f") toggleFav();
});
draw();
</script>
</body></html>
"""
