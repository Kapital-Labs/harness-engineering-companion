import json
import tempfile
import unittest
from unittest.mock import patch
from dataclasses import replace
from pathlib import Path
from defenses import (ACTION, FILES, MARKER, POLICY, Session, assess,
                      run_suite, incident, encoded_marker)


class DefenseTests(unittest.TestCase):
    def test_suite_expectations(self):
        rows = run_suite()
        self.assertEqual(len(rows), 10)
        self.assertTrue(all(r['property_holds'] for r in rows
                            if r['case'] != 'known_disclosure'))
        self.assertFalse(next(r for r in rows
                              if r['case'] == 'known_disclosure')
                         ['property_holds'])

    def test_known_failure_not_hidden_by_refusal(self):
        row = next(r for r in run_suite() if r['case'] == 'known_disclosure')
        self.assertTrue(row['scripted_refusal'])
        self.assertTrue(row['executed_violation'])
        self.assertEqual(row['effects'], 1)

    def test_denial_alone_does_not_prove_no_effect(self):
        result = assess({'ok': False}, [{'body': MARKER}],
                        forbidden=True, sensitive=MARKER)
        self.assertFalse(result['property_holds'])
        self.assertTrue(result['executed_violation'])

    def test_positive_control_requires_effect(self):
        self.assertFalse(assess({'ok': True}, [], forbidden=False,
                                expected=ACTION)['property_holds'])

    def test_positive_control_requires_exact_effect(self):
        self.assertFalse(assess({'ok': True}, [{'body': 'wrong'}],
                                forbidden=False, expected=ACTION)
                         ['property_holds'])

    def test_unknown_outcome_inconclusive(self):
        result = assess({'ok': False}, None, forbidden=True)
        self.assertIsNone(result['property_holds'])
        self.assertIsNone(result['executed_violation'])

    def test_encoded_fixture_oracle(self):
        value = encoded_marker()
        result = assess({'ok': True}, [{'body': value}],
                        forbidden=True, sensitive=value)
        self.assertTrue(result['sensitive_effect'])

    def test_containment_preserves_existing_effect(self):
        report = incident()
        self.assertEqual(report['effects_before_containment'], 1)
        self.assertEqual(report['effects_after_containment'], 1)

    def test_containment_blocks_pending_send(self):
        report = incident()
        self.assertEqual(report['pending_send']['error'], 'run_contained')

    def test_containment_blocks_read(self):
        self.assertEqual(incident()['subsequent_read']['error'],
                         'run_contained')

    def test_containment_revokes_policy_and_approvals(self):
        s = Session()
        s.boundary.approve('a1', 'run-1', ACTION, 100)
        s.contain()
        self.assertFalse(s.boundary.approvals)
        self.assertFalse(s.boundary.policy.readable)
        self.assertFalse(s.boundary.policy.destinations)

    def test_containment_idempotent(self):
        s = Session(); s.contain(); first = s.events.copy()
        s.contain()
        self.assertEqual(first, s.events)

    def test_direct_executor_denied_after_containment(self):
        s = Session(); s.boundary.approve('a1', 'run-1', ACTION, 100)
        s.contain()
        got = s.boundary.execute(ACTION, run_id='run-1',
                                 approval_id='a1', now=10)
        self.assertEqual(got['error'], 'destination_denied')
        self.assertEqual(s.boundary.outbox, [])

    def test_recovery_read_only(self):
        report = incident()
        self.assertTrue(report['recovery_read']['ok'])
        self.assertTrue(report['recovery_read']['property_holds'])
        self.assertTrue(all(not r['ok'] for r in report['recovery_sends']))
        self.assertEqual(report['recovery_effects'], 0)

    def test_recovery_has_no_inherited_approvals(self):
        s = Session(policy=replace(POLICY, revision='recovery-1',
                                    destinations=frozenset()))
        self.assertEqual(s.boundary.approvals, {})

    def test_report_excludes_sensitive_payloads(self):
        data = json.dumps(incident())
        self.assertNotIn(MARKER, data)
        self.assertNotIn(encoded_marker(), data)
        self.assertNotIn(FILES['handoff.md'], data)

    def test_event_sequence(self):
        events = incident()['events']
        self.assertEqual([e['sequence'] for e in events],
                         list(range(1, len(events) + 1)))
        self.assertTrue(all(set(e) == {'sequence', 'kind', 'status',
                                       'effects'} for e in events))

    def test_export_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'incident.json'
            report = incident()
            p.write_text(json.dumps(report))
            self.assertEqual(json.loads(p.read_text()), report)

    def test_untrusted_handoff_does_not_create_approval(self):
        s = Session(); got = s.read('handoff.md')
        self.assertTrue(got['ok'])
        self.assertEqual(s.boundary.approvals, {})
        self.assertEqual(s.send(ACTION)['error'], 'approval_required')

    def test_denied_read_with_payload_is_detected_and_not_exported(self):
        reply = {'ok': False, 'error': 'not_disclosable', 'text': MARKER}
        with patch('defenses.Session.read', return_value=reply):
            row = run_suite()[0]
        self.assertTrue(row['executed_violation'])
        self.assertFalse(row['property_holds'])
        self.assertNotIn(MARKER, json.dumps(row))

    def test_denied_read_with_marker_in_error_is_not_exported(self):
        reply = {'ok': False, 'error': MARKER}
        with patch('defenses.Session.read', return_value=reply):
            row = run_suite()[0]
        self.assertTrue(row['executed_violation'])
        self.assertNotIn(MARKER, json.dumps(row))

    def test_denied_read_detects_json_escaped_protected_text(self):
        from defenses import read_effects

        for protected in (
            'line one\nline two',
            'quote "inside"',
            'path\\component',
        ):
            with self.subTest(protected=protected):
                reply = {
                    'ok': False,
                    'error': 'denied',
                    'details': {'text': protected},
                }
                effects = read_effects(reply, protected)
                verdict = assess(reply, effects, forbidden=True)
                self.assertTrue(verdict['executed_violation'])
                self.assertFalse(verdict['property_holds'])

    def test_recovery_success_without_content_fails(self):
        with patch('defenses.Session.read', return_value={'ok': True}):
            report = incident()
        self.assertFalse(report['recovery_read']['property_holds'])

    def test_recovery_wrong_content_fails(self):
        with patch('defenses.Session.read', return_value={
            'ok': True, 'text': 'wrong', 'path': 'review.md'
        }):
            report = incident()
        self.assertFalse(report['recovery_read']['property_holds'])

    def test_negative_control_detects_always_allow(self):
        self.assertFalse(assess({'ok': True}, [ACTION], forbidden=True)
                         ['property_holds'])


if __name__ == '__main__':
    unittest.main()
