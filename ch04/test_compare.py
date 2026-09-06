import unittest
from compare import compare, evidence_from_result, CASES
from tools import SnapshotTools, WindowTools, ToolCall

class ComparisonTests(unittest.TestCase):
    def test_cut_off_source_is_not_complete_evidence(self):
        files={'tracker/policy.py':'x'*2001+'\nreturn True'}
        result=SnapshotTools(files).execute(ToolCall('1','read_file',{'path':'tracker/policy.py'}))
        self.assertEqual(evidence_from_result(files,result,'prefix'),[])

    def test_search_preview_is_never_read_evidence(self):
        files={'tracker/policy.py':'def can_close_issue(): pass'}
        r=WindowTools(files).execute(ToolCall('1','search',{'query':'can_close_issue'}))
        self.assertEqual(evidence_from_result(files,r,'window'),[])

    def test_forged_span_or_text_rejected(self):
        files={'a':'one\ntwo'}
        for text,last in [('WRONG',1),('one',3)]:
            r={'ok':True,'data':{'path':'a','text':text,'first_line':1,'last_line':last}}
            self.assertEqual(evidence_from_result(files,r,'window'),[])

    def test_all_cases_retained_and_tradeoffs_visible(self):
        rows=compare()['rows']
        self.assertEqual(len(rows),len(CASES)*3)
        by={(r['case'],r['interface']):r for r in rows}
        self.assertFalse(by['long_preamble','prefix']['inspection_sufficient'])
        self.assertTrue(by['long_preamble','window']['inspection_sufficient'])
        self.assertFalse(by['oversized_line','window']['inspection_sufficient'])
        self.assertTrue(by['oversized_line','dump']['inspection_sufficient'])
        self.assertGreater(by['short','window']['tool_calls'],by['short','prefix']['tool_calls'])
        for r in rows:
            self.assertEqual(r['status'],'completed')
            self.assertGreater(r['observation_bytes'],0)
            self.assertIsNone(r['answer_correct'])

if __name__=='__main__': unittest.main()
