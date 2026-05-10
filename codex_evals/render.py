from __future__ import annotations

import json
from typing import Any


def render_result(result: dict[str, Any], *, output_format: str = "markdown") -> str:
    if output_format == "json":
        return json.dumps(result, indent=2, sort_keys=True)
    if output_format != "markdown":
        raise ValueError(f"Unsupported format: {output_format}")
    return render_markdown(result)


def render_markdown(result: dict[str, Any]) -> str:
    overall = result["overall"]
    lines = [
        "# Eval Report",
        "",
        f"**Overall grade:** {overall['grade']} ({overall['score']}/{overall['max_score']})",
        f"**Verdict:** {overall['verdict']}",
        f"**Scope:** {result['type']} - {result['subject']}",
    ]
    if "components" in result:
        components = result["components"]
        lines.append(f"**Related skills:** {len(components.get('related_skill_paths', []))}")
        lines.append(f"**Related plugins:** {len(components.get('related_plugin_paths', []))}")
    lines.extend(["", "## 3 Strongest Signals"])
    lines.extend(_numbered(result["strongest_signals"]))
    lines.extend(["", "## 3 Highest-Impact Fixes"])
    lines.extend(_numbered(result["highest_impact_fixes"]))
    lines.extend(["", "## What To Do Next", "", result["what_to_do_next"], "", "## Scorecard", ""])
    lines.append("| Dimension | Score | Evidence |")
    lines.append("| --- | ---: | --- |")
    for dimension in result["dimensions"]:
        evidence = " ".join(dimension["evidence"]).replace("\n", " ")
        lines.append(f"| {dimension['name']} | {dimension['score']}/{dimension['max_score']} | {evidence} |")
    return "\n".join(lines).rstrip() + "\n"


def _numbered(items: list[str]) -> list[str]:
    return [f"{index}. {item}" for index, item in enumerate(items[:3], start=1)]
