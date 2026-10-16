# Skills

Claude Code skills used in Turnstone development. They are not memories: the index generator and
the disclosure scanner read only `collections/`, so review changes here by hand and propose them
on an ordinary maintenance branch rather than a `memory/` one.

## review

`/review` runs a multi-stage code review. Six finders work in parallel, one per dimension: bugs,
security, performance, quality, regressions against the base, and simplification of the design.
A verify stage re-reads the source behind every claim, an optional sweep looks for variants and
gaps on high-stakes changes, and a single sanity stage merges the findings, checks each fix and
writes the report.

- `review/commands/review.md`: the slash command that orchestrates the pipeline. It runs at the
  top level because an agent can't launch other agents.
- `review/agents/`: the six finders and the verify, sweep and sanity agents it launches.

Install them for every project, or copy them into one project's `.claude/` directory instead:

```sh
cp skills/review/commands/review.md ~/.claude/commands/
cp skills/review/agents/code-review-*.md ~/.claude/agents/
```

The security and performance finders each describe Turnstone's own surfaces in a
project-specific section; replace it when reviewing another codebase.
