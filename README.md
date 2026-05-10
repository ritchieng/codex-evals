# codex-evals

Ask Codex:

```text
/eval
```

and get a short answer to:

> What just happened, how good was it, and what should improve first?

The user surface is intentionally small. The plugin handles the repeatable
scorecard, evidence checks, skill/plugin review, and optional local CLI reports
underneath.

## Install

Add this repo as a Codex plugin marketplace.

In Codex, open **Add marketplace** and use:

```text
Source: <this repo Git URL or local folder>
Git ref: main
Sparse paths:
marketplace.json
plugins/codex-evals
```

For local development on this machine:

```text
Source: /Users/ritchieng/Repos/codex-evals
Git ref: main
Sparse paths:
marketplace.json
plugins/codex-evals
```

Then run:

```text
/eval
```

## Commands

```text
/eval
/eval skill <name-or-path>
/eval bundle
/eval why
/eval fix-first
```

- `/eval` evaluates the current thread.
- `/eval skill <name-or-path>` evaluates a `SKILL.md`.
- `/eval bundle` evaluates the conversation plus related skills/plugins.
- `/eval why` explains the score with evidence.
- `/eval fix-first` returns only the highest-leverage improvements.

Every report starts with:

1. Overall grade.
2. 3 strongest signals.
3. 3 highest-impact fixes.
4. What to do next.

## Scorecard

| Dimension | Question |
| --- | --- |
| Clarity | Did the conversation establish the real goal? |
| Grounding | Did the agent inspect the right files/state before deciding? |
| Execution | Did the agent make concrete progress without unnecessary friction? |
| User Fit | Was the result understandable and usable by the user? |
| Craft | For skills/plugins, are triggers, workflow, boundaries, and outputs sharp? |

Scores are traceable to evidence. Missing receipts lower confidence, even when
the work sounds plausible.

## Optional CLI

The plugin is the main experience. Use the CLI for local reports, demos, and
debugging.

Run without installing:

```bash
python3 -m codex_evals.cli demo
python3 -m codex_evals.cli doctor
python3 -m codex_evals.cli conversation examples/onboarding-thread.md
```

Install the command name:

```bash
python3 -m pip install -e .
```

Then use:

```bash
codex-evals demo
codex-evals doctor
codex-evals conversation transcript.md
codex-evals skill plugins/codex-evals/skills/evaluate-skill/SKILL.md
codex-evals bundle --current
```

Outside Codex, `--current` reads `CODEX_EVALS_THREAD_TEXT`,
`CODEX_EVALS_CURRENT_THREAD`, or `.codex-evals/current-thread.md` when present.

## Files

```text
marketplace.json
plugins/codex-evals/
+-- .codex-plugin/plugin.json
+-- commands/eval.md
+-- skills/
    +-- evaluate-conversation/SKILL.md
    +-- evaluate-skill/SKILL.md
    +-- evaluate-bundle/SKILL.md
codex_evals/
examples/onboarding-thread.md
templates/
```

Useful files:

- [marketplace.json](marketplace.json): marketplace entry for Codex.
- [plugins/codex-evals/commands/eval.md](plugins/codex-evals/commands/eval.md): `/eval` command behavior.
- [codex_evals](codex_evals): local CLI/report engine.
- [examples/onboarding-thread.md](examples/onboarding-thread.md): sample transcript for demos.
- [templates/eval-card.md](templates/eval-card.md): human-readable report template.

## Verify

```bash
python3 -m unittest
python3 -m json.tool marketplace.json
python3 -m json.tool plugins/codex-evals/.codex-plugin/plugin.json
```
