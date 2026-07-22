# 0006 — The linter reports; it never edits

**Status:** Accepted · 2026-07-21

## Context

The linter flags bullets containing no figures, because unquantified prose genuinely does not
convey scope. The obvious way to satisfy that finding is to supply a number.

Point a generative model at a linter that demands metrics and you have built a machine for
manufacturing plausible lies about someone's career — and the person who has to defend
"reduced p99 latency by 40%" in an interview is not the one who wrote it.

Research across the surveyed tools found no tool that tracks which claims are the human's and
which are the model's. The hazard is not hypothetical; it is created by the feature.

## Decision

**`lint.check()` is a pure reporter.** It returns findings and never mutates the profile. No
`--fix`, no autocorrect, no suggested replacement text for a missing figure.

The rule it enforces, stated in the workspace `CLAUDE.md` and the shipped skill: **never
invent a career fact.** Flagging that a bullet lacks a number is useful; filling it in is not.
Ask, and leave the bullet unquantified until answered.

## Rationale

The line is not "AI helped write this" — that is normal and fine. The line is
**misrepresentation**, and invented metrics are the specific failure mode. Rewriting someone's
own facts into stronger prose is the entire point of the tool; introducing new facts is a
different act wearing the same clothes.

Detection-based arguments were considered and rejected: AI detectors are unreliable and biased
(61% false-positive on non-native English speakers), so "you will get caught" is not the
argument. The argument is narrower and stronger.

## Consequences

- Finding messages are phrased as questions and say so explicitly — the `work/unquantified`
  message ends *"(Ask for the number — never invent one.)"*
- A test asserts the profile is byte-identical after a check that fired. This is the only
  place the rule is *enforced* rather than stated.
- The linter reports a permanent error on a genuinely unquantified resume. That is correct
  behaviour, not a defect to silence.
- **Provenance tracking** (RP-0007) is the eventual counterweight: per claim, human-asserted
  fact or model-generated prose. Not built.
