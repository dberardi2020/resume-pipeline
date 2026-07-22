"""The command surface: locating the resume, resolving layouts, publishing."""
from __future__ import annotations

import json

import pytest

from resume_pipeline import cli, compose

COMMANDS = {"lint", "catalogue", "serve", "publish", "init"}


def test_the_command_surface_is_exactly_this(monkeypatch):
    """A guard on scope. Growing this set should be a decision, not a drift."""
    import argparse
    parser = cli.build_parser()
    action = next(a for a in parser._actions
                  if isinstance(a, argparse._SubParsersAction))
    assert set(action.choices) == COMMANDS


# ── find_resume ───────────────────────────────────────────────────────────────

def test_explicit_path_wins(tmp_path, monkeypatch):
    target = tmp_path / "elsewhere.json"
    target.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RESUME_PIPELINE_RESUME", str(tmp_path / "env.json"))
    assert cli.find_resume(str(target)) == target


def test_environment_variable_is_used(tmp_path, monkeypatch):
    target = tmp_path / "env.json"
    target.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("RESUME_PIPELINE_RESUME", str(target))
    assert cli.find_resume(None) == target


def test_it_walks_up_to_find_the_resume(tmp_path, monkeypatch):
    monkeypatch.delenv("RESUME_PIPELINE_RESUME", raising=False)
    (tmp_path / "Resume").mkdir()
    target = tmp_path / "Resume" / "resume.json"
    target.write_text("{}", encoding="utf-8")

    deep = tmp_path / "Resume" / "Archive" / "deep"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    assert cli.find_resume(None) == target


def test_no_resume_anywhere_exits(tmp_path, monkeypatch):
    monkeypatch.delenv("RESUME_PIPELINE_RESUME", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        cli.find_resume(None)


# ── resolve_layout ────────────────────────────────────────────────────────────

def test_presets_resolve():
    for name in compose.PRESETS:
        assert cli.resolve_layout(name).name


def test_generated_ids_resolve():
    """The generated half of the space must be publishable, not just viewable."""
    theme = cli.resolve_layout("moss-charter-rule-grid-stacked-compact")
    assert theme.name == "moss-charter-rule-grid-stacked-compact"


def test_an_unknown_layout_exits_with_help():
    with pytest.raises(SystemExit) as exc:
        cli.resolve_layout("harbor-321-mixed-compact")
    assert "unknown layout" in str(exc.value)
    assert "catalogue" in str(exc.value)


# ── cache_dir ─────────────────────────────────────────────────────────────────

def test_scratch_renders_stay_out_of_the_resume_folder(tmp_path):
    cache = cli.cache_dir(tmp_path / "Resume" / "resume.json")
    assert "resume-pipeline" in cache.parts
    assert tmp_path not in cache.parents


# ── publish ───────────────────────────────────────────────────────────────────

@pytest.fixture
def workspace(tmp_path, data):
    folder = tmp_path / "Resume"
    folder.mkdir()
    (folder / "resume.json").write_text(json.dumps(data), encoding="utf-8")
    return folder


def test_publish_writes_the_deliverable(workspace, monkeypatch):
    monkeypatch.setattr("resume_pipeline.pdf.write",
                        lambda html, path, **kw: path.write_bytes(b"%PDF-fake"))
    exit_code = cli.main(["publish", str(workspace / "resume.json"),
                          "--theme", "default", "--name", "Out"])
    assert exit_code == 0
    for suffix in (".html", ".md", ".pdf"):
        assert (workspace / f"Out{suffix}").exists()


def test_publish_overwrites_rather_than_accumulating(workspace, monkeypatch):
    monkeypatch.setattr("resume_pipeline.pdf.write",
                        lambda html, path, **kw: path.write_bytes(b"%PDF-fake"))
    for theme in ("default", "plain"):
        cli.main(["publish", str(workspace / "resume.json"),
                  "--theme", theme, "--name", "Out"])
    assert len(list(workspace.glob("Out*"))) == 3


def test_publish_reports_a_pdf_failure(workspace, monkeypatch):
    def boom(html, path, **kw):
        raise RuntimeError("no browser here")
    monkeypatch.setattr("resume_pipeline.pdf.write", boom)
    assert cli.main(["publish", str(workspace / "resume.json"),
                     "--theme", "default"]) == 1


def test_lint_exit_code_reflects_errors(workspace, capsys):
    assert cli.main(["lint", str(workspace / "resume.json")]) == 0

    broken = json.loads((workspace / "resume.json").read_text())
    broken["basics"].pop("email")
    (workspace / "resume.json").write_text(json.dumps(broken), encoding="utf-8")
    assert cli.main(["lint", str(workspace / "resume.json")]) == 1


def test_strict_lint_fails_on_warnings(workspace):
    payload = json.loads((workspace / "resume.json").read_text())
    payload["basics"].pop("phone")
    (workspace / "resume.json").write_text(json.dumps(payload), encoding="utf-8")

    assert cli.main(["lint", str(workspace / "resume.json")]) == 0
    assert cli.main(["lint", str(workspace / "resume.json"), "--strict"]) == 1
