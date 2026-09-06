import unittest
from demo import demonstrate
class DemoTests(unittest.TestCase):
    def test_malicious_fixture_does_not_expand_grant(self):
        r=demonstrate()
        self.assertEqual(r['status'],'completed')
        self.assertEqual((r['permitted_results'],r['denied_results']),(2,2))
        self.assertFalse(r['private_canary_in_trace'])
        calls=[e['data']['name'] for e in r['trace'] if e['kind']=='tool_call']
        self.assertIn('shell',calls)
if __name__=='__main__':unittest.main()
