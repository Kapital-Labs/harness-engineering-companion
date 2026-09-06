import copy
import json
from pathlib import Path
import tempfile
import unittest
from tracing import Trace, replay, investigate, run_case


class TraceTests(unittest.TestCase):
    def run_fixture(self, case):
        with tempfile.TemporaryDirectory() as d:
            result = run_case(Path(d), case)
            return result

    def test_success_after_retry(self):
        r = self.run_fixture('success')
        self.assertEqual(r['diagnosis'], 'matching_artifact')
        self.assertTrue(r['artifact_matches'])

    def test_wrong_export_is_harness_mismatch(self):
        r = self.run_fixture('wrong_export')
        self.assertEqual(r['diagnosis'], 'export_mismatch')
        self.assertFalse(r['artifact_matches'])

    def test_wrong_choice_is_proposal_mismatch(self):
        r = self.run_fixture('wrong_choice')
        self.assertEqual(r['diagnosis'], 'proposal_mismatch')

    def test_write_failure_has_no_artifact(self):
        r = self.run_fixture('write_failure')
        self.assertEqual(r['diagnosis'], 'write_failed')
        self.assertIsNone(r['actual_sha256'])

    def test_all_claims_are_scripted_success(self):
        for case in ('success', 'wrong_export', 'wrong_choice', 'write_failure'):
            with self.subTest(case=case):
                self.assertTrue(self.run_fixture(case)['claimed_success'])

    def test_retry_ids_distinct_operation_same(self):
        trace = self.run_fixture('success')['trace']
        spans = [s for s in trace['spans'] if s['name'] == 'export']
        self.assertEqual([s['attempt'] for s in spans], [1, 2])
        self.assertEqual(len({s['span_id'] for s in spans}), 2)
        self.assertEqual(len({s['operation_id'] for s in spans}), 1)
        self.assertEqual([s['status'] for s in spans], ['error', 'ok'])

    def test_replay_does_not_reexecute(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); r = run_case(root, 'wrong_export')
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            for _ in range(3):
                self.assertEqual(replay(r['trace'])['span_count'], 6)
            self.assertEqual(before, {p.name: p.read_bytes()
                                     for p in root.iterdir()})

    def test_missing_final_span_is_incomplete(self):
        t = self.run_fixture('success')['trace']; t['spans'].pop()
        self.assertEqual(investigate(t, None), 'incomplete_trace')

    def test_missing_artifact_not_assumed_correct(self):
        t = self.run_fixture('success')['trace']
        self.assertEqual(investigate(t, None), 'artifact_unavailable')

    def test_duplicate_span_rejected(self):
        t = self.run_fixture('success')['trace']
        t['spans'].append(copy.deepcopy(t['spans'][1]))
        with self.assertRaises(ValueError): replay(t)

    def test_orphan_parent_rejected(self):
        t = self.run_fixture('success')['trace']
        t['spans'][1]['parent_id'] = 'absent'
        with self.assertRaises(ValueError): replay(t)

    def test_negative_duration_rejected(self):
        t = self.run_fixture('success')['trace']
        t['spans'][1]['end_ns'] = -1
        with self.assertRaises(ValueError): replay(t)

    def test_open_span_is_incomplete(self):
        t = self.run_fixture('success')['trace']
        t['spans'][1]['end_ns'] = None
        self.assertFalse(replay(t)['complete'])

    def test_unapproved_attribute_rejected(self):
        t = Trace('test')
        with self.assertRaises(ValueError):
            t.start('run', attributes={'prompt': 'FAKE_SECRET'})
        self.assertEqual(t.spans, [])

    def test_digest_attribute_validated(self):
        t = Trace('test')
        with self.assertRaises(ValueError):
            t.start('run', attributes={'selected_sha256': 'FAKE_SECRET'})

    def test_fake_clock_duration(self):
        values = iter([10, 40])
        t = Trace('test', clock=lambda: next(values))
        span = t.start('run'); t.end(span)
        self.assertEqual(t.spans[0]['end_ns']-t.spans[0]['start_ns'], 30)

    def test_trace_excludes_source_and_model_text(self):
        s = json.dumps(self.run_fixture('wrong_export')['trace'])
        self.assertNotIn('FAKE_TRACE_SECRET', s)
        self.assertNotIn('Candidate ready', s)

    def test_round_trip(self):
        t = self.run_fixture('success')['trace']
        self.assertEqual(replay(t), replay(json.loads(json.dumps(t))))

    def test_changed_artifact_detected_from_bytes(self):
        t = self.run_fixture('success')['trace']
        self.assertEqual(investigate(t, b'changed'), 'export_mismatch')

    def test_duplicate_selection_is_not_arbitrarily_chosen(self):
        t = self.run_fixture('success')['trace']
        selection = copy.deepcopy(t['spans'][1])
        selection['span_id'] = 'extra-selection'
        selection['attributes']['selected_sha256'] = '0' * 64
        t['spans'].append(selection)
        t['expected_span_count'] += 1
        self.assertEqual(investigate(t, b'candidate'), 'incomplete_trace')

    def test_bad_case_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): run_case(Path(d), 'unknown')


if __name__ == '__main__': unittest.main()
