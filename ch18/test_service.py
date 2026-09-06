from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
from service import Queue, fingerprint
from experiment import experiment


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.q = Queue(Path(self.temp.name)/'q.sqlite')
        self.q.enqueue('a', 'j', {'task': 'x'})

    def test_duplicate_admission(self):
        self.assertFalse(self.q.enqueue('a', 'j', {'task': 'x'}))

    def test_idempotency_conflict(self):
        with self.assertRaisesRegex(ValueError, 'idempotency_conflict'):
            self.q.enqueue('a', 'j', {'task': 'different'})

    def test_tenant_key_separation(self):
        self.assertTrue(self.q.enqueue('b', 'j', {'task': 'y'}))

    def test_quota(self):
        self.q.enqueue('a', 'k', {})
        with self.assertRaisesRegex(ValueError, 'tenant_quota'):
            self.q.enqueue('a', 'third', {})

    def test_concurrent_claim(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(lambda _: self.q.claim('a', 'j', 0), [1, 2]))
        self.assertEqual(sum(x is not None for x in result), 1)

    def test_unexpired_claim(self):
        self.q.claim('a', 'j', 0)
        self.assertIsNone(self.q.claim('a', 'j', 9))

    def test_reclaim_at_expiry(self):
        self.assertEqual(self.q.claim('a', 'j', 0), 1)
        self.assertEqual(self.q.claim('a', 'j', 10), 2)

    def test_expired_submit(self):
        g = self.q.claim('a', 'j', 0)
        self.assertFalse(self.q.submit('a', 'j', g, {}, 10))

    def test_old_generation(self):
        self.q.claim('a', 'j', 0)
        self.q.claim('a', 'j', 10)
        self.assertFalse(self.q.submit('a', 'j', 1, {}, 11))

    def test_missing_job(self):
        self.assertIsNone(self.q.claim('a', 'missing', 0))
        self.assertFalse(self.q.approve('a', 'missing', 'x'))

    def test_other_tenant_cannot_submit(self):
        g = self.q.claim('a', 'j', 0)
        self.assertFalse(self.q.submit('b', 'j', g, {}, 1))

    def test_other_tenant_cannot_inspect(self):
        self.assertIsNone(self.q.inspect('b', 'j'))

    def test_cancel_queued(self):
        self.assertTrue(self.q.cancel('a', 'j'))
        self.assertIsNone(self.q.claim('a', 'j', 0))

    def test_cancel_running(self):
        g = self.q.claim('a', 'j', 0)
        self.q.cancel('a', 'j')
        self.assertFalse(self.q.submit('a', 'j', g, {}, 1))

    def test_review_before_effect(self):
        g = self.q.claim('a', 'j', 0)
        self.q.submit('a', 'j', g, {'answer': 'x'}, 1)
        self.assertEqual(self.q.inspect('a', 'j')['state'], 'review')
        self.assertEqual(self.q.effects('a'), [])

    def test_exact_approval(self):
        g = self.q.claim('a', 'j', 0)
        self.q.submit('a', 'j', g, {}, 1)
        with self.assertRaisesRegex(ValueError, 'review_candidate_changed'):
            self.q.approve('a', 'j', 'wrong')
        self.assertEqual(self.q.effects('a'), [])

    def test_duplicate_approval_one_effect(self):
        g = self.q.claim('a', 'j', 0)
        self.q.submit('a', 'j', g, {}, 1)
        self.assertTrue(self.q.approve('a', 'j', fingerprint({})))
        self.assertFalse(self.q.approve('a', 'j', fingerprint({})))
        self.assertEqual(len(self.q.effects('a')), 1)

    def test_cancel_review(self):
        g = self.q.claim('a', 'j', 0)
        self.q.submit('a', 'j', g, {}, 1)
        self.q.cancel('a', 'j')
        self.assertFalse(self.q.approve('a', 'j', fingerprint({})))

    def test_completed_effect_not_undone(self):
        g = self.q.claim('a', 'j', 0)
        self.q.submit('a', 'j', g, {}, 1)
        self.q.approve('a', 'j', fingerprint({}))
        self.assertFalse(self.q.cancel('a', 'j'))
        self.assertEqual(len(self.q.effects('a')), 1)

    def test_connections_are_closed(self):
        import gc
        import warnings
        gc.collect()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', ResourceWarning)
            queue = Queue(Path(self.temp.name)/'closed.sqlite')
            queue.inspect('a', 'missing')
            queue.effects('a')
            del queue
            gc.collect()
        self.assertEqual([w for w in caught
                          if issubclass(w.category, ResourceWarning)], [])

    def test_process_crash_recovery(self):
        report = experiment()
        self.assertEqual(report['child_exit'], 23)
        self.assertEqual(report['replacement_generation'], 2)
        self.assertFalse(report['stale_submit'])
        self.assertTrue(report['fresh_submit'])
        self.assertEqual(len(report['effects']), 1)
        self.assertFalse(report['late_submit'])


    def test_submit_rejects_coerced_generation_without_mutation(self):
        self.q.claim('a', 'j', 0)
        before = self.q.inspect('a', 'j')
        for generation in (True, '1', 1.0, None, 0, -1):
            with self.subTest(generation=generation):
                with self.assertRaisesRegex(ValueError, 'invalid_submission'):
                    self.q.submit('a', 'j', generation, {}, 1)
                self.assertEqual(self.q.inspect('a', 'j'), before)

    def test_submit_rejects_noninteger_time_without_mutation(self):
        generation = self.q.claim('a', 'j', 0)
        before = self.q.inspect('a', 'j')
        for now in (True, '1', 1.5, None):
            with self.subTest(now=now):
                with self.assertRaisesRegex(ValueError, 'invalid_submission'):
                    self.q.submit('a', 'j', generation, {}, now)
                self.assertEqual(self.q.inspect('a', 'j'), before)

if __name__ == '__main__':
    unittest.main()
