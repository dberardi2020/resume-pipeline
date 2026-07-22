"""The two deliveries end to end: a folder you can open, and a server."""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer

import pytest

from resume_pipeline import catalogue, compose, server, space


# ── catalogue ─────────────────────────────────────────────────────────────────

def test_catalogue_writes_a_page_per_layout_plus_an_index(tmp_path, resume):
    index, specs = catalogue.build(resume, 5, tmp_path)

    assert index == tmp_path / "index.html"
    assert index.exists()
    assert len(specs) == 5
    for spec in specs:
        assert (tmp_path / f"{spec.name}.html").exists()


def test_catalogue_is_reproducible(tmp_path, resume):
    a, _ = catalogue.build(resume, 4, tmp_path / "a")
    b, _ = catalogue.build(resume, 4, tmp_path / "b")
    assert a.read_text() == b.read_text()


def test_catalogue_options_json_is_agent_readable(tmp_path, resume):
    """`use number 7` has to resolve without parsing HTML."""
    _, specs = catalogue.build(resume, 5, tmp_path)
    payload = json.loads((tmp_path / "options.json").read_text())

    assert [o["number"] for o in payload["options"]] == [1, 2, 3, 4, 5]
    assert [o["name"] for o in payload["options"]] == [s.name for s in specs]
    for option in payload["options"]:
        assert (tmp_path / option["preview"]).exists()
        assert space.parse(option["name"]) is not None


def test_catalogue_previews_are_the_real_render(tmp_path, resume):
    _, specs = catalogue.build(resume, 3, tmp_path)
    for spec in specs:
        written = (tmp_path / f"{spec.name}.html").read_text()
        assert written == compose.render(resume, spec)


# ── server ────────────────────────────────────────────────────────────────────

@pytest.fixture
def live(tmp_path, resume):
    ctx = {
        "resume": resume,
        "out_dir": tmp_path / "out",
        "stem": "Test",
        "specs": space.spread(4),
    }
    httpd = ThreadingHTTPServer(("127.0.0.1", 0),
                                partial(server.Handler, ctx=ctx))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}", ctx
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=5)


def get(url: str):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status, response.read().decode()


def test_root_serves_the_viewer(live):
    base, _ = live
    status, body = get(base + "/")
    assert status == 200
    assert body.startswith("<!doctype html>")
    assert 'const PREVIEW    = "route"' in body


def test_preview_renders_a_layout(live, resume):
    base, _ = live
    spec = space.spread(4)[0]
    status, body = get(f"{base}/preview/{spec.name}")
    assert status == 200
    assert body == compose.render(resume, spec)


def test_preview_of_an_unknown_layout_is_404(live):
    base, _ = live
    with pytest.raises(urllib.error.HTTPError) as exc:
        get(base + "/preview/harbor-321-mixed-compact")
    assert exc.value.code == 404


def test_unknown_route_is_404(live):
    base, _ = live
    with pytest.raises(urllib.error.HTTPError) as exc:
        get(base + "/nope")
    assert exc.value.code == 404


def test_the_server_keeps_no_session_state(live):
    """No favourites, no verdicts, no persisted batch — nothing to leak or sync."""
    base, ctx = live
    get(base + "/")
    get(base + "/")
    assert not any(p.name.endswith("session.json")
                   for p in ctx["out_dir"].glob("*") if p.is_file())
    assert set(ctx) == {"resume", "out_dir", "stem", "specs"}


def test_export_rejects_an_unknown_layout(live):
    base, _ = live
    request = urllib.request.Request(
        base + "/api/export", method="POST",
        data=json.dumps({"name": "not-a-layout"}).encode(),
        headers={"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(request, timeout=10)
    assert exc.value.code == 400
