import unittest
from experiment import report

class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=report()
    def test_before_commit_retains_previous(self):
        for row in self.report['rows'][:2]:
            self.assertEqual(row['writer_exit_code'],70)
            self.assertEqual(row['result']['revision'],1)
            self.assertEqual(row['pending_files'],1)
    def test_after_commit_retains_candidate(self):
        for row in self.report['rows'][2:]:
            self.assertEqual(row['writer_exit_code'],71)
            self.assertEqual(row['result']['revision'],2)
            self.assertEqual(row['pending_files'],0)
    def test_restored_source_matches_commit_point(self):
        rows=self.report['rows']
        self.assertIn('role == "maintainer"',rows[0]['result']['read']['data']['text'])
        self.assertIn('role in {"maintainer", "administrator"}',rows[2]['result']['read']['data']['text'])
        self.assertNotEqual(rows[0]['result']['candidate_sha256'],rows[2]['result']['candidate_sha256'])
    def test_current_grants_applied(self):
        for row in self.report['rows']:
            self.assertEqual(row['result']['read']['ok'],row['current_grants']=='read_only')
            self.assertEqual(row['result']['write_probe']['error'],'permission_denied')
    def test_poisoned_handoff(self):
        r=self.report['poisoned_handoff']['result']
        self.assertEqual(r['verification'],'stale')
        self.assertEqual(r['summary_status'],'stale')
        self.assertEqual(r['publication'],'not_requested')
    def test_corruption_rejected(self):
        self.assertEqual(self.report['corrupt_artifact']['exit_code'],2)
        self.assertEqual(self.report['corrupt_artifact']['result']['status'],'invalid_checkpoint')

if __name__=='__main__':unittest.main()
