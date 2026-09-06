"""Behavioral checks for the Chapter 2 execution boundary."""

import unittest

from harness import Final, SnapshotTools, ToolCall, run


class SequenceModel:
    def __init__(self, *actions):
        self.actions = iter(actions)
        self.calls = 0

    def next(self, task, events):
        self.calls += 1
        return next(self.actions)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tools = SnapshotTools({
            "tracker/policy.py": "def can_close(role):\n"
            "    return role == 'maintainer'\n",
        })

    def test_results_reach_model_and_final_answer_is_retained(self):
        class EvidenceModel:
            def next(inner, task, events):
                results = [e for e in events if e.kind == "tool_result"]
                if not results:
                    return ToolCall("s1", "search", {"query": "can_close"})
                match = results[-1].data["result"]["data"]["matches"][0]
                return Final(f"Defined at {match['path']}:{match['line']}")

        result = run(EvidenceModel(), self.tools, "Locate can_close")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.answer, "Defined at tracker/policy.py:1")
        self.assertEqual(result.events[-1].data["status"], "completed")

    def test_unknown_tool_returns_error_instead_of_executing_it(self):
        model = SequenceModel(
            ToolCall("x", "shell", {"command": "anything"}),
            Final("Cannot execute shell commands."),
        )
        result = run(model, self.tools, "Run a command")
        observation = next(e for e in result.events if e.kind == "tool_result")
        self.assertEqual(observation.data["result"]["error"], "unknown_tool")
        self.assertEqual(result.status, "completed")

    def test_invalid_tool_arguments_are_recoverable(self):
        for arguments in ({}, {"query": 3}, {"query": ""},
                          {"query": "x", "extra": True}):
            with self.subTest(arguments=arguments):
                result = self.tools.execute(ToolCall("x", "search", arguments))
                self.assertFalse(result["ok"])
                self.assertEqual(result["error"], "invalid_arguments")

    def test_absent_path_never_falls_back_to_host_filesystem(self):
        result = self.tools.execute(
            ToolCall("x", "read_file", {"path": "/etc/passwd"})
        )
        self.assertEqual(result["error"], "unknown_file")

    def test_read_contains_evidence_and_reports_truncation(self):
        tools = SnapshotTools({"long.py": "x" * 3000})
        result = tools.execute(ToolCall("x", "read_file", {"path": "long.py"}))
        self.assertEqual(result["data"]["first_line"], 1)
        self.assertTrue(result["data"]["truncated"])
        self.assertLess(len(result["data"]["text"]), 3000)

    def test_search_is_literal_bounded_and_includes_line_numbers(self):
        tools = SnapshotTools({"a.py": "needle\n" * 12})
        result = tools.execute(ToolCall("x", "search", {"query": "needle"}))
        self.assertEqual(len(result["data"]["matches"]), 5)
        self.assertEqual(result["data"]["matches"][0]["line"], 1)
        self.assertTrue(result["data"]["truncated"])
        absent = tools.execute(ToolCall("y", "search", {"query": ".*"}))
        self.assertEqual(absent["data"]["matches"], [])

    def test_repeating_model_stops_at_limit_without_extra_call(self):
        model = SequenceModel(
            ToolCall("1", "search", {"query": "x"}),
            ToolCall("2", "search", {"query": "x"}),
            Final("This must never run"),
        )
        result = run(model, self.tools, "Find x", max_steps=2)
        self.assertEqual(result.status, "step_limit")
        self.assertIsNone(result.answer)
        self.assertEqual(model.calls, 2)

    def test_final_answer_on_last_allowed_turn_is_completed(self):
        result = run(SequenceModel(Final("Done")), self.tools, "Answer",
                     max_steps=1)
        self.assertEqual(result.status, "completed")

    def test_cancellation_before_call_prevents_model_execution(self):
        model = SequenceModel(Final("Must not run"))
        result = run(model, self.tools, "Answer", cancelled=lambda: True)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(model.calls, 0)

    def test_cancellation_after_reply_prevents_tool_execution(self):
        class RecordingTools(SnapshotTools):
            def __init__(self):
                super().__init__({"sample.py": "x"})
                self.executed = []

            def execute(self, call):
                self.executed.append(call)
                return super().execute(call)

        tools = RecordingTools()
        checks = iter([False, True])
        model = SequenceModel(ToolCall("x", "search", {"query": "x"}))
        result = run(model, tools, "Find x", cancelled=lambda: next(checks))
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(tools.executed, [])
        self.assertFalse(any(e.kind == "tool_result" for e in result.events))

    def test_malformed_model_actions_stop_without_dispatch(self):
        for action in (None, {"name": "search"}, Final(""),
                       ToolCall("", "search", {"query": "x"}),
                       ToolCall("x", "search", [])):
            with self.subTest(action=action):
                result = run(SequenceModel(action), self.tools, "Find x")
                self.assertEqual(result.status, "invalid_output")
                self.assertFalse(any(e.kind == "tool_result" for e in result.events))

    def test_duplicate_call_id_is_rejected(self):
        model = SequenceModel(
            ToolCall("x", "search", {"query": "x"}),
            ToolCall("x", "search", {"query": "x"}),
        )
        result = run(model, self.tools, "Find x")
        self.assertEqual(result.status, "invalid_output")
        self.assertEqual(sum(e.kind == "tool_result" for e in result.events), 1)

    def test_provider_error_does_not_leak_exception_message(self):
        class BrokenModel:
            def next(self, task, events):
                raise RuntimeError("secret-token-123")

        result = run(BrokenModel(), self.tools, "Answer")
        self.assertEqual(result.status, "model_error")
        self.assertNotIn("secret-token-123", repr(result))
        self.assertIn("RuntimeError", repr(result))

    def test_model_cannot_rewrite_existing_trace_records(self):
        class MutatingModel:
            def next(self, task, events):
                events[0].data["task"] = "changed"
                return Final("Done")

        result = run(MutatingModel(), self.tools, "Original")
        self.assertEqual(result.events[0].data["task"], "Original")

    def test_invalid_budget_is_rejected_before_execution(self):
        for limit in (0, -1, True, 1.5, 101):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    run(SequenceModel(), self.tools, "Answer", max_steps=limit)


if __name__ == "__main__":
    unittest.main()
