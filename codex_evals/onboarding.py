from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import __version__
from .evaluator import evaluate_conversation, read_current_thread
from .render import render_result

PLUGIN_NAME = "codex-evals"
REQUIRED_SKILLS = ["evaluate-conversation", "evaluate-skill", "evaluate-bundle"]
DEMO_TRANSCRIPT = """User: Goal: make /eval tell me what just happened and what to improve.
User: Success means a low-friction command, clear requirements, and a report users can understand.
Assistant: I restated the objective, made a plan, and used a checklist before editing.
Assistant: I ran rg, sed, git status, and git diff, then read README.md, codex_evals/cli.py, and plugins/codex-evals/commands/eval.md.
Assistant: I inspected the relevant plugin files and verified the local state before deciding.
Assistant: I implemented the CLI, created the plugin command, updated skills, added tests, and ran the test command.
Assistant: Tests passed. The final Markdown answer was concise, named the changed path, and gave the next command for the user.
"""


def run_demo(*, output_format: str = "markdown") -> str:
    result = evaluate_conversation(DEMO_TRANSCRIPT, source="demo transcript")
    return render_result(result, output_format=output_format)


def init_onboarding(
    *,
    root: str | Path = ".",
    output_format: str = "markdown",
    install_plugin: bool = True,
    write_demo_file: bool = True,
) -> str:
    root_path = Path(root).resolve()
    setup_actions = []

    if write_demo_file:
        demo_path = root_path / ".codex-evals" / "onboarding-thread.md"
        try:
            demo_path.parent.mkdir(parents=True, exist_ok=True)
            demo_path.write_text(DEMO_TRANSCRIPT, encoding="utf-8")
            setup_actions.append(
                _check(
                    "Demo transcript",
                    "ok",
                    f"Wrote {demo_path.relative_to(root_path)}.",
                    f"Run `codex-evals conversation {demo_path} --format markdown`.",
                )
            )
        except OSError as exc:
            setup_actions.append(
                _check(
                    "Demo transcript",
                    "warn",
                    f"Could not write `.codex-evals/onboarding-thread.md`: {exc}.",
                    "Run `codex-evals demo` instead.",
                )
            )

    if install_plugin:
        setup_actions.append(ensure_repo_marketplace(root_path))
    else:
        setup_actions.append(
            _check(
                "Plugin registration",
                "warn",
                "Skipped by request.",
                "Run `codex-evals init` without `--no-install-plugin` to try local registration.",
            )
        )

    report = build_doctor(root_path)
    report["setup_actions"] = setup_actions
    report["headline"] = _headline(report)
    return render_onboarding(report, output_format=output_format)


def build_doctor(root: str | Path = ".") -> dict[str, Any]:
    root_path = Path(root).resolve()
    plugin_root = root_path / "plugins" / PLUGIN_NAME
    command_path = plugin_root / "commands" / "eval.md"
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    checks = [
        _check("CLI package", "ok", f"codex-evals {__version__} is importable.", "Optional: run `python3 -m pip install -e .` to install the command name."),
        _file_check("Plugin manifest", manifest_path, "Add `plugins/codex-evals/.codex-plugin/plugin.json`."),
        _json_check("Plugin JSON", manifest_path, "Fix invalid JSON in the plugin manifest."),
        _file_check("/eval command", command_path, "Add `plugins/codex-evals/commands/eval.md`."),
    ]

    for skill_name in REQUIRED_SKILLS:
        skill_path = plugin_root / "skills" / skill_name / "SKILL.md"
        checks.append(_file_check(f"Skill: {skill_name}", skill_path, f"Add `{skill_path}`."))
        checks.append(_skill_frontmatter_check(skill_name, skill_path))

    checks.append(_report_engine_check())
    checks.append(_current_thread_check(root_path))
    checks.append(_packaged_marketplace_check(root_path))
    checks.append(_marketplace_check(root_path))

    return {
        "status": _overall_status(checks),
        "headline": "",
        "root": str(root_path),
        "checks": checks,
        "next_steps": _next_steps(checks),
    }


def ensure_repo_marketplace(root: str | Path = ".") -> dict[str, str]:
    root_path = Path(root).resolve()
    marketplace_path = root_path / ".agents" / "plugins" / "marketplace.json"
    entry = {
        "name": PLUGIN_NAME,
        "source": {
            "source": "local",
            "path": "./plugins/codex-evals",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }

    try:
        if marketplace_path.exists():
            payload = json.loads(marketplace_path.read_text(encoding="utf-8"))
        else:
            payload = {
                "name": "local-codex-evals",
                "interface": {"displayName": "Local Codex Evals"},
                "plugins": [],
            }
        plugins = payload.setdefault("plugins", [])
        replaced = False
        for index, existing in enumerate(plugins):
            if existing.get("name") == PLUGIN_NAME:
                plugins[index] = entry
                replaced = True
                break
        if not replaced:
            plugins.append(entry)
        marketplace_path.parent.mkdir(parents=True, exist_ok=True)
        marketplace_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        return _check(
            "Plugin registration",
            "warn",
            f"Could not write {marketplace_path}: {exc}.",
            "Manually register `plugins/codex-evals` as a local Codex plugin, then run `/eval`.",
        )
    except json.JSONDecodeError as exc:
        return _check(
            "Plugin registration",
            "fail",
            f"Marketplace JSON is invalid: {exc}.",
            f"Fix {marketplace_path}, then rerun `codex-evals init`.",
        )

    return _check(
        "Plugin registration",
        "ok",
        f"Registered {PLUGIN_NAME} in {marketplace_path}.",
        "Open Codex and run `/eval`.",
    )


def render_onboarding(report: dict[str, Any], *, output_format: str = "markdown") -> str:
    if output_format == "json":
        return json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output_format != "markdown":
        raise ValueError(f"Unsupported format: {output_format}")

    lines = [
        "# codex-evals Onboarding",
        "",
        f"**Status:** {report['status']}",
    ]
    if report.get("headline"):
        lines.append(f"**Summary:** {report['headline']}")
    lines.extend(["", "## Checks", "", "| Check | Status | Detail | Next fix |", "| --- | --- | --- | --- |"])
    for check in report["checks"]:
        lines.append(f"| {check['name']} | {check['status']} | {check['detail']} | {check['fix']} |")

    if report.get("setup_actions"):
        lines.extend(["", "## Setup Actions", "", "| Action | Status | Detail | Next fix |", "| --- | --- | --- | --- |"])
        for check in report["setup_actions"]:
            lines.append(f"| {check['name']} | {check['status']} | {check['detail']} | {check['fix']} |")

    lines.extend(["", "## Try It Now"])
    for index, step in enumerate(report["next_steps"], start=1):
        lines.append(f"{index}. {step}")
    return "\n".join(lines).rstrip() + "\n"


def _headline(report: dict[str, Any]) -> str:
    if report["status"] == "ready":
        return "You can run `codex-evals demo` now, then open Codex and run `/eval`."
    return "The CLI can run, but one or more setup checks need attention."


def _file_check(name: str, path: Path, fix: str) -> dict[str, str]:
    if path.exists():
        return _check(name, "ok", f"Found {path}.", "No action needed.")
    return _check(name, "fail", f"Missing {path}.", fix)


def _json_check(name: str, path: Path, fix: str) -> dict[str, str]:
    if not path.exists():
        return _check(name, "fail", f"Missing {path}.", fix)
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _check(name, "fail", f"Invalid JSON: {exc}.", fix)
    return _check(name, "ok", "Manifest parses as JSON.", "No action needed.")


def _skill_frontmatter_check(skill_name: str, path: Path) -> dict[str, str]:
    if not path.exists():
        return _check(f"Skill metadata: {skill_name}", "fail", f"Missing {path}.", "Create the skill file.")
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return _check(f"Skill metadata: {skill_name}", "fail", "Missing YAML frontmatter.", "Add `name` and `description` frontmatter.")
    frontmatter = text.split("---", 2)[1]
    if "name:" not in frontmatter or "description:" not in frontmatter:
        return _check(f"Skill metadata: {skill_name}", "fail", "Missing `name` or `description`.", "Add both metadata fields.")
    return _check(f"Skill metadata: {skill_name}", "ok", "Frontmatter includes name and description.", "No action needed.")


def _report_engine_check() -> dict[str, str]:
    try:
        rendered = run_demo(output_format="markdown")
    except Exception as exc:  # pragma: no cover - defensive onboarding surface.
        return _check("Report engine", "fail", f"Demo report failed: {exc}.", "Run `python3 -m unittest` and fix the failing test.")
    if "## 3 Highest-Impact Fixes" not in rendered:
        return _check("Report engine", "fail", "Demo report rendered an unexpected shape.", "Check `codex_evals/render.py`.")
    return _check("Report engine", "ok", "Markdown and scorecard rendering work.", "Run `codex-evals demo`.")


def _current_thread_check(root: Path) -> dict[str, str]:
    text, source = read_current_thread(root)
    if text.strip():
        return _check("Current-thread bridge", "ok", f"Found current-thread input via {source}.", "Run `codex-evals conversation --current`.")
    return _check(
        "Current-thread bridge",
        "info",
        "No exported current-thread text found for CLI use.",
        "Use `/eval` inside Codex, pass a transcript file, or set `CODEX_EVALS_CURRENT_THREAD`.",
    )


def _marketplace_check(root: Path) -> dict[str, str]:
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    if not marketplace_path.exists():
        return _check(
            "Marketplace entry",
            "info",
            f"No repo-local marketplace file at {marketplace_path}.",
            "Run `codex-evals init` to try creating one, or register the plugin manually.",
        )
    try:
        payload = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _check("Marketplace entry", "fail", f"Invalid marketplace JSON: {exc}.", f"Fix {marketplace_path}.")
    plugins = payload.get("plugins", [])
    if any(plugin.get("name") == PLUGIN_NAME for plugin in plugins):
        return _check("Marketplace entry", "ok", f"{PLUGIN_NAME} is listed in {marketplace_path}.", "Open Codex and run `/eval`.")
    return _check("Marketplace entry", "info", f"{PLUGIN_NAME} is not listed in {marketplace_path}.", "Run `codex-evals init`.")


def _packaged_marketplace_check(root: Path) -> dict[str, str]:
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    if not marketplace_path.exists():
        return _check(
            "Packaged marketplace",
            "warn",
            "No `.agents/plugins/marketplace.json` found for Add Marketplace import.",
            "Add `.agents/plugins/marketplace.json` with a `./plugins/codex-evals` entry.",
        )
    try:
        payload = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _check("Packaged marketplace", "fail", f"Invalid marketplace JSON: {exc}.", "Fix `.agents/plugins/marketplace.json`.")
    plugins = payload.get("plugins", [])
    if any(plugin.get("name") == PLUGIN_NAME and plugin.get("source", {}).get("path") == "./plugins/codex-evals" for plugin in plugins):
        return _check(
            "Packaged marketplace",
            "ok",
            "`.agents/plugins/marketplace.json` exposes `plugins/codex-evals`.",
            "Use Add marketplace with this repo as Source.",
        )
    return _check(
        "Packaged marketplace",
        "fail",
        "`.agents/plugins/marketplace.json` does not expose `plugins/codex-evals`.",
        "Add a plugin entry whose source path is `./plugins/codex-evals`.",
    )


def _overall_status(checks: list[dict[str, str]]) -> str:
    if any(check["status"] == "fail" for check in checks):
        return "blocked"
    if any(check["status"] == "warn" for check in checks):
        return "needs attention"
    return "ready"


def _next_steps(checks: list[dict[str, str]]) -> list[str]:
    failing_or_warn = [check for check in checks if check["status"] in {"fail", "warn"}]
    if failing_or_warn:
        return [
            "Run `codex-evals demo` to see the report shape.",
            failing_or_warn[0]["fix"],
            "Open Codex and run `/eval` after the plugin is registered.",
        ]
    return [
        "Run `codex-evals demo`.",
        "Open Codex and run `/eval`.",
        "Run `/eval fix-first` after any substantial Codex session.",
    ]


def _check(name: str, status: str, detail: str, fix: str) -> dict[str, str]:
    return {
        "name": name,
        "status": status,
        "detail": detail,
        "fix": fix,
    }
