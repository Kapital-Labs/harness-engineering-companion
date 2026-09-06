"""Compare offline controls by default. --candidate live makes billable calls."""

import argparse
import json
import os
from chapter2 import AnthropicModel
from candidates import FixedPolicyWorkflow, ReplayCandidate
from evaluation import evaluate
from tasks import TASKS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=["compare", "baseline", "scripted", "live"], default="compare")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--model")
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.repeats <= 100:
        parser.error("--repeats must be between 1 and 100")
    choices = []
    if args.candidate in {"compare", "baseline"}:
        choices.append(("fixed_baseline", lambda _: FixedPolicyWorkflow()))
    if args.candidate in {"compare", "scripted"}:
        choices.append(("scripted_fixture", ReplayCandidate))
    if args.candidate == "live":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key or not args.model:
            parser.error("live requires --model and ANTHROPIC_API_KEY")
        choices.append(("live", lambda _: AnthropicModel(args.model, key)))
    reports = []
    for kind, factory in choices:
        report = evaluate(TASKS, factory, kind, args.repeats)
        report["model_id"] = args.model if kind == "live" else None
        reports.append(report)
    print(json.dumps({"reports": reports}, indent=2))
    failed = any(r["summary"]["passed"] < r["summary"]["trials"] for r in reports)
    return 1 if args.require_pass and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
