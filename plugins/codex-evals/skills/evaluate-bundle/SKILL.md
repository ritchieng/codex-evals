---
name: evaluate-bundle
description: Use when the user runs /eval bundle or asks to evaluate a whole workflow that includes the current conversation plus created or modified skills, plugins, commands, or local reports.
---

# Evaluate Bundle

Evaluate the whole loop: conversation quality plus the quality of any skill/plugin artifacts it created or changed.

## Scorecard

- Clarity: Was the overall goal clear across the conversation and artifacts?
- Grounding: Did the agent inspect the right state before creating or changing the artifacts?
- Execution: Did the workflow produce concrete, verified progress?
- User Fit: Can the user understand and use the result without learning eval machinery?
- Craft: For skills/plugins, are triggers, workflow, boundaries, and outputs sharp?

## Workflow

1. Evaluate the current conversation using the conversation scorecard.
2. Identify related artifacts from the thread and worktree:
   - `plugins/*/commands/*.md`
   - `plugins/*/skills/*/SKILL.md`
   - `skills/*/SKILL.md`
   - `.codex-plugin/plugin.json`
   - local JSON or Markdown reports
3. Evaluate each related `SKILL.md` with the skill scorecard.
4. Check that command docs and plugin metadata match the promised user surface.
5. Return one concise bundle report with grade, signals, fixes, and next action.

## Boundaries

- Do not bury the user in per-file diagnostics by default.
- If related skills/plugins cannot be detected, say that directly and tell the user how to pass a path.
- If the CLI is available, use `codex-evals bundle --current --format markdown` for a repeatable report.
