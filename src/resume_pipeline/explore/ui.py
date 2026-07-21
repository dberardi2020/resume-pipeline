"""The explorer's front end, as a single self-contained page.

Two decisions drive the design.

**Show many at once.** Judging a layout takes under a second, but only if you can
see it. One-at-a-time paging spends more time on navigation than on looking, so the
default view is a grid of live, scaled previews — twelve real renders on screen,
each a true iframe rather than a screenshot, so nothing can drift from what exports.

**Make the verdict the primary action.** Favourite and reject are not bookkeeping;
they are the input to the next batch. So they sit on every card, are bound to single
keys, and the batch button states plainly what it will do with them.
"""
from __future__ import annotations

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Layout explorer</title>
<style>
  :root{
    --bg:#f2f4f7; --card:#fff; --ink:#12151a; --muted:#69707c; --line:#e0e4ea;
    --accent:#0b6fa4; --fav:#1a7f42; --fav-bg:#e6f6ec; --rej:#b3261e; --rej-bg:#fdeceb;
    --shadow:0 1px 2px rgba(16,24,40,.06),0 4px 12px rgba(16,24,40,.06);
  }
  @media (prefers-color-scheme:dark){
    :root{ --bg:#0e1014; --card:#181b21; --ink:#e8eaef; --muted:#98a0ad; --line:#282d36;
           --accent:#63b3e0; --fav:#5fd08b; --fav-bg:#12301e; --rej:#ff8f88; --rej-bg:#37130f;
           --shadow:0 1px 2px rgba(0,0,0,.4),0 6px 18px rgba(0,0,0,.35); }
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{background:var(--bg);color:var(--ink);
       font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif}

  header{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:16px;
         padding:12px 20px;background:var(--card);border-bottom:1px solid var(--line);
         flex-wrap:wrap}
  h1{font-size:15px;margin:0;letter-spacing:-.2px;font-weight:700}
  .meta{color:var(--muted);font-size:12.5px}
  .grow{flex:1}
  button{font:inherit;font-size:13px;color:var(--ink);background:var(--card);
         border:1px solid var(--line);border-radius:8px;padding:7px 13px;cursor:pointer;
         transition:border-color .12s,background .12s}
  button:hover{border-color:var(--accent)}
  button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
  button.primary:hover{filter:brightness(1.08)}
  button.ghost{border-color:transparent;color:var(--muted)}
  kbd{font:11.5px ui-monospace,Menlo,monospace;background:var(--bg);border:1px solid var(--line);
      border-bottom-width:2px;border-radius:5px;padding:1px 5px;color:var(--muted)}

  .grid{display:grid;gap:18px;padding:20px;
        grid-template-columns:repeat(auto-fill,minmax(270px,1fr))}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;
        overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column;
        transition:border-color .12s,transform .12s}
  .card:hover{transform:translateY(-2px)}
  .card.fav{border-color:var(--fav)}
  .card.rej{opacity:.42}
  .card.sel{outline:2px solid var(--accent);outline-offset:-2px}

  /* A real 8.5in-wide render, scaled down. Not a screenshot — what you see is
     exactly what exports. */
  .shot{position:relative;height:330px;overflow:hidden;background:#fff;cursor:pointer;
        border-bottom:1px solid var(--line)}
  .shot iframe{position:absolute;top:0;left:0;width:816px;height:1056px;border:0;
               transform-origin:top left;pointer-events:none}
  .shot .veil{position:absolute;inset:0}

  .info{padding:9px 11px;display:flex;flex-direction:column;gap:7px}
  .nm{font-size:12.5px;font-weight:700;letter-spacing:-.1px}
  .chips{display:flex;flex-wrap:wrap;gap:4px}
  .chip{font-size:10.5px;background:var(--bg);border:1px solid var(--line);
        border-radius:20px;padding:1px 7px;color:var(--muted)}
  .acts{display:flex;gap:6px}
  .acts button{flex:1;padding:5px 0;font-size:12px}
  .acts .f.on{background:var(--fav-bg);border-color:var(--fav);color:var(--fav);font-weight:700}
  .acts .r.on{background:var(--rej-bg);border-color:var(--rej);color:var(--rej);font-weight:700}

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
  .empty{padding:60px 20px;text-align:center;color:var(--muted)}
</style></head><body>

<header>
  <h1>Layout explorer</h1>
  <span class="meta" id="meta"></span>
  <span class="grow"></span>
  <span class="meta"><kbd>F</kbd> keep <kbd>X</kbd> pass <kbd>↵</kbd> open <kbd>N</kbd> next</span>
  <button id="reset" class="ghost">Reset</button>
  <button id="next" class="primary">Next batch</button>
</header>

<div class="grid" id="grid"></div>

<dialog id="dlg">
  <div class="dlg-bar">
    <b id="dlgName"></b>
    <span class="meta" id="dlgDesc"></span>
    <span class="grow"></span>
    <button id="dlgFav"></button>
    <button id="dlgExport" class="primary">Export PDF</button>
    <button id="dlgClose" class="ghost">Close</button>
  </div>
  <iframe id="dlgFrame" title="preview"></iframe>
</dialog>

<div class="toast" id="toast"></div>

<script>
let state = { batch: [], favourites: [], rejects: [], total: 0, seen: 0 };
let cursor = 0;

const $ = s => document.querySelector(s);
const api = (p, body) => fetch(p, body
  ? { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) }
  : undefined).then(r => r.json());

let toastTimer;
function toast(msg){
  const t = $("#toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(()=>t.classList.remove("show"), 1900);
}

function fitShot(frame){
  // Scale the 816px-wide render to whatever the card ended up being.
  const w = frame.parentElement.clientWidth;
  frame.style.transform = `scale(${w/816})`;
}

function render(){
  $("#meta").textContent =
    `${state.batch.length} shown · ${state.favourites.length} kept · ` +
    `${state.seen} judged of ${state.total.toLocaleString()}`;

  const grid = $("#grid");
  if(!state.batch.length){
    grid.innerHTML = `<div class="empty">No layouts in this batch. Hit <b>Next batch</b>.</div>`;
    return;
  }
  grid.innerHTML = "";
  state.batch.forEach((v, i) => {
    const fav = state.favourites.includes(v.name);
    const rej = state.rejects.includes(v.name);
    const card = document.createElement("div");
    card.className = "card" + (fav?" fav":"") + (rej?" rej":"") + (i===cursor?" sel":"");
    card.innerHTML = `
      <div class="shot"><iframe loading="lazy" src="/preview/${encodeURIComponent(v.name)}"
           title="${v.name}"></iframe><div class="veil"></div></div>
      <div class="info">
        <div class="nm">${v.name}</div>
        <div class="chips">${Object.entries(v.axes)
          .map(([k,val]) => `<span class="chip">${val}</span>`).join("")}</div>
        <div class="acts">
          <button class="f${fav?" on":""}">${fav?"★ Kept":"☆ Keep"}</button>
          <button class="r${rej?" on":""}">${rej?"✕ Passed":"✕ Pass"}</button>
        </div>
      </div>`;
    const frame = card.querySelector("iframe");
    frame.addEventListener("load", ()=>fitShot(frame));
    new ResizeObserver(()=>fitShot(frame)).observe(card.querySelector(".shot"));
    card.querySelector(".shot").onclick = ()=>{ cursor=i; open(v); };
    card.querySelector(".f").onclick = e=>{ e.stopPropagation(); mark(v, fav?"clear":"favourite"); };
    card.querySelector(".r").onclick = e=>{ e.stopPropagation(); mark(v, rej?"clear":"reject"); };
    grid.appendChild(card);
  });
}

async function mark(v, verdict){
  const r = await api("/api/mark", { name:v.name, verdict });
  state.favourites = r.favourites; state.rejects = r.rejects;
  state.seen = new Set([...r.favourites, ...r.rejects]).size;
  render();
}

function open(v){
  $("#dlgName").textContent = v.name;
  $("#dlgDesc").textContent = v.description;
  $("#dlgFrame").src = "/preview/" + encodeURIComponent(v.name);
  const fav = state.favourites.includes(v.name);
  $("#dlgFav").textContent = fav ? "★ Kept" : "☆ Keep";
  $("#dlgFav").onclick = async ()=>{ await mark(v, fav?"clear":"favourite"); open(v); };
  $("#dlgExport").onclick = async ()=>{
    $("#dlgExport").disabled = true; $("#dlgExport").textContent = "Exporting…";
    const r = await api("/api/export", { name:v.name });
    $("#dlgExport").disabled = false; $("#dlgExport").textContent = "Export PDF";
    toast(r.error ? ("Export failed: " + r.error) : ("Exported " + r.path.split("/").pop()));
  };
  $("#dlg").showModal();
}

async function load(){ state = await api("/api/state"); cursor = 0; render(); }
async function nextBatch(){
  $("#next").disabled = true; $("#next").textContent = "Sampling…";
  const r = await api("/api/next", {});
  state.batch = r.batch; cursor = 0;
  $("#next").disabled = false;
  $("#next").textContent = state.favourites.length ? "More like these" : "Next batch";
  render();
  toast(state.favourites.length
    ? "Sampled near your keeps" : "Fresh spread across the space");
}

$("#next").onclick = nextBatch;
$("#reset").onclick = async ()=>{ await api("/api/reset", {}); await load(); toast("Session cleared"); };
$("#dlgClose").onclick = ()=>$("#dlg").close();

addEventListener("keydown", e => {
  if($("#dlg").open){ if(e.key==="Escape") $("#dlg").close(); return; }
  const v = state.batch[cursor];
  if(e.key==="ArrowRight"||e.key==="j"){ cursor=Math.min(cursor+1,state.batch.length-1); render(); }
  else if(e.key==="ArrowLeft"||e.key==="k"){ cursor=Math.max(cursor-1,0); render(); }
  else if(e.key.toLowerCase()==="f" && v){ mark(v, state.favourites.includes(v.name)?"clear":"favourite"); }
  else if(e.key.toLowerCase()==="x" && v){ mark(v, state.rejects.includes(v.name)?"clear":"reject"); }
  else if(e.key==="Enter" && v){ open(v); }
  else if(e.key.toLowerCase()==="n"){ nextBatch(); }
});

load();
</script>
</body></html>
"""
