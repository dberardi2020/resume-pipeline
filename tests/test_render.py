"""The docs renderer's inline emphasis — its one piece with real logic.

Bold may wrap an italic (`**a *b* c**`) and an italic may wrap a bold
(`*a **b** c*`); both must resolve, and emphasis inside a code span must stay
literal. These lock the behaviour the ticket board's rendering relies on.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "docs_render", Path(__file__).resolve().parents[1] / "docs" / "render.py")
render = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(render)


@pytest.mark.parametrize("src, want", [
    ("**bold**", "<strong>bold</strong>"),
    ("*italic*", "<em>italic</em>"),
    ("**a *b* c**", "<strong>a <em>b</em> c</strong>"),          # bold wraps italic
    ("*a **b** c*", "<em>a <strong>b</strong> c</em>"),          # italic wraps bold
    ("**a** and **b**", "<strong>a</strong> and <strong>b</strong>"),
    ("**a** then *b*", "<strong>a</strong> then <em>b</em>"),
    ("**Decision: a hold *implies* a filter**",
     "<strong>Decision: a hold <em>implies</em> a filter</strong>"),
    ("`**not bold**`", "<code>**not bold**</code>"),            # untouched inside code
    ("plain text", "plain text"),
])
def test_inline_emphasis(src, want):
    assert render.inline(src) == want
