# Testing

The approach, what is covered, what is not, and how CI runs. 208 unit tests, ~30s locally,
plus a separate on-demand acceptance harness (see below).

```sh
pytest -q                    # everything (the unit layer)
pytest -q tests/test_pdf.py  # just the slow ones
python qa/acceptance.py      # the acceptance layer — real browser + live server
```

## The approach

Three ideas do most of the work.

**Assert over the whole space, not a sample.** The claims that matter are universal — every
spec renders, every name round-trips, every layout is single-column and ≥10pt. Those are
checked across all 10,080 specs, or a `spread()` across them where rendering each would be
slow. A property that holds for a sample and fails for one point is exactly the bug a resume
tool cannot afford.

**Test the output a machine will read, not the one a human sees.** The PDF tests re-extract
text with PyMuPDF and assert the content survived — including that it comes back in document
order, which is the mechanism every layout rule rests on. A resume that renders beautifully
and extracts as garbage is worse than useless, because the failure is invisible to the sender.

**Test the prose too.** `scaffold.py` ships documentation to users. Tests parse that prose and
assert every command it mentions exists and every `--theme` value resolves. This is not
belt-and-braces: it caught a shipped quickstart that documented two deleted commands and a
`--theme` that errored.

## Layout

| File | Covers |
|---|---|
| `conftest.py` | One fixture profile, deliberately **clean** — it trips no rule, so a lint test can break exactly one thing and attribute the finding. |
| `test_space.py` | Enumeration, name uniqueness, round-trip across the whole space, distance and neighbour invariants, deterministic spread. |
| `test_compose.py` | Every spec renders; ATS claims hold; screen inset; no multi-column CSS; no network reference; escaping; purity. |
| `test_lint.py` | Each rule, by breaking one thing. Plus that the linter cannot edit. |
| `test_stints.py` | The model, legacy normalisation, validation, and that no bullet is dropped by either grouping. |
| `test_viewer.py` | The embedded payload, both deliveries, and that they differ *only* in the two documented switches. |
| `test_catalogue_and_server.py` | Both deliveries end to end over a live loopback server; paging partitions the space; the profile is re-read on change; publish and export; that no session state exists. |
| `test_cli.py` | Command surface, profile resolution, layout resolution, publish, exit codes, deliverable naming. |
| `test_pdf.py` | PDF production, text extraction, page margins, one-page output. |

## Tests worth knowing about

**`test_names_survive_a_new_axis_value`** inserts a value into an axis and asserts existing
names are unchanged. The previous naming scheme failed this silently, and a published spec
came to mean a different layout.

**`test_no_layout_prints_to_the_paper_edge`** forces a multi-page profile deliberately — the
bug it guards was invisible on anything that fitted on one page, and invisible in the viewer,
which shows page one.

**`test_the_two_deliveries_differ_only_in_those_switches`** normalises the two viewer outputs
and asserts equality. The viewer was two implementations that had begun to drift.

**`test_the_linter_only_ever_reports`** asserts the profile is byte-identical after a check
that fired. The anti-fabrication rule is stated in prose everywhere; this is the only place it
is enforced.

**`test_the_scaffold_makes_no_assumptions_about_the_reader`** greps shipped prose for gendered
pronouns. It exists because a shipped skill once described the author rather than a stranger.

## Skips

`test_pdf.py` skips wholesale when PyMuPDF is missing or no Chromium-family browser is
present — a machine that cannot make a PDF should not fail the suite for it.

**A skip that nobody notices is a test that stopped running**, so CI has a step that fails
deliberately if the PDF tests skip on a runner where they should not.

## CI

`.github/workflows/tests.yml` — macOS and Ubuntu × Python 3.11 and 3.13, on push, PR and
manual dispatch. Ubuntu installs Chromium so PDF export is genuinely exercised.

CI runs the bare `pytest` entry point, which does **not** put the working directory on
`sys.path` the way `python -m pytest` does. The suite shares a fixture via
`from tests.conftest import CLEAN`, so `pythonpath = ["."]` is pinned in `pyproject.toml`.
This was the first thing CI caught.

## Acceptance layer — `qa/acceptance.py`

The unit suite mocks the browser and calls `cli.main` in-process, so it cannot see whether the
thing works end to end on a real machine. `qa/acceptance.py` is the second layer: it runs the
command as a subprocess, drives a **live `serve` server** over HTTP, renders the viewer in a
**real headless browser** and confirms the JavaScript actually builds the grid, exports a
**real PDF**, and does it all against a fresh `init` workspace. It exits non-zero on failure,
skips browser-dependent checks when none is present, and takes `--open` (watch the live viewer)
and `--keep` (preserve the workspace to inspect outputs). It is run on demand, not in CI — and
it was written after it caught an archive-collision bug the unit suite missed. Details:
[`qa/README.md`](../../qa/README.md).

## Gaps

Honest list.

- **Windows is untested.** Nothing is known to be platform-specific, but nobody has run it.
- **No visual regression.** Rendering correctness is structural — content present, single
  column, margins, escaping. Whether a layout looks *good* is unchecked, and several real
  defects were found by looking rather than by testing.
- **No *automated* clean-machine install test.** A fresh venv install from the packaged repo,
  then `init`/`lint`/`catalogue`/`serve`/`publish`, was run by hand once before release and
  passed — but nothing in CI installs the built package and exercises the entry point, so a
  packaging regression could slip through.
- **`viewer.py`'s JavaScript is only *render*-tested.** The acceptance harness now loads the
  viewer in a real headless browser and confirms the JS builds the grid — but **interactions**
  (colour-pin, paging, the publish button) are still unexercised; that needs a browser-driver
  (e.g. Playwright), a dependency the project has so far avoided.
- **No performance guard.** `spread()` was cubic and shipped that way; nothing would have
  caught it but a slow test run.
