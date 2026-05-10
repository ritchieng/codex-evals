from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .evaluator import (
    evaluate_bundle,
    evaluate_conversation,
    evaluate_skill,
    load_result,
    read_current_thread,
)
from .onboarding import build_doctor, init_onboarding, render_onboarding, run_demo
from .render import render_result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "conversation":
        text, source = _read_conversation_input(args)
        result = evaluate_conversation(text, source=source)
    elif args.command == "skill":
        result = evaluate_skill(args.path)
    elif args.command == "bundle":
        text, source = _read_conversation_input(args)
        result = evaluate_bundle(text, root=args.root, skill_paths=args.skill, source=source)
    elif args.command == "report":
        result = load_result(args.path)
    elif args.command == "demo":
        sys.stdout.write(run_demo(output_format=args.format))
        return 0
    elif args.command == "doctor":
        result = build_doctor(args.root)
        sys.stdout.write(render_onboarding(result, output_format=args.format))
        return 0
    elif args.command == "init":
        sys.stdout.write(
            init_onboarding(
                root=args.root,
                output_format=args.format,
                install_plugin=not args.no_install_plugin,
                write_demo_file=not args.no_demo_file,
            )
        )
        return 0
    else:
        parser.print_help(sys.stderr)
        return 2

    sys.stdout.write(render_result(result, output_format=args.format))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-evals",
        description="Evaluate Codex conversations, skills, and bundles with a concise local report.",
    )
    subparsers = parser.add_subparsers(dest="command")

    conversation = subparsers.add_parser("conversation", help="Evaluate a conversation transcript.")
    _add_conversation_input_args(conversation)
    _add_format_arg(conversation)

    skill = subparsers.add_parser("skill", help="Evaluate a SKILL.md file or skill directory.")
    skill.add_argument("path", help="Path to SKILL.md or a skill directory.")
    _add_format_arg(skill)

    bundle = subparsers.add_parser("bundle", help="Evaluate a conversation plus related skills/plugins.")
    _add_conversation_input_args(bundle)
    bundle.add_argument("--root", default=".", help="Repo root for discovering changed skills. Defaults to current directory.")
    bundle.add_argument("--skill", action="append", help="Related SKILL.md or skill directory. Can be repeated.")
    _add_format_arg(bundle)

    report = subparsers.add_parser("report", help="Render a saved JSON result.")
    report.add_argument("path", help="Path to result.json.")
    _add_format_arg(report)

    demo = subparsers.add_parser("demo", help="Render a built-in sample report so users can see the product immediately.")
    _add_format_arg(demo)

    doctor = subparsers.add_parser("doctor", help="Check CLI, plugin, command, skills, and current-thread readiness.")
    doctor.add_argument("--root", default=".", help="Repo root to inspect. Defaults to current directory.")
    _add_format_arg(doctor)

    init = subparsers.add_parser("init", help="Run first-time onboarding and create local setup hints.")
    init.add_argument("--root", default=".", help="Repo root to initialize. Defaults to current directory.")
    init.add_argument("--no-install-plugin", action="store_true", help="Do not try to create a repo-local marketplace entry.")
    init.add_argument("--no-demo-file", action="store_true", help="Do not write `.codex-evals/onboarding-thread.md`.")
    _add_format_arg(init)

    return parser


def _add_conversation_input_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", nargs="?", help="Transcript file. Use '-' to read from stdin.")
    parser.add_argument("--current", action="store_true", help="Read the current thread from local Codex eval context.")
    parser.add_argument("--stdin", action="store_true", help="Read the transcript from stdin.")


def _add_format_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format. Defaults to markdown.")


def _read_conversation_input(args: argparse.Namespace) -> tuple[str, str]:
    if getattr(args, "stdin", False) or getattr(args, "path", None) == "-":
        return sys.stdin.read(), "stdin"
    if getattr(args, "path", None):
        path = Path(args.path)
        return path.read_text(encoding="utf-8"), str(path)
    if getattr(args, "current", False):
        return read_current_thread(getattr(args, "root", "."))
    return "", "provided text"


if __name__ == "__main__":
    raise SystemExit(main())
