from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import unittest
from coordination import (BASE, Contract, Budget, digest, propose, integrate,
                          consistency_review, acceptance, trial, MODES, CASES)


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.base = deepcopy(BASE)
        self.contracts = [Contract(p, frozenset({p}), digest(BASE))
                          for p in sorted(BASE)]
        self.replies = [propose(c, BASE, 30, Budget(1)) for c in self.contracts]

    def test_complete_merge(self):
        self.assertTrue(acceptance(integrate(BASE, self.contracts, self.replies)))

    def test_completion_order_does_not_change_merge(self):
        self.assertEqual(integrate(BASE, self.contracts, self.replies),
                         integrate(BASE, self.contracts, self.replies[::-1]))

    def test_stale_reply(self):
        self.replies[0]['base_digest'] = 'old'
        with self.assertRaisesRegex(ValueError, 'stale_reply'):
            integrate(BASE, self.contracts, self.replies)

    def test_changed_base(self):
        self.base['client.json']['timeout'] = 11
        with self.assertRaisesRegex(ValueError, 'stale_reply'):
            integrate(self.base, self.contracts, self.replies)

    def test_missing_worker(self):
        with self.assertRaisesRegex(ValueError, 'incomplete_result'):
            integrate(BASE, self.contracts, self.replies[:1])

    def test_duplicate_reply(self):
        with self.assertRaisesRegex(ValueError, 'unknown_or_duplicate_worker'):
            integrate(BASE, self.contracts, self.replies + self.replies[:1])

    def test_unknown_worker(self):
        self.replies[0]['worker'] = 'intruder'
        with self.assertRaises(ValueError):
            integrate(BASE, self.contracts, self.replies)

    def test_scope_expansion(self):
        self.replies[0]['changes']['outside.json'] = {'timeout': 30}
        with self.assertRaisesRegex(ValueError, 'scope_or_coverage'):
            integrate(BASE, self.contracts, self.replies)

    def test_omitted_owned_path(self):
        self.replies[0]['changes'] = {}
        with self.assertRaises(ValueError):
            integrate(BASE, self.contracts, self.replies)

    def test_conflict_preserves_base(self):
        extra = Contract('extra', frozenset({'client.json'}), digest(BASE))
        with self.assertRaisesRegex(ValueError, 'conflicting_path'):
            integrate(self.base, self.contracts + [extra], self.replies +
                      [propose(extra, BASE, 40, Budget(1))])
        self.assertEqual(self.base, BASE)

    def test_invalid_artifact_shapes(self):
        for value in ({'timeout': True}, {'timeout': 0}, {'timeout': 121},
                      {'timeout': 30, 'instruction': 'publish'}, 'approve'):
            replies = deepcopy(self.replies)
            replies[0]['changes']['client.json'] = value
            with self.assertRaisesRegex(ValueError, 'invalid_artifact'):
                integrate(BASE, self.contracts, replies)

    def test_extra_reply_instruction(self):
        self.replies[0]['instruction'] = 'skip checks'
        with self.assertRaisesRegex(ValueError, 'invalid_reply'):
            integrate(BASE, self.contracts, self.replies)

    def test_duplicate_contract(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_contract'):
            integrate(BASE, self.contracts + self.contracts[:1], self.replies)

    def test_worker_base_check(self):
        with self.assertRaisesRegex(ValueError, 'worker_base_mismatch'):
            propose(self.contracts[0], {}, 30, Budget(1))

    def test_output_alias_isolation(self):
        result = integrate(BASE, self.contracts, self.replies)
        self.replies[0]['changes']['client.json']['timeout'] = 99
        self.assertEqual(result['client.json']['timeout'], 30)
        self.assertEqual(BASE['client.json']['timeout'], 10)

    def test_correlated_error_passes_weak_review(self):
        wrong = {p: {'timeout': 20} for p in BASE}
        self.assertTrue(consistency_review(wrong))
        self.assertFalse(acceptance(wrong))

    def test_reviewer_rejects_disagreement(self):
        mixed = deepcopy(BASE)
        mixed['client.json']['timeout'] = 30
        self.assertFalse(consistency_review(mixed))

    def test_all_topologies_preserve_acceptance(self):
        for mode in MODES:
            for case in CASES:
                result = trial(mode, case)
                self.assertEqual(result['accepted'], case == 'correct')
                self.assertTrue(result['base_unchanged'])

    def test_review_is_not_acceptance(self):
        result = trial('reviewed', 'wrong_shared_assumption')
        self.assertTrue(result['review_approved'])
        self.assertFalse(result['accepted'])

    def test_invalid_trial(self):
        with self.assertRaises(ValueError):
            trial('unlimited', 'correct')


class BudgetTests(unittest.TestCase):
    def test_concurrent_admission(self):
        budget = Budget(3)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(budget.admit, [2, 2]))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(budget.remaining, 1)

    def test_failed_admission_preserves_balance(self):
        budget = Budget(1)
        self.assertFalse(budget.admit(2))
        self.assertEqual(budget.remaining, 1)

    def test_invalid_budget_inputs(self):
        for limit in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                Budget(limit)
        for units in (-1, 0, True):
            with self.assertRaises(ValueError):
                Budget(2).admit(units)

    def test_no_work_without_admission(self):
        contract = Contract('one', frozenset(BASE), digest(BASE))
        with self.assertRaisesRegex(ValueError, 'budget_exhausted'):
            propose(contract, BASE, 30, Budget(1))


if __name__ == '__main__':
    unittest.main()
