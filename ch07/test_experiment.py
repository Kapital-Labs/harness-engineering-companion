import unittest
from experiment import comparison, freshness_demo, projected_result
from context import observe, compose
from tasks import TASKS
from candidates import ReplayCandidate
from chapter2 import run, SnapshotTools
from evaluation import grade

class ExperimentTests(unittest.TestCase):
    def test_all_rows_retained(self):
        rows = comparison()
        self.assertEqual(len(rows), 24)
        self.assertTrue(any(not r['retained_evidence_grade']['passed'] for r in rows))
        self.assertTrue(all(r['context']['bytes'] <= r['budget'] for r in rows))

    def test_targeted_long_file(self):
        rows = [r for r in comparison() if r['task'] == 'long_policy' and r['budget'] == 1800]
        self.assertFalse(rows[0]['retained_evidence_grade']['passed'])
        self.assertTrue(rows[1]['retained_evidence_grade']['passed'])
        self.assertGreater(rows[1]['retrieval_operations'], 1)

    def test_conflict_evidence(self):
        rows = [r for r in comparison() if r['task'] == 'conflict' and r['route'] == 'targeted']
        self.assertFalse(rows[0]['retained_evidence_grade']['passed'])
        self.assertTrue(rows[1]['retained_evidence_grade']['passed'])

    def test_path_presence_is_not_evidence_sufficiency(self):
        task = TASKS[0]
        observation = observe(task.files, 'tracker/policy.py', 3, 1, 'definition-only')
        selected = compose(task=task.question, files=task.files, observations=[observation],
            readable=set(task.files), disclosable=set(task.files),
            required={'tracker/policy.py'}, budget=1800)
        self.assertEqual(selected['status'], 'ready')
        fixed = run(ReplayCandidate(task.id), SnapshotTools(task.files), task.question)
        self.assertFalse(grade(task, projected_result(fixed.answer,
            selected['payload']['evidence']))['passed'])

    def test_actual_saved_result_becomes_stale(self):
        r = freshness_demo()
        self.assertEqual(r['current']['payload']['state']['verification'], 'passed')
        self.assertEqual(r['current']['manifest'][0]['reason'], 'stale_source')
        self.assertEqual(r['later_revision']['payload']['state']['verification'], 'stale')
        self.assertEqual(r['later_revision']['status'], 'needs_context')

if __name__ == '__main__': unittest.main()
