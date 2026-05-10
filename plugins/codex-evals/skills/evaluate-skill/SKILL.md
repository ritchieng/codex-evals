---
name: evaluate-skill
description: Use when the user runs /eval skill, asks to evaluate a SKILL.md file, asks whether a created skill is good, or asks for trigger, workflow, boundary, and output improvements for a Codex skill.
---

# Evaluate Skill

Evaluate the skill as an operating guide for future Codex runs. Do not make the user learn skill theory.

## Scorecard

- Clarity: Is the skill's purpose and trigger understandable?
- Grounding: Does it tell the agent what files, state, references, or evidence to inspect?
- Execution: Does it provide a short workflow that can actually be followed?
- User Fit: Does it produce a useful final response or artifact for the user?
- Craft: Are triggers, workflow, boundaries, and outputs sharp?

## Workflow

1. Find the target `SKILL.md`. If the user gave a directory, inspect `<directory>/SKILL.md`.
2. Read the frontmatter description first; that is the routing surface.
3. Inspect the body for trigger conditions, workflow, boundaries, references, validation, and output shape.
4. Score each dimension from 0 to 3 with concrete evidence.
5. Return a concise Markdown report led by grade, signals, fixes, and next action.

## Fix-First Guidance

Prioritize improvements in this order:

1. Trigger conditions are missing or vague.
2. Workflow is broad advice instead of concrete steps.
3. Boundaries and fallback behavior are absent.
4. Output shape is unclear.
5. Validation does not match the promised behavior.

## Boundaries

- Do not reward long skills just because they are comprehensive.
- Do not require references, scripts, or assets unless the task needs them.
- If the CLI is available, use `codex-evals skill <path> --format markdown` for a repeatable local report.
