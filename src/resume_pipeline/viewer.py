"""The one viewer: a grid of live layout previews.

There used to be two of these — a static catalogue and a served explorer — rendering
the same grid of the same scaled iframes, differing only in where a preview came from
and whether it could export. They drifted, as duplicated UI does. This is the single
implementation, parameterised by the two things that actually differ:

- **where previews come from** — a sibling `.html` file, or a `/preview/` route;
- **whether the page can act** — a served page can export a PDF; a file on disk cannot,
  so that control is simply absent rather than present and broken.

Previews are HTML in scaled iframes, never pre-rendered images. They are therefore
*live* — what you see is what publishes, and a catalogue costs milliseconds to build
rather than a second per variant.
"""
from __future__ import annotations

import html
import json

from . import compose, space


def axes_of(spec: compose.Spec) -> dict[str, str]:
    """The spec's axis values, keyed by axis name — the facets, and the chips."""
    return {
        "palette": compose.PALETTES[spec.palette][0],
        "typeface": compose.TYPEFACES[spec.typeface][0],
        "header": spec.header,
        "skills": spec.skills,
        "promo": spec.promo,
        "density": compose.DENSITIES[spec.density][0],
    }


def describe(spec: compose.Spec) -> dict:
    """A spec as the page (and an agent reading `options.json`) sees it."""
    return {
        "name": spec.name,
        "description": spec.description,
        "axes": axes_of(spec),
    }


def page(specs, resume, *, preview: str = "file", exportable: bool = False) -> str:
    """Render the viewer.

    `preview` is "file" (previews sit beside the page as `<name>.html`) or "route"
    (previews come from `/preview/<name>` on a running server).
    """
    options = [describe(s) for s in specs]
    title = html.escape(resume.name or "Resume")
    return _PAGE.replace("__TITLE__", title) \
                .replace("__TOTAL__", f"{space.TOTAL:,}") \
                .replace("__PREVIEW__", preview) \
                .replace("__EXPORTABLE__", "true" if exportable else "false") \
                .replace("__OPTIONS__", json.dumps(options))


# The page is one string with a handful of substitutions rather than a template
# engine: it is the only page, it has no dependencies, and it has to work equally
# from `file://` and from the server.
_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ — layouts</title>
<style>
  :root{
    --bg:#f2f4f7; --card:#fff; --ink:#12151a; --muted:#69707c; --line:#e0e4ea;
    --accent:#0b6fa4;
    --shadow:0 1px 2px rgba(16,24,40,.06),0 4px 12px rgba(16,24,40,.06);
  }
  @media (prefers-color-scheme:dark){
    :root{ --bg:#0e1014; --card:#181b21; --ink:#e8eaef; --muted:#98a0ad; --line:#282d36;
           --accent:#63b3e0;
           --shadow:0 1px 2px rgba(0,0,0,.4),0 6px 18px rgba(0,0,0,.35); }
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{background:var(--bg);color:var(--ink);
       font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif}

  header{position:sticky;top:0;z-index:20;padding:14px 20px 10px;background:var(--card);
         border-bottom:1px solid var(--line)}
  .bar{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
  h1{font-size:15px;margin:0;letter-spacing:-.2px;font-weight:700}
  .meta{color:var(--muted);font-size:12.5px}
  .grow{flex:1}
  .hint{margin:6px 0 0;color:var(--muted);font-size:12.5px;max-width:78ch}

  button{font:inherit;font-size:13px;color:var(--ink);background:var(--card);
         border:1px solid var(--line);border-radius:8px;padding:6px 12px;cursor:pointer;
         transition:border-color .12s,background .12s}
  button:hover{border-color:var(--accent)}
  button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
  button.primary:hover{filter:brightness(1.08)}
  button.ghost{border-color:transparent;color:var(--muted)}

  .grid{display:grid;gap:18px;padding:20px;
        grid-template-columns:repeat(auto-fill,minmax(270px,1fr))}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;
        overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column;
        transition:border-color .12s,transform .12s}
  .card:hover{transform:translateY(-2px)}

  /* A real 8.5in-wide render, scaled down — not a screenshot. What you see here is
     exactly what publishes. */
  .shot{position:relative;height:330px;overflow:hidden;background:#fff;cursor:pointer;
        border-bottom:1px solid var(--line)}
  .shot iframe{position:absolute;top:0;left:0;width:816px;height:1056px;border:0;
               transform-origin:top left;pointer-events:none}
  .shot .veil{position:absolute;inset:0}

  .info{padding:9px 11px;display:flex;flex-direction:column;gap:7px}
  .row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .num{font-size:11px;font-weight:700;color:#fff;background:var(--accent);
       border-radius:20px;min-width:20px;text-align:center;padding:1px 6px}
  .nm{font-size:12px;font-weight:700;letter-spacing:-.1px;word-break:break-all}
  .chips{display:flex;flex-wrap:wrap;gap:4px}
  .chip{font-size:10.5px;background:var(--bg);border:1px solid var(--line);
        border-radius:20px;padding:1px 7px;color:var(--muted)}
  .acts{display:flex;gap:6px}
  .acts button{flex:1;padding:5px 0;font-size:12px}

  dialog{border:0;border-radius:14px;padding:0;background:var(--card);color:var(--ink);
         width:min(94vw,900px);box-shadow:var(--shadow)}
  dialog::backdrop{background:rgba(8,10,14,.55)}
  .dlg-bar{display:flex;align-items:center;gap:10px;padding:11px 14px;
           border-bottom:1px solid var(--line);flex-wrap:wrap}
  dialog iframe{width:100%;height:min(76vh,1056px);border:0;background:#fff}
  .toast{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);
         background:var(--ink);color:var(--bg);padding:9px 16px;border-radius:8px;
         font-size:13px;opacity:0;transition:opacity .2s;pointer-events:none;z-index:60}
  .toast.show{opacity:1}
</style></head><body>

<header>
  <div class="bar">
    <h1>__TITLE__ — layouts</h1>
    <span class="meta" id="meta"></span>
    <span class="grow"></span>
    <span class="meta"><kbd>↵</kbd> open · <kbd>Esc</kbd> close</span>
  </div>
  <p class="hint"><b>Pick one and tell your agent</b> — “publish number 7”, or paste the
  name. Every preview is a live render, identical to what gets published.</p>
</header>

<div class="grid" id="grid"></div>

<dialog id="dlg">
  <div class="dlg-bar">
    <b id="dlgName"></b>
    <span class="meta" id="dlgDesc"></span>
    <span class="grow"></span>
    <button id="dlgCopy">Copy name</button>
    <button id="dlgExport" class="primary" hidden>Export PDF</button>
    <button id="dlgClose" class="ghost">Close</button>
  </div>
  <iframe id="dlgFrame" title="preview"></iframe>
</dialog>

<div class="toast" id="toast"></div>

<script>
const OPTIONS    = __OPTIONS__;
const PREVIEW    = "__PREVIEW__";
const EXPORTABLE = __EXPORTABLE__;
const TOTAL      = "__TOTAL__";

const $ = s => document.querySelector(s);
const previewUrl = name =>
  PREVIEW === "route" ? "/preview/" + encodeURIComponent(name) : name + ".html";

let toastTimer;
function toast(msg){
  const t = $("#toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(()=>t.classList.remove("show"), 1900);
}

function copy(name){
  navigator.clipboard.writeText(name).then(()=>toast("Copied: " + name),
                                           ()=>toast("Could not copy"));
}

function fitShot(frame){
  // Scale the 816px-wide render to whatever width the card ended up being.
  const w = frame.parentElement.clientWidth;
  frame.style.transform = `scale(${w/816})`;
}

let cursor = 0;

function render(){
  $("#meta").textContent = `${OPTIONS.length} of ${TOTAL} possible layouts`;
  const grid = $("#grid");
  grid.innerHTML = "";
  OPTIONS.forEach((v, i) => {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="shot"><iframe loading="lazy" src="${previewUrl(v.name)}"
           title="${v.name}" scrolling="no"></iframe><div class="veil"></div></div>
      <div class="info">
        <div class="row"><span class="num">${i+1}</span><span class="nm">${v.name}</span></div>
        <div class="chips">${Object.values(v.axes)
          .map(val => `<span class="chip">${val}</span>`).join("")}</div>
        <div class="acts">
          <button class="o">Open</button>
          <button class="c">Copy name</button>
        </div>
      </div>`;
    const frame = card.querySelector("iframe");
    frame.addEventListener("load", ()=>fitShot(frame));
    new ResizeObserver(()=>fitShot(frame)).observe(card.querySelector(".shot"));
    card.querySelector(".shot").onclick = ()=>{ cursor=i; open(v); };
    card.querySelector(".o").onclick = ()=>{ cursor=i; open(v); };
    card.querySelector(".c").onclick = ()=>copy(v.name);
    grid.appendChild(card);
  });
}

function open(v){
  $("#dlgName").textContent = v.name;
  $("#dlgDesc").textContent = v.description;
  $("#dlgFrame").src = previewUrl(v.name);
  $("#dlgCopy").onclick = ()=>copy(v.name);
  const ex = $("#dlgExport");
  ex.hidden = !EXPORTABLE;
  if(EXPORTABLE){
    ex.onclick = async ()=>{
      ex.disabled = true; ex.textContent = "Exporting…";
      const r = await fetch("/api/export", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ name: v.name })
      }).then(r=>r.json()).catch(e=>({error:String(e)}));
      ex.disabled = false; ex.textContent = "Export PDF";
      toast(r.error ? ("Export failed: " + r.error)
                    : ("Exported " + r.path.split("/").pop()));
    };
  }
  $("#dlg").showModal();
}

$("#dlgClose").onclick = ()=>$("#dlg").close();

addEventListener("keydown", e => {
  if($("#dlg").open){ if(e.key==="Escape") $("#dlg").close(); return; }
  if(e.key==="ArrowRight"||e.key==="j"){ cursor=Math.min(cursor+1,OPTIONS.length-1); }
  else if(e.key==="ArrowLeft"||e.key==="k"){ cursor=Math.max(cursor-1,0); }
  else if(e.key==="Enter"&&OPTIONS[cursor]){ open(OPTIONS[cursor]); }
});

render();
</script>
</body></html>
"""
