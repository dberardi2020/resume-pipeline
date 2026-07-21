"""Command line entry point.

    python -m resume_pipeline build   resume.json --theme all
    python -m resume_pipeline lint    resume.json --theme ats
    python -m resume_pipeline themes

The resume document is always an argument, never a hardcoded path — the tool
lives in `Code/`, the content lives wherever you keep it.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import catalogue, compose, scaffold, space
from . import lint as lint_mod
from . import markdown, model, pdf, themes


def find_resume(explicit: str | None) -> Path:
    """Locate the resume document.

    Typing a path every time is friction on the most common action, so the path
    is optional: an explicit argument wins, then `RESUME_PIPELINE_RESUME`, then
    the nearest `resume.json` walking up from the working directory. That last
    rule means `resume-pipeline serve` just works anywhere inside a resume folder.
    """
    if explicit:
        return Path(explicit).expanduser()
    if env := os.environ.get("RESUME_PIPELINE_RESUME"):
        return Path(env).expanduser()
    here = Path.cwd().resolve()
    for folder in (here, *here.parents):
        for candidate in ("resume.json", "Resume/resume.json"):
            found = folder / candidate
            if found.is_file():
                return found
    raise SystemExit(
        "error: no resume found. Pass a path, set RESUME_PIPELINE_RESUME, or run "
        "from a folder containing resume.json."
    )


def cache_dir(resume_path: Path) -> Path:
    """Scratch renders go outside the resume folder, deliberately.

    Builds are cheap and disposable, but they pile up — every theme, every
    explored variant, in HTML and PDF. Writing them beside the resume buries the
    one authored file under hundreds of derived ones, and if that folder is
    synced (it usually is, resumes being personal), it churns megabytes of output
    that a single command reproduces. So the default is a cache, and putting a
    render somewhere permanent is an explicit act: see `publish`.
    """
    root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return root / "resume-pipeline" / resume_path.resolve().parent.name


def _resolve_themes(name: str):
    if name == "all":
        return list(themes.registry().values())
    return [themes.get(name)]


def _load(path: str):
    try:
        resume = model.load(path)
    except model.ResumeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    for note in resume.notes:
        print(f"note: {note}", file=sys.stderr)
    return resume


def cmd_build(args) -> int:
    args.resume = str(find_resume(args.resume))
    resume = _load(args.resume)
    out_dir = Path(args.out) if args.out else cache_dir(Path(args.resume))
    stem = args.name or Path(args.resume).stem
    formats = set(args.formats.split(","))

    if "md" in formats:
        target = out_dir / f"{stem}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown.render(resume), encoding="utf-8")
        print(f"wrote {target}")

    selected = _resolve_themes(args.theme)
    for theme in selected:
        html = theme.render(resume)
        # Single theme keeps the bare stem; multiple themes need disambiguating.
        suffix = "" if len(selected) == 1 else f".{theme.name}"
        if "html" in formats:
            target = out_dir / f"{stem}{suffix}.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding="utf-8")
            print(f"wrote {target}")
        if "pdf" in formats:
            target = out_dir / f"{stem}{suffix}.pdf"
            try:
                pdf.write(html, target)
            except (pdf.BrowserNotFound, RuntimeError) as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            print(f"wrote {target}")

        if not theme.ats_safe:
            print(f"note: theme {theme.name!r} is not ATS-safe — use 'ats' for "
                  f"anything submitted through a portal.", file=sys.stderr)

    return 0



def cmd_lint(args) -> int:
    args.resume = str(find_resume(args.resume))
    resume = _load(args.resume)
    theme = None if args.theme == "none" else themes.get(args.theme)
    findings = lint_mod.check(resume, theme=theme)

    if not findings:
        print("clean - no findings.")
        return 0
    for finding in findings:
        print(finding)

    errors = sum(1 for f in findings if f.level == lint_mod.ERROR)
    warnings = sum(1 for f in findings if f.level == lint_mod.WARNING)
    infos = len(findings) - errors - warnings
    print(f"\n{errors} error(s), {warnings} warning(s), {infos} info")
    # Only errors fail the command, so lint is usable in CI without forcing
    # every stylistic nit to be resolved.
    return 1 if (errors or (args.strict and warnings)) else 0


def cmd_catalogue(args) -> int:
    args.resume = str(find_resume(args.resume))
    resume = _load(args.resume)
    out_dir = (Path(args.out) if args.out
               else cache_dir(Path(args.resume)) / "catalogue")
    index, specs = catalogue.build(resume, args.count, out_dir, seed=args.seed)
    print(f"built {len(specs)} layouts of {space.TOTAL:,}")
    for n, spec in enumerate(specs, 1):
        print(f"  {n:>2}. {spec.name:<34} {spec.description}")
    print(f"\nopen: file://{index}")
    print("publish one with: resume-pipeline publish --theme <name>")
    return 0


def cmd_serve(args) -> int:
    from .explore import serve
    resume_path = find_resume(args.resume)
    serve(
        resume_path,
        out_dir=Path(args.out) if args.out else cache_dir(resume_path),
        stem=args.name or resume_path.stem,
        batch_size=args.batch,
        port=args.port,
        open_browser=not args.no_open,
    )
    return 0


def cmd_publish(args) -> int:
    """Write the chosen layout beside the resume as *the* deliverable.

    A resume folder should answer one question instantly: which file do I send?
    So publish writes a single fixed set of names, overwriting in place, rather
    than accumulating theme-suffixed variants.
    """
    args.resume = str(find_resume(args.resume))
    resume = _load(args.resume)
    theme = themes.get(args.theme)
    out_dir = Path(args.resume).parent
    stem = args.name or f"{resume.name.split()[-1]}_Resume".replace(" ", "_")

    html = theme.render(resume)
    (out_dir / f"{stem}.html").write_text(html, encoding="utf-8")
    (out_dir / f"{stem}.md").write_text(markdown.render(resume), encoding="utf-8")
    try:
        pdf.write(html, out_dir / f"{stem}.pdf")
    except (pdf.BrowserNotFound, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"published {stem}.pdf / .html / .md to {out_dir}  (theme: {theme.name})")
    if not theme.ats_safe:
        print(f"note: {theme.name!r} is not ATS-safe - do not submit it through a portal.",
              file=sys.stderr)
    return 0


def cmd_init(args) -> int:
    root = Path(args.directory or ".").expanduser().resolve()
    print(f"scaffolding career workspace in {root}")
    for line in scaffold.init(root, skill_only=args.skill_only):
        print(line)
    if not args.skill_only:
        print("\nnext: edit Resume/resume.json, then `cd Resume && resume-pipeline lint`")
    return 0


def cmd_themes(args) -> int:
    for name, theme in sorted(themes.registry().items()):
        flag = "ATS-safe" if theme.ats_safe else "not ATS-safe"
        print(f"{name:<10} {theme.description}  ({flag}, {theme.columns}-col)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-pipeline",
        description="Render a JSON Resume to HTML, PDF and Markdown.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("build", help="render a resume")
    p.add_argument("resume", nargs="?", help="path to a JSON Resume document (default: nearest resume.json)")
    p.add_argument("--theme", default="ats",
                   help="theme name, or 'all' (default: ats)")
    p.add_argument("--formats", default="html,pdf",
                   help="comma-separated: html,pdf,md (default: html,pdf)")
    p.add_argument("--out", help="output directory (default: alongside input)")
    p.add_argument("--name", help="output basename (default: input stem)")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("lint", help="check against ATS best practices")
    p.add_argument("resume", nargs="?")
    p.add_argument("--theme", default="ats",
                   help="theme to judge layout against, or 'none'")
    p.add_argument("--strict", action="store_true",
                   help="treat warnings as failures")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("catalogue",
                       help="build a static, browsable page of layout options")
    p.add_argument("resume", nargs="?")
    p.add_argument("--count", type=int, default=20,
                   help="how many layouts to generate (default: 20)")
    p.add_argument("--seed", type=int, default=0,
                   help="sampling seed - the same seed gives the same catalogue")
    p.add_argument("--out", help="output directory (default: cache)")
    p.set_defaults(func=cmd_catalogue)

    p = sub.add_parser("serve", help="open the interactive layout explorer")
    p.add_argument("resume", nargs="?")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--batch", type=int, default=12,
                   help="layouts shown per batch (default: 12)")
    p.add_argument("--out", help="export directory (default: <resume dir>/out)")
    p.add_argument("--name", help="export basename (default: input stem)")
    p.add_argument("--no-open", action="store_true", help="do not open a browser")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("publish",
                       help="write the deliverable beside the resume")
    p.add_argument("resume", nargs="?")
    p.add_argument("--theme", default="slate", help="theme to publish (default: slate)")
    p.add_argument("--name", help="output basename (default: <Lastname>_Resume)")
    p.set_defaults(func=cmd_publish)

    p = sub.add_parser("init", help="scaffold a career workspace")
    p.add_argument("directory", nargs="?", help="where to create it (default: here)")
    p.add_argument("--skill-only", action="store_true",
                   help="install just the Claude Code skill into an existing workspace")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("themes", help="list available themes")
    p.set_defaults(func=cmd_themes)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyError as exc:
        print(f"error: {exc.args[0]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
