"""A local server for browsing the layout space.

The same viewer as the static catalogue, with two things a file on disk cannot do:
previews are rendered on request rather than written out ahead of time, and a layout
can be exported to PDF without leaving the page.

Rendering HTML is sub-millisecond, so there is no ceiling on how many layouts are
worth looking at — PDF is an export step for the one you chose, not a precondition
for looking at any of them.

There is deliberately no session: no favourites, no verdicts, no persisted batch.
The space is enumerable, so the page shows a spread of it and the axes are the
facets. Nothing needs remembering between requests, which is also what keeps this
honest about a hosted future — the server holds no per-user state.

Stdlib only — `http.server` is unglamorous, but this binds to loopback for one user.
"""
from __future__ import annotations

import json
import webbrowser
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import compose, deliverable, model, pdf, space, viewer


class Handler(BaseHTTPRequestHandler):
    server_version = "resume-pipeline"

    def __init__(self, *args, ctx=None, **kwargs):
        self.ctx = ctx
        super().__init__(*args, **kwargs)

    # Quiet by default; a request log per preview is noise while browsing.
    def log_message(self, fmt, *args):
        pass

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

    def do_GET(self):
        route = urlparse(self.path).path
        ctx = self.ctx

        if route == "/":
            page = viewer.page(ctx["specs"], ctx["resume"],
                               preview="route", exportable=True)
            return self._send(page.encode(), "text/html; charset=utf-8")

        if route.startswith("/preview/"):
            spec = space.parse(unquote(route[len("/preview/"):]))
            if not spec:
                return self._send(b"unknown layout", "text/plain", 404)
            return self._send(compose.render(ctx["resume"], spec).encode(),
                              "text/html; charset=utf-8")

        return self._send(b"not found", "text/plain", 404)

    def do_POST(self):
        route = urlparse(self.path).path
        ctx = self.ctx

        if route == "/api/publish":
            # Browsing has to be able to end in the deliverable. Otherwise the
            # last step is copying a name out of the page and pasting it into a
            # command, which is the half-finished handoff this replaces.
            spec = space.parse(self._body().get("name") or "")
            if not spec:
                return self._json({"error": "unknown layout"}, 400)
            try:
                stem = deliverable.write(ctx["resume"], spec,
                                         ctx["publish_dir"], ctx["publish_stem"])
            except (pdf.BrowserNotFound, RuntimeError) as exc:
                return self._json({"error": str(exc)}, 500)
            return self._json({"ok": True, "stem": stem,
                               "dir": str(ctx["publish_dir"])})

        if route == "/api/export":
            spec = space.parse(self._body().get("name") or "")
            if not spec:
                return self._json({"error": "unknown layout"}, 400)
            out_dir = ctx["out_dir"]
            out_dir.mkdir(parents=True, exist_ok=True)
            html = compose.render(ctx["resume"], spec)
            target = out_dir / f"{ctx['stem']}.{spec.name}.pdf"
            try:
                pdf.write(html, target)
            except (pdf.BrowserNotFound, RuntimeError) as exc:
                return self._json({"error": str(exc)}, 500)
            (out_dir / f"{ctx['stem']}.{spec.name}.html").write_text(
                html, encoding="utf-8")
            return self._json({"ok": True, "path": str(target)})

        return self._json({"error": "not found"}, 404)


def serve(resume_path: Path, out_dir: Path, stem: str, count: int = 24,
          port: int = 8765, open_browser: bool = True,
          publish_stem: str | None = None) -> None:
    resume = model.load(resume_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx = {
        "resume": resume,
        "out_dir": out_dir,            # scratch exports — the cache
        "stem": stem,
        # Publishing writes beside the profile, never into the cache: that is
        # the whole distinction between an export and the deliverable.
        "publish_dir": Path(resume_path).parent,
        "publish_stem": publish_stem or deliverable.default_stem(resume),
        "specs": space.spread(count),
    }
    httpd = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, ctx=ctx))
    url = f"http://127.0.0.1:{port}/"
    print(f"layout viewer running at {url}")
    print(f"  showing {len(ctx['specs'])} of {space.TOTAL:,} layouts")
    print("  ctrl-c to stop")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
