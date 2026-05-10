# AGENTS.md

This repo builds a Codex plugin for evaluating Codex work. Treat this file as
the shared operating model for future agents improving the project.

## Product Promise

The product should feel like:

```text
Codex, evaluate what just happened and tell me what to improve.
```

The primary surface is `/eval`. Users should not need to understand rubrics,
schemas, harnesses, or implementation details before getting value.

Keep the powerful parts underneath:

- Repeatable scorecards.
- Evidence-backed local reports.
- Conversation quality review.
- Skill and plugin quality review.
- Bundle review across conversation plus created or edited artifacts.
- Optional JSON for machines, Markdown for humans.

## Public Reasoning Model

Do not expose private chain-of-thought. When explaining an evaluation, show the
public reasoning model:

1. What was the user trying to accomplish?
2. What evidence is visible?
3. What changed or progressed?
4. What is easiest for the user to act on next?
5. What single fix has the highest leverage?

Reports should give concise rationale, receipts, and next steps, not hidden
internal deliberation.

## Ontology

- **Thread**: The current Codex conversation being evaluated.
- **Artifact**: Any file, report, command output, screenshot, skill, plugin, or
  generated object produced or modified during the work.
- **Skill**: A `SKILL.md` that changes future Codex behavior through triggers,
  workflow, boundaries, and output guidance.
- **Plugin**: A packaged Codex capability with `.codex-plugin/plugin.json`,
  commands, skills, and optional support files.
- **Marketplace**: A `marketplace.json` that exposes one or more plugins for
  Codex Add Marketplace.
- **Bundle**: A thread plus related artifacts, especially created or modified
  skills/plugins.
- **Receipt**: Concrete evidence: file path, diff, test result, command output,
  screenshot, citation, rendered artifact, or user confirmation.
- **Signal**: A positive evidence-backed observation.
- **Fix**: A specific improvement that can be acted on next.
- **Scorecard**: The default small rubric used by `/eval`.
- **Report**: The user-facing Markdown output and its equivalent JSON structure.

## Scorecard

Use the default scorecard unless a user explicitly asks for a custom rubric:

| Dimension | Question |
| --- | --- |
| Clarity | Did the conversation establish the real goal? |
| Grounding | Did the agent inspect the right files/state before deciding? |
| Execution | Did the agent make concrete progress without unnecessary friction? |
| User Fit | Was the result understandable and usable by the user? |
| Craft | For skills/plugins, are triggers, workflow, boundaries, and outputs sharp? |

Craft applies to skills/plugins and bundle review. It may be omitted for a pure
conversation report.

## Report Contract

Every user-facing report should lead with:

1. Overall grade.
2. 3 strongest signals.
3. 3 highest-impact fixes.
4. What to do next.

Keep the first response short. Put detailed evidence behind `/eval why` or an
explicit request for deeper diagnostics.

## Command Surface

The plugin should expose these user behaviors:

- `/eval`: Evaluate the current thread.
- `/eval skill <name-or-path>`: Evaluate a skill.
- `/eval bundle`: Evaluate the current thread plus related skills/plugins.
- `/eval why`: Explain the current score with evidence.
- `/eval fix-first`: Return only the highest-leverage improvements.
- `/eval demo`: Show a sample report.
- `/eval doctor`: Check that plugin packaging is wired correctly.

Do not send normal users to a separate CLI onboarding flow. The CLI can exist as
an implementation detail and testing aid, but README and command docs should keep
the product plugin-first.

## Evidence Rules

- Prefer receipts over confidence.
- Missing evidence should lower confidence.
- Do not treat "looks good" as proof.
- If no current-thread text is available outside Codex, say so plainly and tell
  the user how to provide a transcript.
- Never claim tests, validation, screenshots, or files were inspected unless
  there is actual evidence.

## Improvement Loop

When improving this repo:

1. Keep `/eval` as the simplest possible entrypoint.
2. Update the marketplace, plugin command, skills, README, and tests together
   when behavior changes.
3. Preserve Markdown as the default human output and JSON as the machine-readable
   equivalent.
4. Keep onboarding plugin-first: Add Marketplace, install, run `/eval`.
5. Add abstractions only when they reduce user friction or make reports more
   repeatable.

## Repo Map

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
examples/
templates/
tests/
```

## Verification

Before handing off changes, run:

```bash
python3 -m unittest
python3 -m json.tool marketplace.json
python3 -m json.tool plugins/codex-evals/.codex-plugin/plugin.json
git diff --check
```

Also check that the README still gives the shortest path:

```text
Add Marketplace -> install plugin -> /eval
```

## Non-Goals For Now

- Heavy benchmark dashboards.
- Requiring users to choose rubrics before first value.
- Making CLI onboarding the main product path.
- Long diagnostic walls by default.
- Exposing private chain-of-thought.

## Design Bias

This project should bias toward low-friction understanding. If a feature makes
the first successful `/eval` harder, it probably belongs behind an advanced mode
or should wait.
