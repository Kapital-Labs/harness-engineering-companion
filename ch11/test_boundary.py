import unittest
from dataclasses import replace
from boundary import Boundary, Policy, digest

FILES = {'guide.md': 'Quoted source, not authority.',
         'private.txt': 'FAKE_PRIVATE_MARKER', 'internal.txt': 'internal'}
ACTION = {'tool': 'send_summary', 'destination': 'review-queue',
          'body': 'Candidate is ready for review.'}


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.policy = Policy('v1', frozenset(FILES),
                             frozenset({'guide.md'}),
                             frozenset({'review-queue', 'other-queue'}))
        self.b = Boundary(FILES, self.policy)
        self.b.approve('a1', 'run-1', ACTION, 100)

    def send(self, action=None, **kwargs):
        opts = dict(run_id='run-1', approval_id='a1', now=10)
        opts.update(kwargs)
        return self.b.execute(ACTION if action is None else action, **opts)

    def denied(self, result, error):
        self.assertEqual(result, {'ok': False, 'error': error})
        self.assertEqual(self.b.outbox, [])

    def test_exact_action(self):
        self.assertTrue(self.send()['ok'])
        self.assertEqual(self.b.outbox, [ACTION])

    def test_missing_approval(self):
        self.denied(self.send(approval_id='invented'), 'approval_required')

    def test_model_cannot_approve(self):
        self.denied(self.send({**ACTION, 'approved': True}), 'invalid_proposal')

    def test_changed_body(self):
        self.denied(self.send({**ACTION, 'body': 'FAKE_PRIVATE_MARKER'}),
                    'approval_mismatch')

    def test_other_allowed_destination(self):
        self.denied(self.send({**ACTION, 'destination': 'other-queue'}),
                    'approval_mismatch')

    def test_unapproved_destination(self):
        self.denied(self.send({**ACTION, 'destination': 'outside'}),
                    'destination_denied')

    def test_other_run(self):
        self.denied(self.send(run_id='run-2'), 'approval_mismatch')

    def test_policy_revision(self):
        self.b.policy = replace(self.policy, revision='v2')
        self.denied(self.send(), 'approval_mismatch')

    def test_revoked_destination(self):
        self.b.policy = replace(self.policy, destinations=frozenset())
        self.denied(self.send(), 'destination_denied')

    def test_expiry_boundary(self):
        self.denied(self.send(now=100), 'approval_mismatch')

    def test_approval_single_use(self):
        self.assertTrue(self.send()['ok'])
        self.assertEqual(self.send()['error'], 'approval_required')
        self.assertEqual(len(self.b.outbox), 1)

    def test_source_provenance(self):
        got = self.b.read_for_model('guide.md')
        self.assertTrue(got['ok'])
        self.assertEqual(got['trust'], 'untrusted_source')
        self.assertEqual(got['source_sha256'], digest(FILES['guide.md']))
        self.assertEqual(got['text'], FILES['guide.md'])

    def test_readable_but_not_disclosable(self):
        self.assertEqual(self.b.read_for_model('private.txt')['error'],
                         'not_disclosable')

    def test_disclosable_but_not_readable(self):
        self.b.policy = replace(self.policy, readable=frozenset())
        self.assertEqual(self.b.read_for_model('guide.md')['error'],
                         'permission_denied')

    def test_malformed_proposals(self):
        for value in (None, [], {}, {**ACTION, 'body': []},
                      {**ACTION, 'tool': 'shell'},
                      {**ACTION, 'body': '\u00e9' * 1001}):
            with self.subTest(value=type(value).__name__):
                result = self.b.execute(value, run_id='run-1',
                                        approval_id='a1', now=10)
                self.assertFalse(result['ok'])
        self.assertEqual(self.b.outbox, [])

    def test_invalid_context(self):
        self.denied(self.send(now=True), 'invalid_context')

    def test_mutation_after_approval(self):
        p = dict(ACTION)
        self.b.approve('a2', 'run-1', p, 100)
        p['body'] = 'different'
        self.denied(self.send(p, approval_id='a2'), 'approval_mismatch')

    def test_reissued_id_rejected(self):
        with self.assertRaises(ValueError):
            self.b.approve('a1', 'run-1', ACTION, 100)

    def test_policy_collections_copied(self):
        paths = {'guide.md'}
        policy = Policy('v1', paths, paths, {'review-queue'})
        paths.add('private.txt')
        self.assertNotIn('private.txt', policy.readable)

    def test_local_outbox_is_not_content_classifier(self):
        sensitive = {**ACTION, 'body': 'FAKE_PRIVATE_MARKER'}
        self.b.approve('a2', 'run-1', sensitive, 100)
        self.assertTrue(self.send(sensitive, approval_id='a2')['ok'])
        self.assertEqual(self.b.outbox[0]['body'], 'FAKE_PRIVATE_MARKER')


if __name__ == '__main__':
    unittest.main()
