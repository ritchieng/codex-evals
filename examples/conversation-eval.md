# Conversation Eval Example

## Subject

- Name: Add import validation to CSV upload
- Type: conversation
- Source: transcript
- Evaluator: reviewer

## Overall

- Grade: A
- Score: 11/12
- Verdict: Pass

## 3 Strongest Signals

1. Grounding: The agent inspected the importer and existing tests before changing behavior.
2. Execution: The agent added validation and ran the focused test command.
3. User Fit: The final response named changed files, verification, and remaining risk.

## 3 Highest-Impact Fixes

1. User Fit: Include the exact invalid-row error examples in the final handoff.
2. Grounding: Add a fixture preview if CSV errors become visual.
3. Execution: Add one integration test if the upload path has a UI layer.

## What To Do Next

```text
Run /eval fix-first after adding the integration test.
```

## Scorecard

| Dimension | Score | Evidence | Fix |
| --- | ---: | --- | --- |
| Clarity | 3/3 | The goal and success condition were explicit. | Keep the success condition in the first plan. |
| Grounding | 3/3 | The agent inspected relevant files and existing test shape. | Add fixture previews for visual errors. |
| Execution | 3/3 | Code changed and tests passed. | Add broader coverage only if the UI path is touched. |
| User Fit | 2/3 | The final handoff was usable but could show example errors. | Include one concrete before/after example. |
