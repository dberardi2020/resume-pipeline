# Tech stack

Every dependency, what it buys, and why it over the alternatives. The short version: there is
one runtime dependency and it is not a Python package.

## Runtime

| | |
|---|---|
| **Python ≥ 3.11** | The floor. `X \| Y` unions, `:=`, and `dataclasses` with `slots`-era behaviour. Nothing needs 3.12+. |
| **Standard library only** | No runtime pip dependencies. `http.server`, `json`, `dataclasses`, `pathlib`, `subprocess`, `html`, `re`, `hashlib`. |
| **A Chromium-family browser** | Not a Python dependency — an executable located at runtime. Chrome, Chromium, Edge or Brave. **Only** for PDF export. |

**Why zero dependencies.** This is a small tool people install to touch one file. Every
dependency is a thing that can break an install, need a lockfile, or pull a supply chain into
someone's resume. The stdlib does everything here adequately, and `http.server` binding to
loopback for one user is not a compromise worth trading a dependency for.

## Development

| | |
|---|---|
| **pytest ≥ 8** | The suite. `pythonpath` is set in `pyproject.toml`. |
| **PyMuPDF ≥ 1.24** | Text extraction from generated PDFs. The only way to assert what a parser actually sees. |

Both are `[project.optional-dependencies].dev`; neither is needed to use the tool.

## Rejected alternatives

Surveyed July 2026 across five research tracks. The full write-ups are in the author's
workspace; the conclusions that shaped this code:

| Considered | Why not |
|---|---|
| **RenderCV** | The strongest candidate — Python, Typst since v2.0, nine single-column themes, tagged PDFs. Rejected because **cover letters do not fit its schema**, so adopting it means running two rendering paths. Its data model is also its own YAML, making JSON Resume → RenderCV one-way and lossy, and it is bus-factor 1. See [`../decisions/0007-keep-the-in-house-renderer.md`](../decisions/0007-keep-the-in-house-renderer.md). |
| **JSON Resume tooling** (`resume-cli`, themes) | Node-centric; themes are Node modules and unusable without it. The schema is worth adopting; the ecosystem is not. Archived June 2026. |
| **HackMyResume / FRESH** | Dead since 2018. The published package crashes on modern Node. Its `analyze` has zero ATS logic. Worth stealing ideas from, not code. |
| **Reactive Resume** and hosted builders | Wrong shape — running Postgres and two containers to edit a text file. Genuinely scriptable, and its JSON Patch edit interface is a good idea worth stealing later. |
| **WeasyPrint / wkhtmltopdf** for PDF | Would replace "a browser you already have" with a compiled Python dependency, breaking the zero-dependency property. Headless Chrome is already installed on virtually every machine this targets. |
| **LaTeX / Typst** | Better typesetting than a browser, but Knuth-Plass buys little on 1–2 pages of ragged-right bullets, and either adds a toolchain. HTML is also what the viewer needs anyway. |
| **A template engine** (Jinja2) | One HTML skeleton and one page do not justify it, and it is a runtime dependency. Rendering is f-strings through a single `esc()`. |
| **A frontend framework** | The viewer is one self-contained page that must work from `file://`. Vanilla JS, no build step. |
| **The JSON Resume registry** | Requires a public gist and an OAuth scope that reads and writes all your gists, and copies the resume to a third party. Not a dependency question — a privacy one. |

## Things deliberately not adopted from the schema

JSON Resume has **no required fields and `additionalProperties: true` throughout**, so `{}`
validates. Validation is therefore hand-rolled rather than delegated to a schema validator —
see [`data-model-and-config.md`](data-model-and-config.md).
