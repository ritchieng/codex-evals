# codex-evals

Ask Codex:

```text
/eval
```

and get a short answer to:

> What just happened, how good was it, and what should improve first?

The user surface is intentionally small. The plugin handles the repeatable
scorecard, evidence checks, skill/plugin review, demos, and setup checks
underneath.

## Install

Add this repo as a Codex plugin marketplace.

In Codex, open **Add marketplace** and use:

```text
Source: https://github.com/ritchieng/codex-evals
Git ref: main
Sparse paths:
.agents/plugins
plugins/codex-evals
```

For local development on this machine:

```text
Source: /Users/ritchieng/Repos/codex-evals
Git ref: main
Sparse paths:
.agents/plugins
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
/eval demo
/eval doctor
```

- `/eval` evaluates the current thread.
- `/eval skill <name-or-path>` evaluates a `SKILL.md`.
- `/eval bundle` evaluates the conversation plus related skills/plugins.
- `/eval why` explains the score with evidence.
- `/eval fix-first` returns only the highest-leverage improvements.
- `/eval demo` shows a sample report.
- `/eval doctor` checks whether the plugin package is wired correctly.

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

## Files

```text
.agents/plugins/marketplace.json
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

- [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json): marketplace entry for Codex.
- [plugins/codex-evals/commands/eval.md](plugins/codex-evals/commands/eval.md): `/eval` command behavior.
- [codex_evals](codex_evals): shared report engine used by the plugin package.
- [examples/onboarding-thread.md](examples/onboarding-thread.md): sample transcript for demos.
- [templates/eval-card.md](templates/eval-card.md): human-readable report template.

## Verify

```bash
python3 -m unittest
python3 -m json.tool .agents/plugins/marketplace.json
python3 -m json.tool plugins/codex-evals/.codex-plugin/plugin.json
```
