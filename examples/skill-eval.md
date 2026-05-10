# Skill Eval Example

## Subject

- Name: spreadsheet-cleanup
- Type: skill
- Source: `skills/spreadsheet-cleanup/SKILL.md`
- Evaluator: reviewer

## Overall

- Grade: B
- Score: 11/15
- Verdict: Pass

## 3 Strongest Signals

1. Execution: The skill has a concrete cleanup and verification workflow.
2. Grounding: It tells the agent to inspect workbook structure before editing.
3. Craft: Boundaries are present for preserving formulas and user data.

## 3 Highest-Impact Fixes

1. Clarity: Replace "messy spreadsheet" with observable triggers such as merged headers, duplicate rows, and inconsistent dates.
2. Craft: Collapse two overlapping cleanup paths into one default workflow.
3. User Fit: Define the final report shape more tightly.

## What To Do Next

```text
codex-evals skill skills/spreadsheet-cleanup/SKILL.md --format markdown
```

## Scorecard

| Dimension | Score | Evidence | Fix |
| --- | ---: | --- | --- |
| Clarity | 2/3 | The purpose is useful, but the trigger is broad. | Name concrete spreadsheet symptoms. |
| Grounding | 3/3 | The workflow inspects workbook structure and formula cells. | Keep the evidence checklist close to the workflow. |
| Execution | 3/3 | The skill includes ordered cleanup and verification steps. | Remove the duplicate cleanup path. |
| User Fit | 1/3 | The final response shape is under-specified. | Lead with changed sheets, preserved formulas, and verification. |
| Craft | 2/3 | Triggers, workflow, and boundaries exist, but outputs are soft. | Tighten output requirements. |
