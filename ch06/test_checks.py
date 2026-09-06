import json
import unittest
from checks import classify

class ClassificationTests(unittest.TestCase):
    def payload(self,**changes):
        data={'checks':{'maintainer':True,'administrator':True,'viewer':True,'unknown':True,'caller':True},'python':'3.12.3'}
        data.update(changes);return json.dumps(data)
    def test_positive_result_requires_zero_exit_and_named_checks(self):
        self.assertEqual(classify(0,self.payload())['status'],'passed')
        self.assertEqual(classify(1,self.payload())['status'],'failed')
    def test_failed_check_cannot_pass_on_zero_exit(self):
        r=self.payload(checks={'maintainer':True,'administrator':False,'viewer':True,'unknown':True,'caller':True})
        self.assertEqual(classify(0,r)['status'],'failed')
    def test_invalid_output_is_not_passed(self):
        for output in ['success','{}',self.payload(checks={}),self.payload(checks={'maintainer':1}),'x'*17000]:
            with self.subTest(output=output[:30]):self.assertEqual(classify(0,output)['status'],'invalid_output')
    def test_docker_launch_failure_is_not_a_test_failure(self):
        self.assertEqual(classify(125,'launch failed')['status'],'execution_error')
    def test_duplicate_keys_rejected(self):
        self.assertEqual(classify(0,'{"checks":{},"checks":{}}')['status'],'invalid_output')

class RunnerTests(unittest.TestCase):
    def test_excess_output_stops_collection(self):
        import sys
        from checks import bounded_run
        r=bounded_run([sys.executable,'-c','print("x" * 20000)'],'',timeout=2,limit=100)
        self.assertEqual(r['transport_status'],'output_limit')
        self.assertLessEqual(len(r['output'].encode()),100)
    def test_hanging_worker_times_out(self):
        import sys
        from checks import bounded_run
        r=bounded_run([sys.executable,'-c','import time; time.sleep(10)'],'',timeout=.1)
        self.assertEqual(r['transport_status'],'timeout')

if __name__=='__main__':unittest.main()
