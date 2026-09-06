from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from domains import research_summary, support_proposal, quality_report, support_flow
from experiment import SOURCES, ROWS


class DomainTests(unittest.TestCase):
    def test_research_preserves_conflict(self):
        report = research_summary(SOURCES, 'default timeout')
        self.assertEqual(report['status'], 'conflict')
        self.assertEqual(report['claims'], ['20 seconds', '30 seconds'])
        self.assertEqual(len(report['sources']), 2)

    def test_research_missing(self):
        self.assertEqual(research_summary(SOURCES, 'missing')['status'],
                         'insufficient_evidence')

    def test_research_claims_remain_bound_to_their_sources(self):
        for sources in (SOURCES, list(reversed(SOURCES))):
            report = research_summary(sources, 'default timeout')
            associations = {
                source['id']: (source['revision'], source['value'])
                for source in report['sources']
            }
            self.assertEqual(associations, {
                'release-note': ('r1', '30 seconds'),
                'config-reference': ('r2', '20 seconds'),
            })

    def test_single_source_scope(self):
        self.assertEqual(research_summary(SOURCES[:1], 'default timeout')['status'],
                         'supported_in_fixture')

    def test_source_change_changes_digest(self):
        changed = deepcopy(SOURCES)
        changed[0]['revision'] = 'r3'
        self.assertNotEqual(
            research_summary(SOURCES, 'default timeout')['sources'][0]['digest'],
            research_summary(changed, 'default timeout')['sources'][0]['digest'])

    def proposal(self, ticket):
        return support_proposal(ticket, {'id': 'a', 'orders': ['o']},
                                {'version': 'v1', 'max_refund_cents': 2000})

    def test_support_wrong_account(self):
        with self.assertRaisesRegex(ValueError, 'account_mismatch'):
            self.proposal({'account': 'b', 'order': 'o', 'amount_cents': 100})

    def test_support_wrong_order(self):
        with self.assertRaisesRegex(ValueError, 'order_not_owned'):
            self.proposal({'account': 'a', 'order': 'other', 'amount_cents': 100})

    def test_support_limit(self):
        for amount in (0, True, 2001):
            self.assertEqual(self.proposal({'account': 'a', 'order': 'o',
                                           'amount_cents': amount})['status'],
                             'needs_specialist')

    def test_support_exact_policy_bound(self):
        self.assertEqual(self.proposal({'account': 'a', 'order': 'o',
                                       'amount_cents': 2000})['status'], 'proposal')

    def test_support_local_delivery(self):
        with tempfile.TemporaryDirectory() as folder:
            result = support_flow(Path(folder)/'q.sqlite')
        self.assertEqual(result['before_approval'], 0)
        self.assertEqual(result['local_receipts'], 1)
        self.assertFalse(result['duplicate_approval'])
        self.assertEqual(result['real_refunds'], 0)

    def test_quality_actual_rows(self):
        before = deepcopy(ROWS)
        report = quality_report(ROWS, 's1')
        self.assertEqual(report['rows_checked'], 3)
        self.assertEqual(report['issues'], [{'row': 1, 'rule': 'duplicate_id'},
                                            {'row': 1, 'rule': 'missing_email'}])
        self.assertEqual(ROWS, before)
        self.assertEqual(report['rows_deleted'], 0)

    def test_quality_clean(self):
        self.assertEqual(quality_report(ROWS[:1], 's')['issues'], [])

    def test_quality_empty_population_visible(self):
        self.assertEqual(quality_report([], 's')['rows_checked'], 0)


if __name__ == '__main__':
    unittest.main()
