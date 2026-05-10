# /eval

Evaluate what just happened and tell the user what to improve.

Default behavior:

- No args: evaluate the current conversation.
- `skill <name-or-path>`: evaluate a skill. Prefer a direct path when one is present.
- `bundle`: evaluate the current conversation plus related created or edited skills/plugins.
- `why`: explain the current score with the scorecard and evidence.
- `fix-first`: return only the highest-leverage improvements.

User experience:

- Do not ask the user to choose a rubric first.
- Keep the first response short and improvement-oriented.
- Lead with overall grade, three strongest signals, three highest-impact fixes, and one concrete next command or prompt.
- Use the default scorecard: Clarity, Grounding, Execution, User Fit, and Craft for skills/plugins.
- Make every score traceable to visible evidence from the thread, files, commands, or reports.

Implementation path:

- This plugin is exposed through the repo root `marketplace.json` for Add marketplace imports.
- For current-thread review, use the `evaluate-conversation` skill.
- For skill review, use the `evaluate-skill` skill.
- For bundle review, use the `evaluate-bundle` skill.
- For onboarding outside Codex, suggest `codex-evals init`, `codex-evals doctor`, and `codex-evals demo`.
- If a transcript or skill path is available locally, the shared CLI can render the same report shape:
  - `codex-evals init`
  - `codex-evals doctor`
  - `codex-evals demo`
  - `codex-evals conversation --current --format markdown`
  - `codex-evals skill <path> --format markdown`
  - `codex-evals bundle --current --format markdown`
  - `codex-evals report <result.json> --format markdown`
