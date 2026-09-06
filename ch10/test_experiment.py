import unittest
from experiment import report

class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=report()
    def test_safe_and_naive_counts(self):
        self.assertEqual(self.data['rows'][0]['effect_count'],1)
        self.assertEqual(self.data['rows'][0]['second']['status'],'confirmed')
        self.assertEqual(self.data['naive_control']['effect_count'],2)
    def test_all_stop_reasons_preserved(self):
        rows=self.data['rows']
        self.assertEqual([r['second']['status'] for r in rows],
            ['confirmed','confirmed','blocked','reconcile','deadline',
             'needs_verification','attempt_limit'])
    def test_unknown_survives_budget_stop(self):
        self.assertEqual(self.data['rows'][4]['second']['record']['state'],'unknown')

if __name__=='__main__':unittest.main()
