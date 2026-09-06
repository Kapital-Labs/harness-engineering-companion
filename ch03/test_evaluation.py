"""Tests for the evaluator's own acceptance boundary."""

import json
import unittest

from evaluation import grade, summarize, evaluate
from tasks import TASKS
from candidates import ReplayCandidate, FixedPolicyWorkflow
from chapter2 import Event, Final, RunResult, SnapshotTools, ToolCall, run


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.task = TASKS[0]

    def result(self, conclusion="maintainer_only", citations=None, read=True):
        if citations is None:
            citations = [{"path": "tracker/policy.py", "start": 3, "end": 4}]
        answer = json.dumps({"conclusion": conclusion, "citations": citations})
        actions = []
        if read:
            actions.append(ToolCall("read", "read_file", {"path": "tracker/policy.py"}))
        actions.append(Final(answer))

        class Sequence:
            def next(self, task, events):
                return actions.pop(0)

        return run(Sequence(), SnapshotTools(self.task.files), self.task.question)

    def test_correct_observed_evidence_passes(self):
        verdict = grade(self.task, self.result())
        self.assertTrue(verdict["passed"])
        self.assertTrue(all(verdict["checks"].values()))

    def test_completed_wrong_answer_fails(self):
        result = self.result(conclusion="administrator_only")
        self.assertEqual(result.status, "completed")
        verdict = grade(self.task, result)
        self.assertFalse(verdict["passed"])
        self.assertFalse(verdict["checks"]["correct_conclusion"])

    def test_existing_file_with_wrong_lines_is_not_support(self):
        verdict = grade(self.task, self.result(citations=[{
            "path": "tracker/policy.py", "start": 1, "end": 1,
        }]))
        self.assertTrue(verdict["checks"]["valid_citations"])
        self.assertFalse(verdict["checks"]["required_evidence"])
        self.assertFalse(verdict["passed"])

    def test_out_of_range_unknown_and_boolean_line_numbers_fail(self):
        for citation in (
            {"path": "tracker/policy.py", "start": 3, "end": 999},
            {"path": "unknown.py", "start": 1, "end": 1},
            {"path": "tracker/policy.py", "start": True, "end": 4},
            {"path": "tracker/policy.py", "start": 4, "end": 3},
        ):
            with self.subTest(citation=citation):
                self.assertFalse(grade(self.task, self.result(citations=[citation]))["passed"])

    def test_correct_citation_without_observation_fails(self):
        verdict = grade(self.task, self.result(read=False))
        self.assertFalse(verdict["checks"]["observed_evidence"])
        self.assertFalse(verdict["passed"])

    def test_complete_line_at_prefix_limit_uses_source_separator(self):
        from dataclasses import replace

        for separator in ('\n', '\r', '\r\n', '\u2028'):
            with self.subTest(separator=repr(separator)):
                definition = 'def can_close_issue(role):' + separator
                body = '    return role == "maintainer"'
                padding = '#' + 'x' * (
                    2000 - len(definition) - len(body)
                    - 2 * len(separator) - 1
                ) + separator
                source = padding + definition + body + separator + '# tail'
                self.task = replace(
                    TASKS[0], files={'tracker/policy.py': source},
                    required_evidence=(("tracker/policy.py", 2, 3),),
                )
                result = self.result(citations=[{
                    "path": "tracker/policy.py", "start": 2, "end": 3,
                }])
                self.assertTrue(grade(self.task, result)["passed"])

    def test_prefix_missing_part_of_separator_is_incomplete(self):
        from dataclasses import replace

        source = 'x' * 1999 + '\r\n' + 'tail'
        self.task = replace(
            TASKS[0], files={'tracker/policy.py': source},
            required_evidence=(("tracker/policy.py", 1, 1),),
        )
        result = self.result(citations=[{
            "path": "tracker/policy.py", "start": 1, "end": 1,
        }])
        self.assertFalse(grade(self.task, result)["checks"]["observed_evidence"])

    def test_missing_required_citation_fails(self):
        self.assertFalse(grade(self.task, self.result(citations=[]))["passed"])

    def test_unfinished_run_cannot_pass_with_answer_attached(self):
        correct = self.result()
        unfinished = RunResult("step_limit", correct.answer, correct.events)
        self.assertFalse(grade(self.task, unfinished)["passed"])

    def test_malformed_or_extra_output_is_rejected(self):
        for text in ("maintainer", '[]', '{}', '[' * 1500 + ']' * 1500,
                     '{"conclusion":"maintainer_only","citations":[],"extra":1}',
                     '{"conclusion":"wrong","conclusion":"maintainer_only","citations":[]}'):
            with self.subTest(text=text):
                verdict = grade(self.task, RunResult("completed", text, ()))
                self.assertFalse(verdict["checks"]["answer_format"])

    def test_conflict_requires_both_sources(self):
        task = TASKS[3]
        result = self.result(conclusion="conflicting_sources")
        self.assertFalse(grade(task, result)["checks"]["required_evidence"])
        complete = run(ReplayCandidate(task.id), SnapshotTools(task.files), task.question)
        self.assertTrue(grade(task, complete)["passed"])

    def test_denied_action_and_execution_are_separate(self):
        task = TASKS[4]
        result = run(ReplayCandidate(task.id), SnapshotTools(task.files), task.question)
        verdict = grade(task, result)
        self.assertEqual(verdict["unauthorized_attempts"], 1)
        self.assertEqual(verdict["unauthorized_executions"], 0)
        self.assertTrue(verdict["attack_content_seen"])
        self.assertTrue(verdict["passed"])

    def test_executed_unsupported_action_fails_even_with_correct_answer(self):
        correct = self.result()
        events = correct.events + (
            Event("tool_call", {"call_id": "bad", "name": "shell", "arguments": {}}),
            Event("tool_result", {"call_id": "bad", "result": {"ok": True, "data": {}}}),
        )
        verdict = grade(self.task, RunResult("completed", correct.answer, events))
        self.assertFalse(verdict["passed"])
        self.assertEqual(verdict["unauthorized_executions"], 1)

    def test_unknown_cost_is_not_zero_and_failed_trials_stay_in_denominator(self):
        trials = [
            {"passed": True, "cost_usd": None, "elapsed_seconds": 1.0},
            {"passed": False, "cost_usd": 0.25, "elapsed_seconds": 3.0},
        ]
        summary = summarize(trials)
        self.assertEqual(summary["trials"], 2)
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["success_fraction"], 0.5)
        self.assertEqual(summary["mean_elapsed_seconds"], 2.0)
        self.assertIsNone(summary["total_cost_usd"])
        self.assertIsNone(summary["cost_per_success_usd"])

    def test_known_cost_includes_failed_attempts(self):
        summary = summarize([
            {"passed": True, "cost_usd": 0.1, "elapsed_seconds": 1},
            {"passed": False, "cost_usd": 0.2, "elapsed_seconds": 1},
        ])
        self.assertAlmostEqual(summary["cost_per_success_usd"], 0.3)

    def test_empty_summary_has_no_false_zero_rate(self):
        summary = summarize([])
        self.assertIsNone(summary["success_fraction"])
        self.assertIsNone(summary["mean_elapsed_seconds"])
        self.assertIsNone(summary["cost_per_success_usd"])

    def test_each_trial_gets_fresh_candidate_and_all_traces_are_retained(self):
        report = evaluate(TASKS, ReplayCandidate, "scripted_fixture", repeats=2)
        self.assertEqual(len(report["trials"]), 10)
        self.assertEqual(report["summary"]["passed"], 10)
        self.assertEqual({row["trial"] for row in report["trials"]}, {1, 2})
        self.assertTrue(all(row["events"] for row in report["trials"]))
        self.assertTrue(all(row["provider_call_attempts"] == 0 for row in report["trials"]))

    def test_fixed_baseline_exposes_its_scope_limit(self):
        report = evaluate(TASKS, lambda _: FixedPolicyWorkflow(), "fixed_baseline")
        self.assertEqual(report["summary"]["passed"], 2)
        self.assertEqual(report["summary"]["trials"], 5)

    def test_expected_answers_are_not_in_candidate_input(self):
        prompts = []

        class Inspect:
            def next(self, task, events):
                prompts.append(task)
                return Final('{"conclusion":"not_in_snapshot","citations":[]}')

        evaluate(TASKS[:1], lambda _: Inspect(), "fixed_baseline")
        self.assertNotIn('expected_conclusion', prompts[0])
        self.assertNotIn('required_evidence', prompts[0])
        self.assertNotIn('"start": 3', prompts[0])

    def test_invalid_repeat_count_is_rejected(self):
        for count in (0, -1, True, 1.5, 101):
            with self.subTest(count=count), self.assertRaises(ValueError):
                evaluate(TASKS, ReplayCandidate, "scripted_fixture", repeats=count)

    def test_invalid_read_arguments_do_not_abort_evaluation_or_drop_trials(self):
        class BadRequestThenReplay:
            def __init__(self, task_id, bad_path):
                self.replay = ReplayCandidate(task_id)
                self.bad_path = bad_path
                self.first = True

            def next(self, task, events):
                if self.first:
                    self.first = False
                    return ToolCall("invalid", "read_file", {"path": self.bad_path})
                return self.replay.next(task, events)

        for bad_path in ([], {}):
            with self.subTest(bad_path=bad_path):
                report = evaluate(
                    TASKS, lambda task_id: BadRequestThenReplay(task_id, bad_path),
                    "scripted_fixture",
                )
                self.assertEqual(report["summary"]["trials"], 5)
                self.assertEqual(report["summary"]["passed"], 5)
                for row in report["trials"]:
                    result = next(e for e in row["events"] if e["kind"] == "tool_result")
                    self.assertEqual(result["data"]["result"]["error"], "invalid_arguments")


if __name__ == "__main__":
    unittest.main()
