---
name: evaluate-conversation
description: Use when the user runs /eval with no args, asks to evaluate the current thread, asks what just happened, asks why a conversation scored a certain way, or asks for fix-first improvements to a Codex conversation.
---

# Evaluate Conversation

Default to the current visible thread. Do not ask the user to pick a rubric.

## Scorecard

Score only what is visible from the thread and local evidence:

- Clarity: Did the conversation establish the real goal?
- Grounding: Did the agent inspect the right files, commands, state, screenshots, citations, or outputs before deciding?
- Execution: Did the agent make concrete progress without unnecessary friction?
- User Fit: Was the result understandable and usable by the user?

## Workflow

1. Identify the user's latest goal and the actual outcome.
2. Gather receipts from the visible thread: files changed, commands run, tests, screenshots, citations, user confirmations, blockers, and final handoff.
3. Score each dimension from 0 to 3 with one evidence line.
4. Lead with a concise Markdown report:
   - Overall grade.
   - 3 strongest signals.
   - 3 highest-impact fixes.
   - What to do next as a concrete command or prompt.
5. Keep deeper diagnostics out of the first response unless the user asks `why`.

## Modes

- `/eval`: concise current-thread report.
- `/eval why`: include the scorecard table and evidence for each score.
- `/eval fix-first`: return only the top one to three improvements, ordered by leverage.

## Boundaries

- Do not overclaim when the thread lacks receipts.
- Treat missing evidence as an improvement opportunity, not a character judgment.
- Prefer "fix first" guidance over numeric score discussion.
- If the local CLI has an exported transcript, `codex-evals conversation --current --format markdown` may be used for a repeatable report.
