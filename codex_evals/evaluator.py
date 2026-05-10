from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from statistics import mean
from typing import Any

SCORE_MAX = 3
RESULT_VERSION = "0.1"


def evaluate_conversation(text: str, *, source: str = "provided text") -> dict[str, Any]:
    text = text or ""
    empty = not text.strip()

    clarity_hits = _count_hits(
        text,
        [
            r"\bgoal\b",
            r"\bobjective\b",
            r"\bsuccess\b",
            r"\bdeliverable\b",
            r"\brequirement\b",
            r"\bplan\b",
            r"\bchecklist\b",
        ],
    )
    grounding_hits = _count_hits(
        text,
        [
            r"\brg\b",
            r"\bsed\b",
            r"\bgit status\b",
            r"\bgit diff\b",
            r"\binspect",
            r"\bread",
            r"\bopened",
            r"\bverified",
            r"[A-Za-z0-9_\-/]+\.(md|py|ts|tsx|js|json|yaml|yml|txt)",
        ],
    )
    execution_hits = _count_hits(
        text,
        [
            r"\bimplemented\b",
            r"\bcreated\b",
            r"\bupdated\b",
            r"\bchanged\b",
            r"\badded\b",
            r"\bran\b",
            r"\btest",
            r"\bpassed\b",
            r"\bcomplete",
        ],
    )
    fit_hits = _count_hits(
        text,
        [
            r"\bfinal\b",
            r"\bnext\b",
            r"\bwhat to do\b",
            r"\buser\b",
            r"\bconcise\b",
            r"\bmarkdown\b",
            r"\bcommand\b",
            r"\bpath\b",
        ],
    )

    dimensions = [
        _dimension(
            "Clarity",
            0 if empty else _score_from_hits(clarity_hits, 1, 3, 5),
            _evidence(
                clarity_hits,
                "The thread names goals, requirements, plans, or success conditions.",
                "The goal is not explicit enough to judge the outcome confidently.",
            ),
            "Restate the user's real goal and success condition before judging the work.",
        ),
        _dimension(
            "Grounding",
            0 if empty else _score_from_hits(grounding_hits, 1, 3, 6),
            _evidence(
                grounding_hits,
                "The agent inspected files, commands, diffs, or state before deciding.",
                "There is little evidence that the agent inspected the relevant state.",
            ),
            "Add concrete receipts: files inspected, commands run, screenshots, citations, or diffs.",
        ),
        _dimension(
            "Execution",
            0 if empty else _score_from_hits(execution_hits, 1, 3, 6),
            _evidence(
                execution_hits,
                "The thread shows concrete progress through edits, commands, tests, or verification.",
                "The thread mostly discusses intent instead of showing completed work.",
            ),
            "Make the next response action-oriented: change the artifact, run the check, and report the result.",
        ),
        _dimension(
            "User Fit",
            0 if empty else _score_from_hits(fit_hits, 1, 3, 5),
            _evidence(
                fit_hits,
                "The handoff is oriented toward what the user can understand or do next.",
                "The handoff does not yet make the result easy for the user to apply.",
            ),
            "Lead with the outcome, the top fixes, and one concrete next command or prompt.",
        ),
    ]

    if empty:
        dimensions[0]["evidence"] = ["No conversation text was available to evaluate."]
        dimensions[0]["fix"] = "Pass a transcript file, pipe text on stdin, or set CODEX_EVALS_CURRENT_THREAD."

    return _result(
        result_type="conversation",
        subject="Current conversation" if source == "current thread" else "Conversation",
        dimensions=dimensions,
        input_source=source,
        next_action="Run `/eval fix-first` to focus on the highest-leverage improvement.",
    )


def evaluate_skill(path: str | Path) -> dict[str, Any]:
    skill_path = Path(path)
    if skill_path.is_dir():
        skill_path = skill_path / "SKILL.md"

    if not skill_path.exists():
        dimensions = [
            _dimension("Clarity", 0, [f"No SKILL.md found at {skill_path}."], "Point the command at a valid SKILL.md file."),
            _dimension("Grounding", 0, ["The skill file could not be inspected."], "Create or select the skill before evaluating it."),
            _dimension("Execution", 0, ["No workflow could be evaluated."], "Add a workflow with concrete steps."),
            _dimension("User Fit", 0, ["No output guidance could be evaluated."], "Add a clear output shape."),
            _dimension("Craft", 0, ["Triggers, workflow, boundaries, and outputs are unavailable."], "Create the skill skeleton first."),
        ]
        return _result(
            result_type="skill",
            subject=str(skill_path),
            dimensions=dimensions,
            input_source=str(skill_path),
            next_action=f"Create {skill_path} or run `codex-evals skill <path> --format markdown` on an existing skill.",
        )

    text = skill_path.read_text(encoding="utf-8")
    frontmatter = _frontmatter(text)
    body = _body_without_frontmatter(text)

    has_name = bool(frontmatter.get("name"))
    description = frontmatter.get("description", "")
    has_trigger = bool(re.search(r"\b(use when|trigger|asks?|requested|should be used)\b", description, re.I))
    has_workflow = bool(re.search(r"\b(workflow|quick start|steps?|process|checklist)\b", body, re.I)) or bool(re.search(r"^\s*\d+\.", body, re.M))
    has_boundaries = bool(re.search(r"\b(do not|avoid|only|never|ask before|fallback|blocked)\b", body, re.I))
    has_outputs = bool(re.search(r"\b(output|final|report|include|deliver|markdown|json|what to do next)\b", body, re.I))
    has_validation = bool(re.search(r"\b(validate|verification|test|dry run|check|render|inspect)\b", body, re.I))
    has_references = bool(re.search(r"\b(references?/|scripts?/|assets?/|SKILL\.md|files?|state)\b", body, re.I))

    clarity_score = _score_booleans([has_name, 40 <= len(description) <= 500, has_trigger])
    grounding_score = _score_booleans([has_validation, has_references, bool(re.search(r"\binspect|read|source|evidence|receipt\b", body, re.I))])
    execution_score = _score_booleans([has_workflow, bool(re.search(r"\b(run|create|edit|use|open|write|review|score)\b", body, re.I)), has_validation])
    user_fit_score = _score_booleans([has_outputs, bool(re.search(r"\bconcise|short|lead with|user|next\b", body, re.I)), has_boundaries])
    craft_score = _score_booleans([has_trigger, has_workflow, has_boundaries, has_outputs])

    dimensions = [
        _dimension(
            "Clarity",
            clarity_score,
            _bool_evidence(
                [
                    (has_name, "Frontmatter includes a skill name."),
                    (40 <= len(description) <= 500, "Description is specific enough for routing."),
                    (has_trigger, "Description names when the skill should trigger."),
                ]
            ),
            "Tighten the frontmatter description around observable user requests and concrete trigger conditions.",
        ),
        _dimension(
            "Grounding",
            grounding_score,
            _bool_evidence(
                [
                    (has_validation, "The skill includes validation or checking guidance."),
                    (has_references, "The skill mentions files, state, scripts, or references to inspect."),
                    (bool(re.search(r"\binspect|read|source|evidence|receipt\b", body, re.I)), "The skill asks the agent to ground decisions in evidence."),
                ]
            ),
            "Add the exact files, state, receipts, or validation checks the agent should inspect before deciding.",
        ),
        _dimension(
            "Execution",
            execution_score,
            _bool_evidence(
                [
                    (has_workflow, "The skill has a workflow, quick start, or ordered process."),
                    (bool(re.search(r"\b(run|create|edit|use|open|write|review|score)\b", body, re.I)), "The instructions use action verbs."),
                    (has_validation, "The workflow includes a verification step."),
                ]
            ),
            "Convert broad advice into a short ordered workflow with a verification step at the end.",
        ),
        _dimension(
            "User Fit",
            user_fit_score,
            _bool_evidence(
                [
                    (has_outputs, "The skill describes the expected output or report shape."),
                    (bool(re.search(r"\bconcise|short|lead with|user|next\b", body, re.I)), "The skill includes user-facing handoff guidance."),
                    (has_boundaries, "The skill includes boundaries or fallback behavior."),
                ]
            ),
            "Define the final response shape and the one next action the user should see.",
        ),
        _dimension(
            "Craft",
            craft_score,
            _bool_evidence(
                [
                    (has_trigger, "Trigger conditions are present."),
                    (has_workflow, "Workflow guidance is present."),
                    (has_boundaries, "Boundaries are present."),
                    (has_outputs, "Output expectations are present."),
                ]
            ),
            "Sharpen triggers, workflow, boundaries, and outputs until each is observable in a dry run.",
        ),
    ]

    if all(dimension["score"] == dimension["max_score"] for dimension in dimensions):
        next_action = f"Save a baseline with `codex-evals skill {skill_path} --format json`, then rerun after the next edit."
    else:
        next_action = f"Revise the lowest-scoring dimension, then rerun `codex-evals skill {skill_path} --format markdown`."

    return _result(
        result_type="skill",
        subject=frontmatter.get("name") or skill_path.stem,
        dimensions=dimensions,
        input_source=str(skill_path),
        next_action=next_action,
    )


def evaluate_plugin(path: str | Path) -> dict[str, Any]:
    plugin_path = Path(path)
    plugin_root = plugin_path
    if plugin_path.name == "plugin.json":
        plugin_root = plugin_path.parent.parent
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    command_path = plugin_root / "commands" / "eval.md"
    skill_paths = sorted(plugin_root.glob("skills/*/SKILL.md"))

    if not manifest_path.exists():
        dimensions = [
            _dimension("Clarity", 0, [f"No plugin manifest found at {manifest_path}."], "Add `.codex-plugin/plugin.json`."),
            _dimension("Grounding", 0, ["Plugin files could not be inspected."], "Add command and skill files before evaluating the plugin."),
            _dimension("Execution", 0, ["No command entrypoint was found."], "Add `commands/eval.md`."),
            _dimension("User Fit", 0, ["No user-facing plugin metadata was found."], "Add interface metadata and default prompts."),
            _dimension("Craft", 0, ["No plugin command/skill structure was found."], "Add command docs and evaluation skills."),
        ]
        return _result(
            result_type="plugin",
            subject=str(plugin_root),
            dimensions=dimensions,
            input_source=str(plugin_root),
            next_action="Create a plugin manifest, command entrypoint, and evaluation skills.",
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_valid = True
    except json.JSONDecodeError:
        manifest = {}
        manifest_valid = False

    command_text = command_path.read_text(encoding="utf-8") if command_path.exists() else ""
    skill_names = {path.parent.name for path in skill_paths}
    interface = manifest.get("interface", {}) if isinstance(manifest, dict) else {}

    has_modes = all(token in command_text for token in ["/eval", "skill", "bundle", "why", "fix-first"])
    has_required_skills = {"evaluate-conversation", "evaluate-skill", "evaluate-bundle"}.issubset(skill_names)
    has_user_metadata = bool(interface.get("displayName")) and bool(interface.get("shortDescription"))
    has_default_prompts = bool(interface.get("defaultPrompt"))

    dimensions = [
        _dimension(
            "Clarity",
            _score_booleans([manifest_valid, bool(manifest.get("name")), bool(manifest.get("description")), has_user_metadata]),
            _bool_evidence(
                [
                    (manifest_valid, "Plugin manifest is valid JSON."),
                    (bool(manifest.get("name")), "Plugin has a stable name."),
                    (bool(manifest.get("description")), "Plugin describes its purpose."),
                    (has_user_metadata, "Plugin has user-facing display metadata."),
                ]
            ),
            "Tighten plugin metadata so the user can understand the surface before installing or invoking it.",
        ),
        _dimension(
            "Grounding",
            _score_booleans(
                [
                    bool(re.search(r"\bevidence|receipts?|traceable\b", command_text, re.I)),
                    bool(re.search(r"\bfiles?|state|commands?|reports?\b", command_text, re.I)),
                    has_required_skills,
                ]
            ),
            _bool_evidence(
                [
                    (bool(re.search(r"\bevidence|receipts?|traceable\b", command_text, re.I)), "Command docs require evidence-backed scoring."),
                    (bool(re.search(r"\bfiles?|state|commands?|reports?\b", command_text, re.I)), "Command docs mention local state or report inputs."),
                    (has_required_skills, "Plugin includes the expected evaluation skills."),
                ]
            ),
            "Make the command docs explicit about which receipts and local state should ground the score.",
        ),
        _dimension(
            "Execution",
            _score_booleans([command_path.exists(), has_modes, has_required_skills]),
            _bool_evidence(
                [
                    (command_path.exists(), "Plugin has `commands/eval.md`."),
                    (has_modes, "Command docs cover no-arg, skill, bundle, why, and fix-first modes."),
                    (has_required_skills, "Plugin has conversation, skill, and bundle evaluation skills."),
                ]
            ),
            "Ensure the slash-command entrypoint maps each mode to a concrete skill or CLI path.",
        ),
        _dimension(
            "User Fit",
            _score_booleans(
                [
                    has_default_prompts,
                    bool(re.search(r"\bshort|concise|conversational|do not ask\b", command_text, re.I)),
                    bool(re.search(r"\bMarkdown|what to do next|fix-first\b", command_text, re.I)),
                ]
            ),
            _bool_evidence(
                [
                    (has_default_prompts, "Plugin includes default prompts."),
                    (bool(re.search(r"\bshort|concise|conversational|do not ask\b", command_text, re.I)), "Command docs protect the low-friction UX."),
                    (bool(re.search(r"\bMarkdown|what to do next|fix-first\b", command_text, re.I)), "Command docs define a user-friendly report shape."),
                ]
            ),
            "Keep the default response short and make deeper diagnostics opt-in.",
        ),
        _dimension(
            "Craft",
            _score_booleans([manifest_valid, command_path.exists(), has_required_skills, has_modes]),
            _bool_evidence(
                [
                    (manifest_valid, "Manifest is parseable."),
                    (command_path.exists(), "Command entrypoint is present."),
                    (has_required_skills, "Required skills are present."),
                    (has_modes, "Command modes are documented."),
                ]
            ),
            "Keep plugin metadata, command docs, and skills synchronized as modes are added.",
        ),
    ]

    return _result(
        result_type="plugin",
        subject=manifest.get("name") or plugin_root.name,
        dimensions=dimensions,
        input_source=str(plugin_root),
        next_action=f"Rerun `codex-evals bundle --skill <path> --format markdown` after plugin changes.",
    )


def evaluate_bundle(
    conversation_text: str,
    *,
    root: str | Path = ".",
    skill_paths: list[str | Path] | None = None,
    source: str = "current thread",
) -> dict[str, Any]:
    root_path = Path(root)
    discovered = skill_paths or discover_related_skills(root_path)
    discovered_plugins = discover_related_plugins(root_path)
    conversation = evaluate_conversation(conversation_text, source=source)
    skills = [evaluate_skill(path) for path in discovered]
    plugins = [evaluate_plugin(path) for path in discovered_plugins]

    dimensions = []
    for name in ["Clarity", "Grounding", "Execution", "User Fit"]:
        values = [_dimension_by_name(conversation, name)]
        values.extend(_dimension_by_name(skill, name) for skill in skills)
        values.extend(_dimension_by_name(plugin, name) for plugin in plugins)
        dimensions.append(_merge_dimension(name, values))

    craft_values = [_dimension_by_name(skill, "Craft") for skill in skills]
    craft_values.extend(_dimension_by_name(plugin, "Craft") for plugin in plugins)
    if craft_values:
        dimensions.append(_merge_dimension("Craft", craft_values))
    else:
        dimensions.append(
            _dimension(
                "Craft",
                1,
                ["No related created or edited SKILL.md files were detected."],
                "Pass one or more skill paths, or run from a git worktree with changed plugin/skill files.",
            )
        )

    result = _result(
        result_type="bundle",
        subject="Current conversation and related skills/plugins",
        dimensions=dimensions,
        input_source=source,
        next_action="Run `/eval fix-first`, apply the top fix, then rerun `/eval bundle`.",
    )
    result["components"] = {
        "conversation": conversation,
        "skills": skills,
        "plugins": plugins,
        "related_skill_paths": [str(path) for path in discovered],
        "related_plugin_paths": [str(path) for path in discovered_plugins],
    }
    return result


def discover_related_skills(root: str | Path = ".") -> list[Path]:
    root_path = Path(root)
    paths: set[Path] = set()

    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root_path,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        proc = None

    if proc and proc.stdout:
        for line in proc.stdout.splitlines():
            candidate = line[3:].strip()
            if " -> " in candidate:
                candidate = candidate.split(" -> ", 1)[1]
            path = root_path / candidate
            if path.name == "SKILL.md" and "skills" in path.parts:
                paths.add(path)

    if not paths:
        for path in root_path.glob("plugins/*/skills/*/SKILL.md"):
            paths.add(path)
        for path in root_path.glob("skills/*/SKILL.md"):
            paths.add(path)

    return sorted(paths)


def discover_related_plugins(root: str | Path = ".") -> list[Path]:
    root_path = Path(root)
    paths: set[Path] = set()

    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root_path,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        proc = None

    if proc and proc.stdout:
        for line in proc.stdout.splitlines():
            candidate = line[3:].strip()
            if " -> " in candidate:
                candidate = candidate.split(" -> ", 1)[1]
            path = root_path / candidate
            parts = path.parts
            if ".codex-plugin" in parts or ("plugins" in parts and len(parts) >= 2):
                plugin_root = _plugin_root_from_path(path, root_path)
                manifest = plugin_root / ".codex-plugin" / "plugin.json"
                if manifest.exists():
                    paths.add(plugin_root)

    if not paths:
        for manifest in root_path.glob("plugins/*/.codex-plugin/plugin.json"):
            paths.add(manifest.parent.parent)

    return sorted(paths)


def read_current_thread(root: str | Path = ".") -> tuple[str, str]:
    inline = os.environ.get("CODEX_EVALS_THREAD_TEXT")
    if inline:
        return inline, "current thread"

    candidates = []
    env_path = os.environ.get("CODEX_EVALS_CURRENT_THREAD")
    if env_path:
        candidates.append(Path(env_path))
    root_path = Path(root)
    candidates.extend(
        [
            root_path / ".codex-evals" / "current-thread.md",
            root_path / "current-thread.md",
        ]
    )

    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8"), "current thread"

    return "", "current thread"


def _plugin_root_from_path(path: Path, root: Path) -> Path:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return path
    parts = relative.parts
    if len(parts) >= 2 and parts[0] == "plugins":
        return root / parts[0] / parts[1]
    return path.parent


def load_result(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _result(
    *,
    result_type: str,
    subject: str,
    dimensions: list[dict[str, Any]],
    input_source: str,
    next_action: str,
) -> dict[str, Any]:
    total = sum(item["score"] for item in dimensions)
    max_score = sum(item["max_score"] for item in dimensions)
    grade = _grade(total, max_score)
    fixes = _top_fixes(dimensions)
    signals = _top_signals(dimensions)

    return {
        "version": RESULT_VERSION,
        "type": result_type,
        "subject": subject,
        "overall": {
            "grade": grade,
            "score": total,
            "max_score": max_score,
            "verdict": _verdict(grade),
        },
        "strongest_signals": signals,
        "highest_impact_fixes": fixes,
        "what_to_do_next": next_action,
        "dimensions": dimensions,
        "evidence": {
            "input_source": input_source,
        },
    }


def _dimension(name: str, score: int, evidence: list[str], fix: str) -> dict[str, Any]:
    return {
        "name": name,
        "score": max(0, min(SCORE_MAX, int(score))),
        "max_score": SCORE_MAX,
        "evidence": evidence[:3] or ["No supporting evidence found."],
        "fix": fix,
    }


def _merge_dimension(name: str, values: list[dict[str, Any]]) -> dict[str, Any]:
    if not values:
        return _dimension(name, 0, ["No component scores were available."], "Add an evaluable component.")
    score = round(mean(value["score"] for value in values))
    evidence = []
    for value in sorted(values, key=lambda item: item["score"], reverse=True):
        if value["score"] <= 0 and evidence:
            continue
        evidence.extend(value.get("evidence", [])[:1])
    lowest = sorted(values, key=lambda item: item["score"])[0]
    return _dimension(name, score, evidence[:3], lowest.get("fix", "Improve this dimension."))


def _dimension_by_name(result: dict[str, Any], name: str) -> dict[str, Any]:
    for dimension in result["dimensions"]:
        if dimension["name"] == name:
            return dimension
    return _dimension(name, 0, ["Dimension was not present."], "Add this dimension to the evaluation.")


def _score_from_hits(count: int, low: int, medium: int, high: int) -> int:
    if count >= high:
        return 3
    if count >= medium:
        return 2
    if count >= low:
        return 1
    return 0


def _score_booleans(values: list[bool]) -> int:
    count = sum(1 for value in values if value)
    if not values or count == 0:
        return 0
    ratio = count / len(values)
    if ratio >= 0.8:
        return 3
    if ratio >= 0.5:
        return 2
    return 1


def _count_hits(text: str, patterns: list[str]) -> int:
    return sum(len(re.findall(pattern, text, flags=re.I)) for pattern in patterns)


def _evidence(count: int, positive: str, negative: str) -> list[str]:
    if count:
        return [positive, f"Matched {count} supporting signal{'s' if count != 1 else ''}."]
    return [negative]


def _bool_evidence(items: list[tuple[bool, str]]) -> list[str]:
    evidence = [message for passed, message in items if passed]
    missing = [message for passed, message in items if not passed]
    if evidence:
        return evidence
    return [f"Missing: {missing[0]}" if missing else "No supporting evidence found."]


def _top_signals(dimensions: list[dict[str, Any]]) -> list[str]:
    ordered = sorted(dimensions, key=lambda item: item["score"], reverse=True)
    signals = []
    for item in ordered:
        if item["score"] > 0:
            signals.append(f"{item['name']}: {item['evidence'][0]}")
    return _pad_three(signals, "No strong signal found yet.")


def _top_fixes(dimensions: list[dict[str, Any]]) -> list[str]:
    if all(item["score"] >= item["max_score"] for item in dimensions):
        return [
            "Preserve the current report shape and rerun after the next material change.",
            "Add one realistic dry-run receipt so future reviewers can compare behavior.",
            "Keep Markdown and JSON outputs aligned as the evaluator evolves.",
        ]
    ordered = sorted(dimensions, key=lambda item: item["score"])
    fixes = [f"{item['name']}: {item['fix']}" for item in ordered if item["score"] < item["max_score"]]
    return _pad_three(fixes, "Keep the current report shape and rerun after the next change.")


def _pad_three(items: list[str], fallback: str) -> list[str]:
    trimmed = [item for item in items if item][:3]
    while len(trimmed) < 3:
        trimmed.append(fallback)
    return trimmed


def _grade(score: int, max_score: int) -> str:
    if max_score <= 0:
        return "F"
    ratio = score / max_score
    if ratio >= 0.85:
        return "A"
    if ratio >= 0.70:
        return "B"
    if ratio >= 0.55:
        return "C"
    if ratio >= 0.40:
        return "D"
    return "F"


def _verdict(grade: str) -> str:
    if grade in {"A", "B"}:
        return "Pass"
    if grade == "C":
        return "Needs work"
    return "Fail"


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    result: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def _body_without_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    return parts[2]
