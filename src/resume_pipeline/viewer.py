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
        "grouping": spec.grouping,
    }


def describe(spec: compose.Spec) -> dict:
    """A spec as the page (and an agent reading `options.json`) sees it."""
    return {
        "name": spec.name,
        "description": spec.description,
        "axes": axes_of(spec),
    }


def page(specs, resume, *, preview: str = "file", exportable: bool = False,
         pages: int = 0) -> str:
    """Render the viewer.

    `preview` is "file" (previews sit beside the page as `<name>.html`) or "route"
    (previews come from `/preview/<name>` on a running server).
    """
    options = [describe(s) for s in specs]
    title = html.escape(resume.name or "Resume")
    # Palette is one axis, and the first segment of every spec name — so the
    # viewer can offer "this layout, that colour" as an instant re-render of a
    # neighbouring spec rather than a live edit. The swatch colour is the accent.
    palettes = [{"name": p[0], "accent": p[1]} for p in compose.PALETTES]
    # Typeface is the same story on the second name segment: a small closed set, so
    # it earns its own "hold this constant" bar too — but sample chips rather than
    # swatches, each rendered in its own face, since a font can't be a dot. (RP-0037.)
    typefaces = [{"name": t[0], "font": t[1]} for t in compose.TYPEFACES]
    return _PAGE.replace("__PAGES__", str(pages)) \
                .replace("__TITLE__", title) \
                .replace("__TOTAL__", f"{space.TOTAL:,}") \
                .replace("__TOTAL_N__", str(space.TOTAL)) \
                .replace("__PREVIEW__", preview) \
                .replace("__EXPORTABLE__", "true" if exportable else "false") \
                .replace("__PALETTES__", json.dumps(palettes)) \
                .replace("__TYPEFACES__", json.dumps(typefaces)) \
                .replace("__OPTIONS__", json.dumps(options))


# The page is one string with a handful of substitutions rather than a template
# engine: it is the only page, it has no dependencies, and it has to work equally
# from `file://` and from the server.
_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ — Layouts</title>
<style>
  :root{
    --bg:#f2f4f7; --card:#fff; --ink:#12151a; --muted:#69707c; --line:#e0e4ea;
    --accent:#0b6fa4;
    /* Buttons need a surface of their own. Using --card put a card-coloured
       button on a card-coloured panel, which in dark mode left only a faint
       border to see — controls read as disabled, or vanished entirely. */
    --btn:#f1f4f8; --btn-line:#c9d0da;
    --shadow:0 1px 2px rgba(16,24,40,.06),0 4px 12px rgba(16,24,40,.06);
  }
  @media (prefers-color-scheme:dark){
    :root{ --bg:#0e1014; --card:#181b21; --ink:#e8eaef; --muted:#98a0ad; --line:#282d36;
           --accent:#63b3e0;
           --btn:#262b36; --btn-line:#3c4453;
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
  .statusline{margin-top:5px}
  .grow{flex:1}
  .hint{margin:6px 0 0;color:var(--muted);font-size:12.5px;max-width:82ch}
  .nav{display:flex;gap:6px;align-items:center}
  .nav button{padding:5px 11px}

  button{font:inherit;font-size:13px;font-weight:500;color:var(--ink);
         background:var(--btn);border:1px solid var(--btn-line);border-radius:8px;
         padding:6px 12px;cursor:pointer;white-space:nowrap;
         transition:border-color .12s,background .12s,color .12s}
  button:hover{border-color:var(--accent);color:var(--accent)}
  button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
  button.primary:hover{filter:brightness(1.08);color:#fff}

  .grid{display:grid;gap:18px;padding:20px;
        grid-template-columns:repeat(auto-fill,minmax(270px,1fr))}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;
        overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column;
        transition:border-color .12s,transform .12s}
  .card:hover{transform:translateY(-2px)}

  /* A real 8.5in-wide render, scaled down — not a screenshot. What you see here is
     exactly what publishes. */
  .shot{position:relative;height:400px;overflow:hidden;background:#fff;cursor:pointer;
        border-bottom:1px solid var(--line)}
  .shot iframe{position:absolute;top:0;left:0;width:816px;height:1056px;border:0;
               transform-origin:top left;pointer-events:none}
  .shot .veil{position:absolute;inset:0}

  /* Cards in a row are as tall as the tallest, and chip rows wrap to different
     heights — so the actions are pinned to the bottom rather than floating
     wherever the chips happen to end. */
  .info{padding:9px 11px;display:flex;flex-direction:column;gap:7px;flex:1}
  .row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  /* Names are long and hyphenated by design. `break-all` would split them
     mid-word (`badge-co / mpact`); this wraps at the hyphens instead. */
  .nm{font-size:12px;font-weight:700;letter-spacing:-.1px;
      overflow-wrap:anywhere;word-break:normal;line-height:1.35}
  .chips{display:flex;flex-wrap:wrap;gap:4px}
  .chip{font-size:10.5px;background:var(--bg);border:1px solid var(--line);
        border-radius:20px;padding:1px 7px;color:var(--muted)}
  /* Pinned to the bottom: cards in a row are as tall as the tallest, and chip
     rows wrap to different heights, so without this the buttons sit at a
     different height on every card. */
  .acts{display:flex;gap:6px;margin-top:auto}
  .acts button{flex:1;padding:5px 0;font-size:12px}

  dialog{border:0;border-radius:14px;padding:0;background:var(--card);color:var(--ink);
         width:min(94vw,900px);box-shadow:var(--shadow)}
  dialog::backdrop{background:rgba(8,10,14,.55)}
  /* No wrapping: a long spec name used to push Close onto a line of its own,
     which is where it went to hide. The name truncates instead. */
  .dlg-bar{display:flex;align-items:center;gap:10px;padding:11px 14px;
           border-bottom:1px solid var(--line);flex-wrap:nowrap}
  .dlg-id{min-width:0;flex:1;display:flex;flex-direction:column;gap:1px}
  .dlg-id b{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .dlg-id .meta{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .dlg-acts{display:flex;gap:8px;flex:0 0 auto}
  dialog iframe{width:100%;height:min(76vh,1056px);border:0;background:#fff}
  /* With a dialog open, reaching the bottom of the preview handed the scroll
     back to the grid behind it. Lock the page while the modal is up. */
  body.modal-open{overflow:hidden}

  /* Colour bar. Palette is one axis but the one people react to first, so it is
     lifted out of the chips into its own always-visible control: pick a colour
     and every layout re-renders in it, so structure can be judged with colour
     held constant. Purely a re-render of a neighbouring spec — no live edit. */
  .palette{display:flex;align-items:center;gap:7px;margin:9px 0 2px;flex-wrap:wrap}
  .palette .lbl{font-size:12px;color:var(--muted)}
  .sw{width:20px;height:20px;border-radius:50%;border:2px solid transparent;
      cursor:pointer;padding:0;background-clip:padding-box;transition:transform .1s}
  .sw:hover{transform:scale(1.15)}
  .sw.on{border-color:var(--ink);box-shadow:0 0 0 2px var(--card),0 0 0 3px var(--ink)}
  .sw-varied{width:auto;height:auto;border-radius:20px;padding:2px 10px;font-size:12px;
             border:1px solid var(--btn-line);background:var(--btn);color:var(--ink)}
  .sw-varied.on{border-color:var(--accent);color:var(--accent);font-weight:600}
  .dlg-palette{padding:8px 14px;border-bottom:1px solid var(--line)}

  /* Type bar. Typeface is the second axis and the second name segment — the same
     "hold one constant while the rest vary" control as colour, but a font is not a
     dot: each chip is a text sample rendered in its own face, so you pick by the
     look of the letters, not a label. Only four faces, so it costs less room than
     the colour swatches. */
  .tf{font-size:12.5px;line-height:1;padding:4px 11px;border-radius:20px;
      border:1px solid var(--btn-line);background:var(--btn);color:var(--ink);
      cursor:pointer;transition:border-color .12s,color .12s}
  .tf:hover{border-color:var(--accent);color:var(--accent)}
  .tf.on{border-color:var(--accent);color:var(--accent);font-weight:600}
  .dlg-typeface{padding:8px 14px;border-bottom:1px solid var(--line)}

  .toast{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);
         background:var(--ink);color:var(--bg);padding:9px 16px;border-radius:8px;
         font-size:13px;opacity:0;transition:opacity .2s;pointer-events:none;z-index:60}
  .toast.show{opacity:1}
</style></head><body>

<header>
  <div class="bar">
    <h1>__TITLE__ — Layouts</h1>
    <span class="grow"></span>
    <span class="meta" id="pageMeta"></span>
    <span class="nav" id="nav" hidden>
      <button id="first" title="Back to page 1">«</button>
      <button id="prev" title="Previous page">‹</button>
      <button id="shuffle">Shuffle</button>
      <button id="next" title="Next page">›</button>
    </span>
  </div>
  <!-- The layout count / active holds live on their own line: variable-length text
       here used to push the nav buttons onto a second row once an axis was held. -->
  <div class="meta statusline" id="meta"></div>
  <div class="palette" id="palette"></div>
  <div class="palette" id="typeface"></div>
  <p class="hint">Layouts are <b>generated</b>, not templates — each is one combination of
  seven independent choices, so there are __TOTAL__ of them. The arrows walk the space in
  order; <b>Shuffle</b> jumps somewhere else entirely. Pick a <b>colour</b> or <b>typeface</b>
  to hold it constant while you judge the rest. Open any layout, then <b>Make this my resume</b>
  to publish it — every preview is a live render, identical to what gets published.</p>
</header>

<div class="grid" id="grid"></div>

<dialog id="dlg">
  <div class="dlg-bar">
    <div class="dlg-id">
      <b id="dlgName"></b>
      <span class="meta" id="dlgDesc"></span>
    </div>
    <div class="dlg-acts">
      <button id="dlgCopy">Copy Name</button>
      <button id="dlgExport" hidden>Export PDF</button>
      <button id="dlgPublish" class="primary" hidden>★ Make this my resume</button>
      <button id="dlgClose">Close</button>
    </div>
  </div>
  <div class="palette dlg-palette" id="dlgPalette"></div>
  <div class="palette dlg-typeface" id="dlgTypeface"></div>
  <iframe id="dlgFrame" title="preview"></iframe>
</dialog>

<div class="toast" id="toast"></div>

<script>
let   OPTIONS    = __OPTIONS__;
let   PAGES      = __PAGES__;   // updated as filtering narrows the set
let   PAGE_INDEX = 0;
const PREVIEW    = "__PREVIEW__";
const EXPORTABLE = __EXPORTABLE__;
let   TOTAL      = __TOTAL_N__; // the (filtered) layout count, a number
const PALETTES   = __PALETTES__;
const TYPEFACES  = __TYPEFACES__;
let   PALETTE    = null;   // null = as generated; otherwise a forced palette
let   TYPEFACE   = null;   // null = as generated; otherwise a forced typeface

const $ = s => document.querySelector(s);
const previewUrl = name =>
  PREVIEW === "route" ? "/preview/" + encodeURIComponent(name) : name + ".html";

// Palette and typeface are the first two segments of a spec name. Holding one
// constant is therefore just swapping its segment — a different, equally-valid
// spec, rendered the same way, so what you see stays exactly what would publish.
const pin = name => {
  if(!PALETTE && !TYPEFACE) return name;
  const parts = name.split("-");
  if(PALETTE)  parts[0] = PALETTE;   // palette is segment 0
  if(TYPEFACE) parts[1] = TYPEFACE;  // typeface is segment 1
  return parts.join("-");
};

// The static catalogue writes previews as sibling files, only for the specs it
// shipped — so a pinned name may have no file. Holding an axis is a served-viewer
// affordance; disable it when previews come from disk.
const CAN_PIN = PREVIEW === "route";

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
let CURRENT = null;   // the spec currently open in the dialog

function render(){
  paletteBar($("#palette"));
  typefaceBar($("#typeface"));
  // Served, the count follows the held axes: hold a colour and "10,080 layouts"
  // becomes the size of that filtered subset, with the page counter tracking where
  // you are in it. The static catalogue is a fixed sample, so it keeps "N of TOTAL".
  if(PREVIEW === "route"){
    const held = [PALETTE, TYPEFACE].filter(Boolean);
    $("#meta").textContent = `${TOTAL.toLocaleString()} layout${TOTAL===1?"":"s"}`
                           + (held.length ? ` · holding ${held.join(" · ")}` : "");
    $("#nav").hidden = PAGES <= 1;
    $("#pageMeta").textContent =
      PAGES > 1 ? `page ${PAGE_INDEX + 1} of ${PAGES.toLocaleString()}` : "";
    $("#first").disabled = PAGE_INDEX === 0;   // already home
  } else {
    $("#meta").textContent = `${OPTIONS.length} of ${TOTAL.toLocaleString()} possible layouts`;
  }
  const grid = $("#grid");
  grid.innerHTML = "";
  OPTIONS.forEach((v, i) => {
    const name = pin(v.name);
    // The palette/typeface chips reflect a forced value, since that is what shows.
    const axes = { ...v.axes };
    if(PALETTE)  axes.palette  = PALETTE;
    if(TYPEFACE) axes.typeface = TYPEFACE;
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="shot"><iframe loading="lazy" src="${previewUrl(name)}"
           title="${name}" scrolling="no"></iframe><div class="veil"></div></div>
      <div class="info">
        <div class="chips">${Object.values(axes)
          .map(val => `<span class="chip">${val}</span>`).join("")}</div>
        <div class="acts">
          <button class="o">Open</button>
          <button class="c">Copy Name</button>
        </div>
      </div>`;
    const frame = card.querySelector("iframe");
    frame.addEventListener("load", ()=>fitShot(frame));
    new ResizeObserver(()=>fitShot(frame)).observe(card.querySelector(".shot"));
    card.querySelector(".shot").onclick = ()=>{ cursor=i; open(v); };
    card.querySelector(".o").onclick = ()=>{ cursor=i; open(v); };
    card.querySelector(".c").onclick = ()=>copy(name);
    grid.appendChild(card);
  });
}

function paletteBar(el){
  if(!CAN_PIN){ el.hidden = true; return; }
  el.innerHTML = `<span class="lbl">Colour</span>` +
    `<button class="sw-varied${PALETTE?"":" on"}" data-p="">Varied</button>` +
    PALETTES.map(p =>
      `<button class="sw${PALETTE===p.name?" on":""}" data-p="${p.name}"
               style="background:${p.accent}" title="${p.name}"></button>`).join("");
  el.querySelectorAll("[data-p]").forEach(b => b.onclick = ()=>{
    PALETTE = b.dataset.p || null;
    onPin();
  });
}

// The typeface counterpart of the colour bar: same "hold one constant" idea on the
// second name segment, but each chip is a sample rendered in its own face (a font
// can't be a swatch), so you pick by how the letters look.
function typefaceBar(el){
  if(!CAN_PIN){ el.hidden = true; return; }
  el.innerHTML = `<span class="lbl">Type</span>` +
    `<button class="tf${TYPEFACE?"":" on"}" data-t="">Varied</button>` +
    TYPEFACES.map(t =>
      `<button class="tf${TYPEFACE===t.name?" on":""}" data-t="${t.name}"
               style="font-family:${t.font.replace(/"/g,"&quot;")}" title="${t.name}">${t.name}</button>`).join("");
  el.querySelectorAll("[data-t]").forEach(b => b.onclick = ()=>{
    TYPEFACE = b.dataset.t || null;
    onPin();
  });
}

// The description is "palette · typeface · header header · …"; reflect any held
// axis so the dialog subtitle matches the render on screen.
function pinnedDesc(v){
  if(!PALETTE && !TYPEFACE) return v.description;
  const parts = v.description.split(" · ");
  if(PALETTE)  parts[0] = PALETTE;
  if(TYPEFACE) parts[1] = TYPEFACE;
  return parts.join(" · ");
}

function open(v){
  CURRENT = v;
  const name = pin(v.name);
  $("#dlgName").textContent = name;
  $("#dlgDesc").textContent = pinnedDesc(v);
  $("#dlgFrame").src = previewUrl(name);
  $("#dlgCopy").onclick = ()=>copy(name);
  paletteBar($("#dlgPalette"));
  typefaceBar($("#dlgTypeface"));

  const post = (path, body) => fetch(path, {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify(body)
  }).then(r=>r.json()).catch(e=>({error:String(e)}));

  const act = async (button, label, busy, path, done) => {
    button.disabled = true; button.textContent = busy;
    const r = await post(path, { name });   // publish/export the recoloured spec
    button.disabled = false; button.textContent = label;
    toast(r.error ? (label + " failed: " + r.error) : done(r));
  };

  const ex = $("#dlgExport"), pub = $("#dlgPublish");
  ex.hidden = pub.hidden = !EXPORTABLE;
  if(EXPORTABLE){
    ex.onclick = ()=>act(ex, "Export PDF", "Exporting…", "/api/export",
                         r => "Exported " + r.path.split("/").pop());
    // The whole point of browsing: end on the deliverable, not on a name to
    // copy somewhere else.
    pub.onclick = ()=>act(pub, "★ Make this my resume", "Publishing…", "/api/publish",
                          r => "Published " + r.stem + ".pdf / .html / .md");
  }
  if(!$("#dlg").open){   // re-entrant when a swatch recolours an open dialog
    $("#dlg").showModal();
    document.body.classList.add("modal-open");
  }
}

// Held axes travel with every page request, so paging walks only the filtered
// subset and the server reports its true size.
function filterQuery(){
  const p = new URLSearchParams();
  if(PALETTE)  p.set("palette",  PALETTE);
  if(TYPEFACE) p.set("typeface", TYPEFACE);
  const q = p.toString();
  return q ? "&" + q : "";
}

async function goto(index){
  const nav = $("#nav"); nav.style.opacity = ".5";
  const r = await fetch("/api/page?i=" + index + filterQuery()).then(r=>r.json())
                  .catch(e=>({error:String(e)}));
  nav.style.opacity = "1";
  if(r.error){ toast("Could not load page: " + r.error); return; }
  OPTIONS = r.options; PAGE_INDEX = r.index; PAGES = r.pages; TOTAL = r.total; cursor = 0;
  render();
  scrollTo({ top: 0, behavior: "smooth" });
}

// Holding or releasing an axis re-queries from the top of the now-filtered set,
// so the layouts, the page count and the total all move together (RP-0033/0035).
function onPin(){
  goto(0);
  if($("#dlg").open && CURRENT) open(CURRENT);  // keep an open preview in sync
}

if(PAGES > 1){
  $("#first").onclick   = ()=>goto(0);
  $("#next").onclick    = ()=>goto(PAGE_INDEX + 1);
  $("#prev").onclick    = ()=>goto(PAGE_INDEX - 1 + PAGES);
  // Somewhere else in the space entirely, rather than the next twelve along.
  $("#shuffle").onclick = ()=>goto(Math.floor(Math.random() * PAGES));
}

$("#dlgClose").onclick = ()=>$("#dlg").close();
$("#dlg").addEventListener("close", ()=>document.body.classList.remove("modal-open"));

addEventListener("keydown", e => {
  if($("#dlg").open){ if(e.key==="Escape") $("#dlg").close(); return; }
  if(e.key==="ArrowRight"||e.key==="j"){ cursor=Math.min(cursor+1,OPTIONS.length-1); }
  else if(e.key==="ArrowLeft"||e.key==="k"){ cursor=Math.max(cursor-1,0); }
  else if(e.key==="Enter"&&OPTIONS[cursor]){ open(OPTIONS[cursor]); }
  else if(PAGES>1&&(e.key==="]"||e.key==="n")){ goto(PAGE_INDEX+1); }
  else if(PAGES>1&&(e.key==="["||e.key==="p")){ goto(PAGE_INDEX-1+PAGES); }
});

render();
</script>
</body></html>
"""
