"""Command line entry point.

    python -m resume_pipeline build   resume.json --theme all
    python -m resume_pipeline lint    resume.json --theme ats
    python -m resume_pipeline themes

The resume document is always an argument, never a hardcoded path — the tool
lives in `Code/`, the content lives wherever you keep it.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import compose, gallery, space
from . import lint as lint_mod
from . import markdown, model, pdf, themes


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
    resume = _load(args.resume)
    out_dir = Path(args.out or Path(args.resume).parent)
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

    # Comparing themes by opening four PDFs in turn is tedious, so when several
    # are built put them side by side on one page.
    if len(selected) > 1 and "pdf" in formats:
        target = out_dir / "index.html"
        target.write_text(_contact_sheet(selected, stem), encoding="utf-8")
        print(f"wrote {target}")
        target = out_dir / "gallery.html"
        target.write_text(gallery.render(selected, stem), encoding="utf-8")
        print(f"wrote {target}")
    return 0


def _contact_sheet(themes_, stem: str) -> str:
    cards = []
    for theme in themes_:
        badge = ("<span class='ok'>ATS-safe</span>" if theme.ats_safe
                 else "<span class='warn'>not ATS-safe</span>")
        pdf = f"{stem}.{theme.name}.pdf"
        cards.append(f"""
    <figure>
      <figcaption><b>{theme.name}</b> {badge}
        <span class='desc'>{theme.description}</span>
        <a href="{pdf}">open PDF</a>
      </figcaption>
      <iframe src="{pdf}#toolbar=0&navpanes=0&view=FitH" title="{theme.name}"></iframe>
    </figure>""")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Resume themes</title><style>
  body {{ font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         margin: 0; padding: 28px; background: #f6f7f9; color: #16181d; }}
  h1 {{ font-size: 20px; margin: 0 0 4px; }}
  p.sub {{ margin: 0 0 22px; color: #5b6577; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 22px; }}
  figure {{ margin: 0; background: #fff; border: 1px solid #dfe3e8; border-radius: 10px;
            overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.06); }}
  figcaption {{ padding: 11px 14px; border-bottom: 1px solid #eceef1; display: flex;
                align-items: center; gap: 9px; flex-wrap: wrap; }}
  .desc {{ color: #6b7280; font-size: 13px; flex: 1; }}
  .ok, .warn {{ font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 20px; }}
  .ok {{ background: #e3f5ea; color: #1a7f42; }}
  .warn {{ background: #fdecec; color: #b3261e; }}
  a {{ color: #0b6fa4; font-size: 13px; text-decoration: none; }}
  iframe {{ width: 100%; height: 660px; border: 0; display: block; background: #fff; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #14161a; color: #e6e8ec; }}
    figure {{ background: #1c1f25; border-color: #2b3038; }}
    figcaption {{ border-color: #2b3038; }}
  }}
</style></head><body>
  <h1>Resume themes</h1>
  <p class="sub">Same data, {len(themes_)} layouts. Generated from resume.json.</p>
  <div class="grid">{''.join(cards)}
  </div>
</body></html>
"""


def cmd_lint(args) -> int:
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


def cmd_explore(args) -> int:
    resume = _load(args.resume)
    out_dir = Path(args.out or (Path(args.resume).parent / "explore"))
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = compose.sample(args.count, seed=args.seed)
    total = len(compose.all_specs())
    print(f"sampling {len(specs)} of {total:,} possible layouts (seed {args.seed})")

    built = []
    for n, spec in enumerate(specs, 1):
        theme = compose.as_theme(spec)
        html = theme.render(resume)
        (out_dir / f"{args.name}.{spec.name}.html").write_text(html, encoding="utf-8")
        try:
            pdf.write(html, out_dir / f"{args.name}.{spec.name}.pdf")
        except (pdf.BrowserNotFound, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        built.append(theme)
        print(f"  [{n}/{len(specs)}] {spec.name}")

    target = out_dir / "gallery.html"
    target.write_text(gallery.render(built, args.name), encoding="utf-8")
    print(f"\nwrote {target}")
    return 0


def cmd_serve(args) -> int:
    from .explore import serve
    resume_path = Path(args.resume)
    serve(
        resume_path,
        out_dir=Path(args.out) if args.out else resume_path.parent / "out",
        stem=args.name or resume_path.stem,
        batch_size=args.batch,
        port=args.port,
        open_browser=not args.no_open,
    )
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
    p.add_argument("resume", help="path to a JSON Resume document")
    p.add_argument("--theme", default="ats",
                   help="theme name, or 'all' (default: ats)")
    p.add_argument("--formats", default="html,pdf",
                   help="comma-separated: html,pdf,md (default: html,pdf)")
    p.add_argument("--out", help="output directory (default: alongside input)")
    p.add_argument("--name", help="output basename (default: input stem)")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("lint", help="check against ATS best practices")
    p.add_argument("resume")
    p.add_argument("--theme", default="ats",
                   help="theme to judge layout against, or 'none'")
    p.add_argument("--strict", action="store_true",
                   help="treat warnings as failures")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("explore", help="generate many layout variants to flip through")
    p.add_argument("resume")
    p.add_argument("--count", type=int, default=24,
                   help="how many variants to generate (default: 24)")
    p.add_argument("--seed", type=int, default=0,
                   help="sampling seed - same seed gives the same catalogue")
    p.add_argument("--out", help="output directory (default: <resume dir>/explore)")
    p.add_argument("--name", default="v", help="output basename (default: v)")
    p.set_defaults(func=cmd_explore)

    p = sub.add_parser("serve", help="open the interactive layout explorer")
    p.add_argument("resume")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--batch", type=int, default=12,
                   help="layouts shown per batch (default: 12)")
    p.add_argument("--out", help="export directory (default: <resume dir>/out)")
    p.add_argument("--name", help="export basename (default: input stem)")
    p.add_argument("--no-open", action="store_true", help="do not open a browser")
    p.set_defaults(func=cmd_serve)

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
