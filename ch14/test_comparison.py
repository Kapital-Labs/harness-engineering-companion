import json
import unittest
from comparison import (run_comparison, paired, summarize, judge_verdict,
                        calibration, validate_splits, SPLITS, wilson)


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.report = run_comparison()

    def test_trials_have_unique_keys(self):
        rows=self.report['trials']
        self.assertEqual(len(rows),45)
        self.assertEqual(len({(r['config'],r['task'],r['repeat']) for r in rows}),45)

    def test_scripted_full_passes(self):
        self.assertEqual(self.report['summaries']['scripted_full']['passed'],15)

    def test_no_reads_ablation(self):
        self.assertEqual(self.report['summaries']['scripted_no_reads']['passed'],3)

    def test_baseline(self):
        self.assertEqual(self.report['summaries']['fixed_baseline']['passed'],6)

    def test_pair_task_counts_not_repeat_counts(self):
        p=self.report['paired_full_vs_baseline']
        self.assertEqual((p['wins'],p['losses'],p['ties']),(3,0,2))
        self.assertEqual(p['tasks'],5)

    def test_pair_missing_row_rejected(self):
        rows=self.report['trials'][:-1]
        with self.assertRaises(ValueError):
            paired(rows,'scripted_full','scripted_no_reads')

    def test_shared_missing_trial_rejected_by_schedule(self):
        from comparison import validate_schedule, CONFIGS, TASKS
        rows=[r for r in self.report['trials']
              if not (r['task']=='policy' and r['repeat']==2)]
        # Pair equality alone cannot detect the omission from both sides.
        paired(rows,'scripted_full','fixed_baseline')
        with self.assertRaisesRegex(ValueError,'incomplete_trial_schedule'):
            validate_schedule(rows, CONFIGS, [t.id for t in TASKS], 3)

    def test_explicit_unknown_keeps_schedule_complete(self):
        from comparison import validate_schedule, CONFIGS, TASKS
        rows=[dict(r) for r in self.report['trials']]
        rows[0]['passed']=None
        validate_schedule(rows, CONFIGS, [t.id for t in TASKS], 3)
        self.assertEqual(summarize(rows)['unknown'],1)

    def test_duplicate_row_rejected(self):
        rows=self.report['trials']+[self.report['trials'][0]]
        with self.assertRaises(ValueError): paired(rows,'scripted_full','fixed_baseline')

    def test_repeats_not_variation(self):
        for summary in self.report['summaries'].values():
            self.assertEqual(summary['tasks_with_mixed_outcomes'],0)

    def test_unknowns_not_dropped(self):
        s=summarize([{'task':'a','passed':True}, {'task':'a','passed':None}])
        self.assertEqual(s['trials'],2)
        self.assertEqual(s['unknown'],1)
        self.assertEqual(s['success_per_scheduled_trial'],0.5)
        self.assertEqual(s['success_among_resolved'],1.0)

    def test_empty_summary(self):
        self.assertIsNone(summarize([])['success_per_scheduled_trial'])

    def test_split_overlap_rejected(self):
        bad={**SPLITS,'regression':['policy']}
        with self.assertRaises(ValueError):validate_splits(bad)

    def test_split_missing_rejected(self):
        with self.assertRaises(ValueError):validate_splits({'development':['policy']})

    def test_valid_judgment(self):
        self.assertTrue(judge_verdict(
            '{"grounded":2,"limitations":2,"evidence":["e1"]}'))

    def test_judge_abstention(self):
        self.assertIsNone(judge_verdict(
            '{"grounded":null,"limitations":2,"evidence":[]}'))

    def test_malformed_judge_does_not_pass(self):
        for raw in ('yes','{}','{"grounded":2,"grounded":0,"limitations":2,"evidence":["e1"]}',
                    '{"grounded":true,"limitations":2,"evidence":["e1"]}',
                    '{"grounded":2,"limitations":2,"evidence":["invented"]}'):
            with self.subTest(raw=raw):self.assertIsNone(judge_verdict(raw))

    def test_no_evidence_not_accepted(self):
        self.assertIsNone(judge_verdict(
            '{"grounded":2,"limitations":2,"evidence":[]}'))

    def test_calibration_errors_visible(self):
        c=calibration()
        self.assertEqual(c['false_acceptances'],1)
        self.assertEqual(c['false_rejections'],1)
        self.assertEqual(c['unknown'],1)
        self.assertEqual(c['cases'],7)

    def test_report_round_trip(self):
        self.assertEqual(json.loads(json.dumps(self.report)),self.report)

    def test_attacks_retained(self):
        rows=[r for r in self.report['trials']
              if r['task']=='injection' and r['config']=='scripted_full']
        self.assertTrue(all(r['unauthorized_attempts']==1
                            and r['unauthorized_executions']==0 for r in rows))

    def test_wilson_example(self):
        low,high=wilson(20,25)
        self.assertAlmostEqual(low,0.6087,places=4)
        self.assertAlmostEqual(high,0.9114,places=4)

    def test_wilson_boundaries(self):
        self.assertAlmostEqual(wilson(0,10)[0],0)
        self.assertAlmostEqual(wilson(10,10)[1],1)

    def test_wilson_invalid_counts(self):
        for args in ((1,0),(-1,10),(11,10),(True,10)):
            with self.assertRaises(ValueError):wilson(*args)

    def test_paired_unknown_task_retained(self):
        rows=[{'config':c,'task':t,'repeat':1,'passed':value}
              for c,t,value in [('a','unknown',None),('b','unknown',True),
                                ('a','known',True),('b','known',False)]]
        result=paired(rows,'a','b')
        self.assertEqual(result['tasks'],2)
        self.assertEqual(result['unknown_tasks'],1)
        self.assertEqual(result['task_deltas'],{'known':1.0,'unknown':None})
        self.assertEqual(result['mean_task_delta'],1.0)
        self.assertEqual((result['wins'],result['losses'],result['ties']),
                         (1,0,0))

    def test_no_live_inference(self):
        self.assertEqual(self.report['mode'],'deterministic controls, public tasks')
        self.assertIsNone(self.report['confidence_interval'])


if __name__=='__main__':unittest.main()
