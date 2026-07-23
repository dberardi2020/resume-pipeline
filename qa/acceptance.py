#!/usr/bin/env python3
"""Acceptance harness — end-to-end QA a dev or an agent can run on demand.

This is the *acceptance* layer, deliberately distinct from `tests/` (the unit
layer). It exercises the un-mockable integration surface the unit suite cannot,
because unit tests mock the browser and call `cli.main` in-process:

  - the command run as a subprocess, as a user runs it;
  - a **live HTTP server** (`serve`), driven over real requests;
  - **real PDF export through an actual browser**;
  - a **fresh `init` workspace**, from nothing.

It answers "does it actually work end to end on a real machine", which is exactly
where a fast, mocked unit suite is blind — this harness was written after an
acceptance run caught an archive-collision bug the unit tests missed.

Run:   python qa/acceptance.py
Exit:  non-zero if any check fails, so CI or an agent can gate on it.

Chrome-dependent checks SKIP cleanly when no Chromium-family browser is present,
so the harness runs anywhere; a full run needs one for the PDF leg.

See `qa/README.md` and `qa/product-map.md`. It is intended to grow (and split) as
the tool does; interaction-level checks of the viewer's JavaScript are handled by
an agent with browser control (the agentic layer), not by this harness.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "docs" / "assets" / "demo-profile.json"


class QA:
    def __init__(self) -> None:
        self.passed = self.failed = self.skipped = 0

    def ok(self, name: str, cond: bool, detail: str = "") -> None:
        if cond:
            self.passed += 1
            print(f"  PASS  {name}")
        else:
            self.failed += 1
            print(f"  FAIL  {name}   {detail}")

    def skip(self, name: str, why: str) -> None:
        self.skipped += 1
        print(f"  SKIP  {name}   ({why})")


def cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "resume_pipeline", *args],
                          cwd=cwd, capture_output=True, text=True)


def sidecar(folder: Path) -> dict:
    return json.loads((folder / ".resume-pipeline.json").read_text())


def snapshots(folder: Path) -> list[Path]:
    arc = folder / "Archive"
    return [p for p in arc.iterdir() if p.is_dir()] if arc.is_dir() else []


def have_browser() -> bool:
    from resume_pipeline import pdf
    try:
        return pdf.find_browser() is not None
    except Exception:
        return False


def check_init(qa: QA, tmp: Path) -> None:
    print("== init: a fresh workspace ==")
    ws = tmp / "fresh"
    cli("init", str(ws))
    for rel in ("CLAUDE.md", "README.md", ".claude/skills/career-resume-update/SKILL.md",
                ".claude/skills/career-layouts-browse/SKILL.md", "Resume/resume.json",
                "Resume/Archive", "Cover Letters", "Applications", "Reference"):
        qa.ok(f"init wrote {rel}", (ws / rel).exists())
    # the two skills must reference only real subcommands
    real = {"lint", "catalogue", "serve", "publish", "init"}
    import re
    for name in ("career-resume-update", "career-layouts-browse"):
        text = (ws / ".claude/skills" / name / "SKILL.md").read_text()
        cmds = set(re.findall(r"resume-pipeline\s+([a-z-]+)", text))
        qa.ok(f"{name} documents only real commands", cmds <= real, str(cmds - real))
    lint = cli("lint", str(ws / "Resume/resume.json"))
    qa.ok("starter resume lints without crashing", lint.returncode in (0, 1))


def check_publish(qa: QA, tmp: Path, browser: bool) -> None:
    print("== publish: layout/format memory, and the archive ==")
    ws = tmp / "pub"
    (ws).mkdir()
    (ws / "resume.json").write_text(FIXTURE.read_text())
    (ws / "Archive").mkdir()
    (ws / "Archive" / "20200101-precious.txt").write_text("keepsake")
    r = str(ws / "resume.json")

    cli("publish", r, "--theme", "editorial", "--formats", "html,md", "--name", "Res")
    qa.ok("first publish creates a sidecar", (ws / ".resume-pipeline.json").is_file())
    qa.ok("subset writes html+md, not pdf",
          (ws / "Res.html").exists() and (ws / "Res.md").exists() and not (ws / "Res.pdf").exists())
    qa.ok("first publish archives nothing", len(snapshots(ws)) == 0)
    layout = sidecar(ws)["layout"]

    out = cli("publish", r, "--name", "Res").stdout
    qa.ok("bare re-publish keeps layout & formats", "kept your last layout & formats" in out)
    qa.ok("layout is unchanged", sidecar(ws)["layout"] == layout)
    qa.ok("previous design is archived", len(snapshots(ws)) == 1)
    qa.ok("snapshot is self-describing", any((s / ".resume-pipeline.json").is_file() for s in snapshots(ws)))

    # three back-to-back publishes must not collide within the same second
    for theme in ("plain", "editorial", "default"):
        cli("publish", r, "--theme", theme, "--name", "Res")
    qa.ok("rapid publishes do not clobber snapshots", len(snapshots(ws)) == 4,
          f"{len(snapshots(ws))} snapshots")
    qa.ok("pre-existing archive file untouched",
          (ws / "Archive" / "20200101-precious.txt").read_text() == "keepsake")

    # content edit round-trips through the kept layout
    d = json.loads((ws / "resume.json").read_text())
    d["basics"]["label"] = "ACCEPTANCE EDIT MARKER"
    (ws / "resume.json").write_text(json.dumps(d))
    cli("publish", r, "--formats", "html", "--name", "Res")
    qa.ok("edited content appears in the re-render", "ACCEPTANCE EDIT MARKER" in (ws / "Res.html").read_text())

    if browser:
        cli("publish", r, "--formats", "pdf", "--name", "Res")
        pdf_bytes = (ws / "Res.pdf").read_bytes() if (ws / "Res.pdf").exists() else b""
        qa.ok("real PDF export produces a PDF", pdf_bytes[:4] == b"%PDF")
    else:
        qa.skip("real PDF export produces a PDF", "no browser")


def check_serve(qa: QA, tmp: Path, browser: bool, open_ui: bool = False) -> None:
    print("== serve: a live viewer over HTTP ==")
    ws = tmp / "serve"
    ws.mkdir()
    (ws / "resume.json").write_text(FIXTURE.read_text())
    port = 8791
    serve_cmd = [sys.executable, "-m", "resume_pipeline", "serve",
                 str(ws / "resume.json"), "--port", str(port)]
    if not open_ui:
        serve_cmd.append("--no-open")  # headless: driven over HTTP, no window
    proc = subprocess.Popen(serve_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    try:
        up = False
        for _ in range(50):
            try:
                urllib.request.urlopen(base + "/", timeout=1)
                up = True
                break
            except Exception:
                time.sleep(0.2)
        qa.ok("server comes up", up)
        if not up:
            return
        home = urllib.request.urlopen(base + "/", timeout=3).read().decode()
        qa.ok("home page renders the viewer", "palette" in home.lower() or "layout" in home.lower())
        page = json.loads(urllib.request.urlopen(base + "/api/page?i=1", timeout=3).read())
        qa.ok("/api/page returns options", bool(page.get("options")))
        full_total, full_pages = page["total"], page["pages"]
        # RP-0033/0035: holding an axis narrows the browse to that subset — the total
        # and page count must drop, and every returned layout must match the hold.
        held = json.loads(urllib.request.urlopen(
            base + "/api/page?i=0&palette=moss", timeout=3).read())
        narrowed = held["total"] < full_total and held["pages"] < full_pages
        all_moss = all(o["axes"]["palette"] == "moss" for o in held["options"])
        qa.ok("holding a palette narrows the browse (filter, not overlay)",
              narrowed and all_moss, f"total {full_total}->{held['total']}, all_moss={all_moss}")
        spec = page["options"][0]["name"]
        preview = urllib.request.urlopen(base + f"/preview/{spec}", timeout=3).read().decode()
        qa.ok("/preview renders a layout", "<html" in preview.lower())
        # The grid is empty in the served HTML — JavaScript builds it. Render the page
        # in a real (headless) browser and confirm the JS actually populated it. This is
        # the only check that exercises viewer.js; it uses the browser we already require.
        if browser:
            from resume_pipeline import compose, pdf
            dom = subprocess.run([pdf.find_browser(), "--headless", "--dump-dom", base + "/"],
                                 capture_output=True, text=True, timeout=30).stdout
            cards = dom.count('class="card')
            qa.ok("viewer JS builds the grid in a real browser", cards >= 1, f"{cards} cards")
            qa.ok("rendered grid carries the colour control", "Colour" in dom)
            # RP-0037: the type bar is the colour bar's twin — its label and every
            # face's sample chip must be built into the same rendered DOM.
            faces = [t[0] for t in compose.TYPEFACES]
            has_type = ">Type<" in dom and all(f">{f}<" in dom for f in faces)
            qa.ok("rendered grid carries the typeface control", has_type,
                  f"faces found: {[f for f in faces if f'>{f}<' in dom]}")
        else:
            qa.skip("viewer JS builds the grid in a real browser", "no browser")
        if browser:
            req = urllib.request.Request(
                base + "/api/publish", data=json.dumps({"name": spec}).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=60).read()
            from resume_pipeline import deliverable
            stem = deliverable.existing_stem(ws)
            qa.ok("/api/publish writes a complete deliverable", stem is not None)
            qa.ok("viewer publish records the same sidecar", (ws / ".resume-pipeline.json").is_file())
        else:
            qa.skip("/api/publish writes the deliverable", "no browser")
        if open_ui:
            print(f"\n  viewer live at {base}/ — the demo profile, in a real browser. "
                  "look around; press Enter to tear it down.")
            try:
                input()
            except EOFError:
                pass
    finally:
        proc.terminate()


def main() -> int:
    ap = argparse.ArgumentParser(description="resume-pipeline acceptance harness")
    ap.add_argument("--open", action="store_true",
                    help="open the live viewer in a real browser during the serve leg and "
                         "pause so you can watch it (default: headless over HTTP)")
    ap.add_argument("--keep", action="store_true",
                    help="keep the temp workspace and print its path, to inspect the "
                         "generated PDFs / HTML / archive afterwards")
    args = ap.parse_args()

    browser = have_browser()
    print(f"acceptance harness — browser {'present' if browser else 'ABSENT (PDF legs skip)'}\n")
    qa = QA()
    tmp = Path(tempfile.mkdtemp(prefix="rp-acceptance-"))
    try:
        check_init(qa, tmp)
        check_publish(qa, tmp, browser)
        check_serve(qa, tmp, browser, open_ui=args.open)
    finally:
        if args.keep:
            print(f"\n  workspace kept at: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n== {qa.passed} passed, {qa.failed} failed, {qa.skipped} skipped ==")
    return 1 if qa.failed else 0


if __name__ == "__main__":
    sys.exit(main())
