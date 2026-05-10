# /eval

Evaluate what just happened and tell the user what to improve.

Default behavior:

- No args: evaluate the current conversation.
- `skill <name-or-path>`: evaluate a skill. Prefer a direct path when one is present.
- `bundle`: evaluate the current conversation plus related created or edited skills/plugins.
- `why`: explain the current score with the scorecard and evidence.
- `fix-first`: return only the highest-leverage improvements.
- `demo`: show a concise sample evaluation so the user understands the output shape.
- `doctor`: check plugin packaging and setup state, then return only missing or useful next steps.

User experience:

- Do not ask the user to choose a rubric first.
- Keep the first response short and improvement-oriented.
- Lead with overall grade, three strongest signals, three highest-impact fixes, and one concrete next command or prompt.
- Use the default scorecard: Clarity, Grounding, Execution, User Fit, and Craft for skills/plugins.
- Make every score traceable to visible evidence from the thread, files, commands, or reports.
- Keep setup help inside `/eval`; do not send normal users to a separate CLI flow.

Implementation path:

- This plugin is exposed through the repo root `marketplace.json` for Add marketplace imports.
- For current-thread review, use the `evaluate-conversation` skill.
- For skill review, use the `evaluate-skill` skill.
- For bundle review, use the `evaluate-bundle` skill.
- For `demo`, use the packaged demo transcript or produce the same report shape directly.
- For `doctor`, check that `marketplace.json`, `.codex-plugin/plugin.json`, `commands/eval.md`, and the three evaluation skills are present and coherent.
