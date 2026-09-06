import tempfile
import unittest
from experiment import report
from preflight import check

class ExperimentTests(unittest.TestCase):
    def test_expected_outcomes(self):
        rows=report()['rows']
        self.assertEqual(len(rows),14)
        guided={r['case']:r for r in rows if r['route']=='maintained_guidance'}
        self.assertTrue(guided['moved_updated']['sufficient_definition'])
        for case,status in [('moved_stale_guide','stale_guidance'),('moved_stale_map','stale_map'),
                            ('duplicate','ambiguous'),('syntax_error','incomplete_map'),('unknown_check','unknown_check')]:
            self.assertEqual(guided[case]['result']['status'],status)
        self.assertTrue(all(r['reads']<=3 for r in rows))
    def test_guidance_has_acquisition_cost(self):
        rows=report()['rows']
        self.assertGreater(rows[1]['response_bytes'],rows[0]['response_bytes'])
        self.assertGreater(rows[1]['index_build_source_bytes'],0)
    def test_preflight_ready(self):
        self.assertEqual(check()['status'],'ready')
        self.assertEqual(check()['behavioral_tests'],'not_run')
    def test_preflight_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(check(folder)['status'],'not_ready')

if __name__=='__main__':unittest.main()
