# codex-evals

`codex-evals` is a local-first way to ask:

> Codex, evaluate what just happened and tell me what to improve.

Users should not need to understand eval frameworks, rubrics, JSON schemas, or
harnesses upfront. The default surface is `/eval`; the repeatable machinery lives
underneath as skills, plugin commands, JSON results, and a small CLI.

## Default UX

The main user surface is conversational:

```text
/eval
```

No args means: evaluate the current thread and return a concise Markdown report.

Supported forms:

```text
/eval
/eval skill <name-or-path>
/eval bundle
/eval why
/eval fix-first
```

The first response should lead with:

1. Overall grade.
2. 3 strongest signals.
3. 3 highest-impact fixes.
4. What to do next as a concrete command or prompt.

Deeper artifacts are available when requested, but the default is a short,
improvement-oriented report.

## Fast Onboarding

From a fresh clone, run the onboarding command first:

```bash
python3 -m codex_evals.cli init
```

After installing the CLI, the same command is:

```bash
codex-evals init
```

`init` checks the CLI, plugin manifest, `/eval` command, required skills, report
engine, current-thread bridge, and local plugin registration. It also writes a
local demo transcript at `.codex-evals/onboarding-thread.md` so the next command
produces a useful report immediately.

Use these during setup:

```bash
codex-evals demo
codex-evals doctor
codex-evals conversation examples/onboarding-thread.md
```

The intended first-run flow is:

1. Run `codex-evals init`.
2. Run `codex-evals demo` to see the report shape.
3. Open Codex and run `/eval`.

If plugin registration cannot be automated in your environment, `doctor` prints
the exact missing path or next fix instead of making you inspect plugin internals.

## Add As A Marketplace

This repo is packaged as a Codex plugin marketplace through
[marketplace.json](marketplace.json). In the Codex "Add marketplace" flow, use:

```text
Source: <this repo Git URL or local folder>
Git ref: main
Sparse paths:
marketplace.json
plugins/codex-evals
```

For local development, `Source` can be this repo folder:

```text
/Users/ritchieng/Repos/codex-evals
```

The marketplace exposes one plugin:

```text
codex-evals -> ./plugins/codex-evals
```

After adding it, the user-facing command is:

```text
/eval
```

## Scorecard

The default scorecard is intentionally small:

| Dimension | Question |
| --- | --- |
| Clarity | Did the conversation establish the real goal? |
| Grounding | Did the agent inspect the right files/state before deciding? |
| Execution | Did the agent make concrete progress without unnecessary friction? |
| User Fit | Was the result understandable and usable by the user? |
| Craft | For skills/plugins, are triggers, workflow, boundaries, and outputs sharp? |

Scores are explainable and traceable to evidence. Missing receipts lower the
score even when the work sounds plausible.

## CLI

The CLI renders Markdown by default and JSON when needed:

```bash
codex-evals init
codex-evals doctor
codex-evals demo
codex-evals conversation --current --format markdown
codex-evals skill <path> --format markdown
codex-evals bundle --current --format markdown
codex-evals report <result.json> --format markdown
```

Inside Codex, `/eval` evaluates the visible current thread. Outside that context,
`--current` reads `CODEX_EVALS_THREAD_TEXT`, `CODEX_EVALS_CURRENT_THREAD`, or a
local current-thread file when one exists.

It also accepts transcript files or stdin for local testing:

```bash
codex-evals conversation transcript.md --format json
cat transcript.md | codex-evals conversation --stdin --format markdown
```

Install locally from this repo:

```bash
python3 -m pip install -e .
```

Or run without installing:

```bash
python3 -m codex_evals.cli conversation --current --format markdown
```

## Plugin Layout

The marketplace entry lives at [marketplace.json](marketplace.json).
The Codex plugin lives in [plugins/codex-evals](plugins/codex-evals):

```text
plugins/codex-evals/
+-- .codex-plugin/plugin.json
+-- commands/eval.md
+-- skills/
    +-- evaluate-conversation/SKILL.md
    +-- evaluate-skill/SKILL.md
    +-- evaluate-bundle/SKILL.md
```

The command is the user entrypoint. The skills hold the repeatable behavior for
current-thread review, skill review, and bundle review.

## Report Shape

Use [templates/eval-card.md](templates/eval-card.md) for a human-readable card.
Use [templates/eval-log.csv](templates/eval-log.csv) to track many evals.

Machine-readable JSON stores the same structure that Markdown renders:

- `overall`: grade, score, max score, verdict.
- `strongest_signals`: the top evidence-backed positives.
- `highest_impact_fixes`: the first fixes to make.
- `what_to_do_next`: a concrete command or prompt.
- `dimensions`: scorecard rows with evidence and fixes.

## Product Principles

- Start with the default scorecard; do not make users choose a rubric first.
- Make `/eval` useful even when the user only wants a quick answer.
- Treat evaluation as improvement-oriented, not judgment-oriented.
- Prefer evidence over confidence.
- Keep scores explainable; make fix-first guidance more important than the number.
- Add benchmark harnesses, custom rubrics, and dashboards later, after the default
  loop is effortless.

## Test Plan

- Verify `/eval` with no args evaluates the current conversation and returns a concise Markdown report.
- Verify `/eval skill <path>` detects a valid `SKILL.md`, scores it, and identifies trigger/workflow gaps.
- Verify `/eval bundle` links the current conversation to created or edited skills/plugins.
- Verify CLI commands work outside Codex and produce the same report shape as the slash command.
- Test empty, short, excellent, and poor conversations so reports stay useful and not overconfident.
