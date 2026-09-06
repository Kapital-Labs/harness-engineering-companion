import json
import unittest
from unittest.mock import patch

from anthropic_adapter import (
    AnthropicModel, InvalidResponse, ProviderError, build_messages,
    parse_response, post_messages,
)
from harness import Event, Final, ToolCall


def response(reason, content):
    return {"id": "msg_fixture", "type": "message", "role": "assistant",
            "model": "fixture-model", "content": content,
            "stop_reason": reason, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5}}


class AdapterTests(unittest.TestCase):
    def test_native_tool_block_becomes_normalized_action(self):
        action = parse_response(response("tool_use", [
            {"type": "text", "text": "I will search."},
            {"type": "tool_use", "id": "t1", "name": "search",
             "input": {"query": "policy"}},
        ]))
        self.assertEqual(action, ToolCall("t1", "search", {"query": "policy"}))

    def test_completed_text_becomes_final_answer(self):
        self.assertEqual(parse_response(response("end_turn", [
            {"type": "text", "text": "See policy.py:3."},
        ])), Final("See policy.py:3."))

    def test_incomplete_refusal_and_incompatible_responses_are_rejected(self):
        tool = {"type": "tool_use", "id": "t1", "name": "search",
                "input": {"query": "x"}}
        cases = [
            response("max_tokens", [{"type": "text", "text": "Partial"}]),
            response("refusal", [{"type": "text", "text": "Declined"}]),
            response("tool_use", [tool, {**tool, "id": "t2"}]),
            response("end_turn", [tool]),
            response("end_turn", [{"type": "thinking", "thinking": "x"}]),
            response("end_turn", [{"type": "text", "text": ""}]),
            response("tool_use", [{**tool, "input": []}]),
            response("end_turn", [None]),
            {}, None,
        ]
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(InvalidResponse):
                    parse_response(case)

    def test_tool_result_immediately_follows_matching_call(self):
        messages = build_messages("Find policy", (
            Event("model_call", {"step": 1}),
            Event("tool_call", {"call_id": "t1", "name": "read_file",
                                "arguments": {"path": "absent.py"}}),
            Event("tool_result", {"call_id": "t1", "result": {
                "ok": False, "error": "unknown_file"}}),
        ))
        self.assertEqual([m["role"] for m in messages],
                         ["user", "assistant", "user"])
        call = messages[1]["content"][0]
        result = messages[2]["content"][0]
        self.assertEqual(call["id"], "t1")
        self.assertEqual(result["tool_use_id"], "t1")
        self.assertTrue(result["is_error"])
        self.assertEqual(json.loads(result["content"])["error"], "unknown_file")

    def test_model_builds_single_tool_request_without_credentials_in_payload(self):
        captured = {}

        def transport(key, payload):
            captured.update(payload)
            return response("end_turn", [{"type": "text", "text": "Answer"}])

        with patch("anthropic_adapter.post_messages", side_effect=transport):
            action = AnthropicModel("account-model", "private-key").next("Task", ())
        self.assertEqual(action, Final("Answer"))
        self.assertEqual(captured["model"], "account-model")
        self.assertEqual(captured["tool_choice"],
                         {"type": "auto", "disable_parallel_tool_use": True})
        self.assertEqual({t["name"] for t in captured["tools"]},
                         {"search", "read_file"})
        self.assertNotIn("private-key", json.dumps(captured))

    def test_http_transport_posts_documented_headers_and_closes_connection(self):
        with patch("anthropic_adapter.http.client.HTTPSConnection") as factory:
            connection = factory.return_value
            connection.getresponse.return_value.status = 200
            connection.getresponse.return_value.read.return_value = b'{"content": []}'
            self.assertEqual(post_messages("test-key", {"model": "fixture"}),
                             {"content": []})
            factory.assert_called_once_with("api.anthropic.com", timeout=30)
            args, kwargs = connection.request.call_args
            self.assertEqual(args, ("POST", "/v1/messages"))
            self.assertEqual(kwargs["headers"]["x-api-key"], "test-key")
            self.assertEqual(kwargs["headers"]["anthropic-version"], "2023-06-01")
            self.assertEqual(json.loads(kwargs["body"]), {"model": "fixture"})
            connection.close.assert_called_once()

    def test_http_errors_do_not_expose_server_body(self):
        with patch("anthropic_adapter.http.client.HTTPSConnection") as factory:
            connection = factory.return_value
            connection.getresponse.return_value.status = 401
            connection.getresponse.return_value.read.return_value = b'private-key'
            with self.assertRaises(ProviderError) as caught:
                post_messages("test-key", {})
            self.assertNotIn("private-key", str(caught.exception))
            connection.close.assert_called_once()

    def test_oversized_http_response_is_rejected(self):
        with patch("anthropic_adapter.http.client.HTTPSConnection") as factory:
            connection = factory.return_value
            connection.getresponse.return_value.status = 200
            connection.getresponse.return_value.read.return_value = b'x' * 1_000_001
            with self.assertRaises(ProviderError):
                post_messages("test-key", {})
            connection.getresponse.return_value.read.assert_called_once_with(
                1_000_001
            )


if __name__ == "__main__":
    unittest.main()
