# resume-pipeline

Explore a design space of resume layouts, lint them for ATS parsing, and render to PDF.

**Not a resume generator.** That category is well served and mostly abandoned. This is
three things that do not exist elsewhere:

- **A design-space explorer.** Layouts are not hand-written themes; they are points in a
  product of six independent axes (5,040 of them). Mark the ones you like and the next
  batch is sampled from their neighbourhood — steering, not shuffling.
- **An ATS linter.** Nothing open-source checks a resume *layout* for parse safety. This
  does, and every generated layout is single-column and >=10pt by construction.
- **A provenance gate** (in progress) so an AI agent can rewrite your resume without
  inventing facts about your career.

Zero runtime dependencies. Python 3.11+, plus any Chromium-family browser for PDF export.

## Use

```
resume-pipeline serve   resume.json          # interactive layout explorer
resume-pipeline build   resume.json --theme all
resume-pipeline lint    resume.json --theme slate
resume-pipeline explore resume.json --count 24
```

Input is [JSON Resume](https://jsonresume.org/schema). Output is HTML, PDF, and Markdown.

## Status

Early. The explorer and linter work; tests, docs, and the provenance model are in progress.

## License

MIT
