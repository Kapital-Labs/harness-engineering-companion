"""Run a scripted fixture by default; --live opts into a remote model."""

import argparse
from dataclasses import asdict
import json
import os

from harness import Final, SnapshotTools, ToolCall, run


# These are synthetic strings, not files loaded from the reader's machine.
FILES = {
    "tracker/policy.py": (
        '"""Permissions for the sample issue tracker."""\n'
        '\n'
        'def can_close_issue(role: str) -> bool:\n'
        '    return role == "maintainer"\n'
    ),
    "tracker/views.py": (
        'from tracker.policy import can_close_issue\n'
        '\n'
        'def close_button_enabled(role: str) -> bool:\n'
        '    return can_close_issue(role)\n'
    ),
}
TASK = "Who can close an issue? Find the policy and cite its file and lines."


class ScriptedModel:
    """A teaching fixture: it exercises the loop but has no learned behavior."""

    def next(self, task, events):
        results = [e.data["result"] for e in events if e.kind == "tool_result"]
        if not results:
            return ToolCall("search-1", "search", {"query": "can_close_issue"})
        if not results[-1]["ok"]:
            return Final("The requested sample evidence is unavailable.")
        if len(results) == 1:
            matches = results[-1]["data"]["matches"]
            definition = next(m for m in matches if "def " in m["text"])
            return ToolCall("read-1", "read_file", {"path": definition["path"]})
        data = results[-1]["data"]
        if 'return role == "maintainer"' not in data["text"]:
            return Final("The sample policy differs from the expected fixture.")
        return Final(
            "The policy permits the maintainer role to close an issue "
            f"({data['path']}:3-4). This identifies the policy; it does not "
            "prove that every application entry point enforces it."
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--model", help="Exact model ID available to your account")
    parser.add_argument("--max-steps", type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.max_steps <= 100:
        parser.error("--max-steps must be between 1 and 100")
    if args.live:
        from anthropic_adapter import AnthropicModel
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not args.model or not key:
            parser.error("--live requires --model and ANTHROPIC_API_KEY")
        model = AnthropicModel(args.model, key)
    else:
        model = ScriptedModel()
    result = run(model, SnapshotTools(FILES), TASK, max_steps=args.max_steps)
    print(json.dumps({"mode": "live" if args.live else "scripted",
                      **asdict(result)}, indent=2))
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
