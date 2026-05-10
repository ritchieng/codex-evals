import json
import tempfile
import unittest
from pathlib import Path

from codex_evals.evaluator import evaluate_conversation, evaluate_plugin, evaluate_skill
from codex_evals.render import render_markdown, render_result


class ConversationEvaluationTests(unittest.TestCase):
    def test_empty_conversation_is_not_overconfident(self):
        result = evaluate_conversation("", source="current thread")

        self.assertEqual(result["overall"]["grade"], "F")
        self.assertEqual(result["overall"]["score"], 0)
        self.assertIn("No conversation text", result["dimensions"][0]["evidence"][0])

    def test_conversation_report_shape(self):
        transcript = """
        User goal: add CSV validation with a clear success condition.
        Agent plan: inspect the importer, then add tests.
        Ran rg importer and sed to read app/uploads/importer.ts.
        Checked git status and git diff.
        Implemented validation, added tests, ran npm test, and tests passed.
        Final response gave the user changed file paths and the next command.
        """

        result = evaluate_conversation(transcript)
        markdown = render_markdown(result)

        self.assertIn("## 3 Strongest Signals", markdown)
        self.assertIn("## 3 Highest-Impact Fixes", markdown)
        self.assertIn("## What To Do Next", markdown)
        self.assertEqual(len(result["strongest_signals"]), 3)
        self.assertEqual(len(result["highest_impact_fixes"]), 3)

    def test_short_conversation_stays_low_confidence(self):
        result = evaluate_conversation("please check this")

        self.assertLess(result["overall"]["score"], 6)

    def test_poor_conversation_stays_low_confidence(self):
        result = evaluate_conversation("I might do something later. Looks good.")

        self.assertIn(result["overall"]["grade"], {"D", "F"})

    def test_excellent_conversation_scores_well(self):
        transcript = """
        The user goal and objective were restated with success requirements.
        The plan listed a checklist and deliverable.
        The agent ran rg, sed, git status, and git diff, then read app/main.py and tests/test_main.py.
        It inspected the relevant state, verified assumptions, implemented the change, updated docs,
        added tests, ran the test command, and tests passed.
        The final answer was concise, named the changed file path, explained verification,
        gave the user the next command, and marked the work complete.
        """

        result = evaluate_conversation(transcript)

        self.assertIn(result["overall"]["grade"], {"A", "B"})


class SkillEvaluationTests(unittest.TestCase):
    def test_skill_detects_valid_skill_and_craft(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "evaluate-thing"
            skill_dir.mkdir()
            skill_path = skill_dir / "SKILL.md"
            skill_path.write_text(
                """---
name: evaluate-thing
description: Use when the user asks to evaluate a thing and wants trigger, workflow, boundary, and output improvements.
---

# Evaluate Thing

## Workflow

1. Inspect the relevant files and evidence.
2. Score the thing.
3. Validate the result with a check.

## Boundaries

Do not overclaim when evidence is missing.

## Output

Lead with a concise Markdown report and what to do next.
""",
                encoding="utf-8",
            )

            result = evaluate_skill(skill_path)

        names = [dimension["name"] for dimension in result["dimensions"]]
        self.assertIn("Craft", names)
        self.assertGreaterEqual(result["overall"]["score"], 10)

    def test_json_result_renders_back_to_markdown(self):
        result = evaluate_conversation("goal plan read file.py implemented tests passed final next command")
        loaded = json.loads(render_result(result, output_format="json"))
        markdown = render_result(loaded, output_format="markdown")

        self.assertIn("Overall grade", markdown)
        self.assertIn("Scorecard", markdown)


class PluginEvaluationTests(unittest.TestCase):
    def test_repo_plugin_scores_with_command_and_skills(self):
        result = evaluate_plugin("plugins/codex-evals")

        self.assertEqual(result["type"], "plugin")
        self.assertGreaterEqual(result["overall"]["score"], 12)
        self.assertTrue(any(dimension["name"] == "Craft" for dimension in result["dimensions"]))


if __name__ == "__main__":
    unittest.main()
