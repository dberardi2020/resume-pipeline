"""A local server for exploring the layout space.

Previews are HTML, rendered on request. The earlier version pre-baked a PDF per
variant by launching Chrome once each — about a second apiece, which put a hard
ceiling on how many options were worth generating. Rendering HTML is
sub-millisecond, so the ceiling disappears and PDF becomes an export step for the
one layout you actually chose.

State lives in a JSON file next to the resume, not in `localStorage`: it survives a
browser profile, it is diffable, and the CLI can read it. Marking a layout is the
input to `space.steer`, so the next batch is a response to the last one.

Stdlib only — `http.server` is unglamorous but this binds to loopback for one user.
"""
from __future__ import annotations

import json
import webbrowser
from dataclasses import asdict
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .. import compose, model, pdf, space
from .ui import PAGE


class Session:
    """Verdicts on layouts, persisted beside the resume."""

    def __init__(self, path: Path):
        self.path = path
        self.favourites: list[str] = []
        self.rejects: list[str] = []
        self.batch: list[str] = []
        self.seed = 0
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            return  # A corrupt session should never block the tool from starting.
        self.favourites = data.get("favourites", [])
        self.rejects = data.get("rejects", [])
        self.batch = data.get("batch", [])
        self.seed = data.get("seed", 0)

    def save(self) -> None:
        self.path.write_text(json.dumps({
            "favourites": self.favourites,
            "rejects": self.rejects,
            "batch": self.batch,
            "seed": self.seed,
        }, indent=2) + "\n", encoding="utf-8")

    def mark(self, name: str, verdict: str) -> None:
        for bucket in (self.favourites, self.rejects):
            if name in bucket:
                bucket.remove(name)
        if verdict == "favourite":
            self.favourites.append(name)
        elif verdict == "reject":
            self.rejects.append(name)
        self.save()

    def specs(self, names: list[str]) -> list[compose.Spec]:
        return [s for s in (space.parse(n) for n in names) if s]


def _describe(spec: compose.Spec) -> dict:
    d = asdict(spec)
    return {
        "name": spec.name,
        "description": spec.description,
        "axes": {
            "palette": compose.PALETTES[spec.palette][0],
            "typeface": compose.TYPEFACES[spec.typeface][0],
            "header": spec.header,
            "skills": spec.skills,
            "promo": spec.promo,
            "density": compose.DENSITIES[spec.density][0],
        },
        "raw": d,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "resume-pipeline"

    def __init__(self, *args, ctx=None, **kwargs):
        self.ctx = ctx
        super().__init__(*args, **kwargs)

    # Quiet by default; a request log per preview is noise during browsing.
    def log_message(self, fmt, *args):
        pass

    # -- helpers --
    def _send(self, body: bytes, ctype: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status: int = 200) -> None:
        self._send(json.dumps(payload).encode(), "application/json", status)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return {}

    # -- routes --
    def do_GET(self):
        route = urlparse(self.path).path
        ctx = self.ctx

        if route == "/":
            return self._send(PAGE.encode(), "text/html; charset=utf-8")

        if route == "/api/state":
            session = ctx["session"]
            if not session.batch:
                batch = space.diverse(ctx["batch_size"], seed=session.seed)
                session.batch = [s.name for s in batch]
                session.save()
            return self._json({
                "batch": [_describe(s) for s in session.specs(session.batch)],
                "favourites": session.favourites,
                "rejects": session.rejects,
                "total": space.TOTAL,
                "seen": len(set(session.favourites) | set(session.rejects)),
                "resume": str(ctx["resume_path"].name),
            })

        if route.startswith("/preview/"):
            name = unquote(route[len("/preview/"):])
            spec = space.parse(name)
            if not spec:
                return self._send(b"unknown layout", "text/plain", 404)
            html = compose.render(ctx["resume"], spec)
            return self._send(html.encode(), "text/html; charset=utf-8")

        return self._send(b"not found", "text/plain", 404)

    def do_POST(self):
        route = urlparse(self.path).path
        ctx = self.ctx
        session = ctx["session"]
        payload = self._body()

        if route == "/api/mark":
            name, verdict = payload.get("name"), payload.get("verdict")
            if not name:
                return self._json({"error": "name required"}, 400)
            session.mark(name, verdict)
            return self._json({"ok": True, "favourites": session.favourites,
                               "rejects": session.rejects})

        if route == "/api/next":
            session.seed += 1
            batch = space.steer(
                session.specs(session.favourites),
                session.specs(session.rejects),
                ctx["batch_size"], seed=session.seed,
                exclude=set(session.batch),
            )
            session.batch = [s.name for s in batch]
            session.save()
            return self._json({"batch": [_describe(s) for s in batch]})

        if route == "/api/reset":
            session.favourites, session.rejects, session.batch = [], [], []
            session.seed = 0
            session.save()
            return self._json({"ok": True})

        if route == "/api/export":
            name = payload.get("name")
            spec = space.parse(name or "")
            if not spec:
                return self._json({"error": "unknown layout"}, 400)
            out_dir = ctx["out_dir"]
            out_dir.mkdir(parents=True, exist_ok=True)
            target = out_dir / f"{ctx['stem']}.{spec.name}.pdf"
            try:
                pdf.write(compose.render(ctx["resume"], spec), target)
            except (pdf.BrowserNotFound, RuntimeError) as exc:
                return self._json({"error": str(exc)}, 500)
            (out_dir / f"{ctx['stem']}.{spec.name}.html").write_text(
                compose.render(ctx["resume"], spec), encoding="utf-8")
            return self._json({"ok": True, "path": str(target)})

        return self._json({"error": "not found"}, 404)


def serve(resume_path: Path, out_dir: Path, stem: str, batch_size: int = 12,
          port: int = 8765, open_browser: bool = True) -> None:
    resume = model.load(resume_path)
    ctx = {
        "resume": resume,
        "resume_path": resume_path,
        "out_dir": out_dir,
        "stem": stem,
        "batch_size": batch_size,
        "session": Session(resume_path.parent / ".explore-session.json"),
    }
    httpd = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, ctx=ctx))
    url = f"http://127.0.0.1:{port}/"
    print(f"explorer running at {url}")
    print(f"  {space.TOTAL:,} layouts · session: {ctx['session'].path}")
    print("  ctrl-c to stop")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
