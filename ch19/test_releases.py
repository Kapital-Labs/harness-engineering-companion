import unittest
from releases import (migrate, migrate_bad, read_budget, release_gate,
                      can_read_all, cohort, experiment, fingerprint, BASE_MANIFEST)


class ReleaseTests(unittest.TestCase):
    def test_preserves_thirty_second_budget(self):
        state = {'version': 1, 'timeout_seconds': 30}
        self.assertEqual(read_budget(migrate(state)), 30000)
        self.assertEqual(state, {'version': 1, 'timeout_seconds': 30})

    def test_seeded_upgrade_regression(self):
        self.assertEqual(read_budget(migrate_bad(
            {'version': 1, 'timeout_seconds': 30})), 30)

    def test_budget_boundaries(self):
        for seconds, expected in [(1, 1000), (120, 120000)]:
            self.assertEqual(read_budget(migrate(
                {'version': 1, 'timeout_seconds': seconds})), expected)

    def test_rejects_boolean_duration(self):
        with self.assertRaises(ValueError):
            migrate({'version': 1, 'timeout_seconds': True})

    def test_rejects_unknown_version(self):
        with self.assertRaises(ValueError):
            read_budget({'version': 3, 'timeout_ms': 30})

    def test_rejects_double_migration(self):
        with self.assertRaises(ValueError):
            migrate({'version': 2, 'timeout_ms': 30000})

    def test_rejects_invalid_shape(self):
        with self.assertRaises(ValueError):
            migrate({'version': 1, 'timeout_seconds': 30, 'extra': 1})

    def test_gate_failure(self):
        self.assertFalse(release_gate({'task': True}, {'task': False}, {'task'}))

    def test_gate_unknown(self):
        self.assertFalse(release_gate({'task': True}, {'task': None}, {'task'}))

    def test_gate_missing(self):
        self.assertFalse(release_gate({'task': True}, {}, {'task'}))

    def test_gate_requires_comparable_baseline(self):
        self.assertFalse(release_gate({'task': None}, {'task': True}, {'task'}))

    def test_gate_empty(self):
        self.assertFalse(release_gate({}, {}, {'task'}))

    def test_both_omit_required_task(self):
        self.assertFalse(release_gate({'a': True}, {'a': True}, {'a', 'b'}))

    def test_gate_success(self):
        self.assertTrue(release_gate({'task': True}, {'task': True}, {'task'}))

    def test_rollback_schema(self):
        self.assertFalse(can_read_all({1}, [{'version': 2}]))
        self.assertTrue(can_read_all({1, 2}, [{'version': 2}]))

    def test_manifest_identity_changes_with_policy(self):
        self.assertNotEqual(fingerprint(BASE_MANIFEST),
                            fingerprint({**BASE_MANIFEST, 'policy': 'changed'}))

    def test_cohort_bounds_and_stability(self):
        self.assertFalse(cohort('tenant-a', 0))
        self.assertTrue(cohort('tenant-a', 100))
        self.assertEqual(cohort('tenant-a', 20), cohort('tenant-a', 20))

    def test_invalid_cohort(self):
        with self.assertRaises(ValueError):
            cohort('tenant-a', True)

    def test_experiment_gate_outcomes(self):
        report = experiment()
        self.assertEqual(report['gates'], {'bad_upgrade': False,
                                          'fixed_upgrade': True})
        self.assertFalse(report['old_reader_rollback_admitted'])


    def test_reader_rejects_nonobject_state_consistently(self):
        for state in (None, [], 1, 'bad'):
            with self.subTest(state=state):
                with self.assertRaisesRegex(ValueError, 'unsupported_state'):
                    read_budget(state)

if __name__ == '__main__':
    unittest.main()
