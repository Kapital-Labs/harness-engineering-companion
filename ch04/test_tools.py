"""Boundary tests for the Chapter 4 read-only interfaces."""
import unittest
from tools import WindowTools, ToolCall

class ToolTests(unittest.TestCase):
    def call(self, files, name='read_file', **args):
        return WindowTools(files).execute(ToolCall('one', name, args))

    def test_window_has_exact_source_span(self):
        r=self.call({'a':'one\ntwo\nthree\n'},path='a',start_line=2,line_count=1)['data']
        self.assertEqual((r['text'],r['first_line'],r['last_line'],r['total_lines']),('two',2,2,3))
        self.assertEqual(r['next_line'],3)
        self.assertTrue(r['omitted_before'])

    def test_defaults_and_eof(self):
        r=self.call({'a':'one\ntwo'},path='a')['data']
        self.assertEqual(r['text'],'one\ntwo')
        self.assertIsNone(r['next_line'])

    def test_empty_file(self):
        r=self.call({'a':''},path='a')['data']
        self.assertEqual((r['text'],r['first_line'],r['last_line'],r['total_lines']),('',None,None,0))

    def test_range_errors(self):
        for files,start in [({'a':''},2),({'a':'one'},2)]:
            with self.subTest(files=files):
                self.assertEqual(self.call(files,path='a',start_line=start)['error'],'out_of_range')

    def test_strict_integer_bounds(self):
        for key,values in [('start_line',[True,0,-1,1.0,'1']),('line_count',[True,0,-1,101,1.0])]:
            for value in values:
                with self.subTest(key=key,value=value):
                    self.assertEqual(self.call({'a':'x'},path='a',**{key:value})['error'],'invalid_arguments')

    def test_unknown_argument(self):
        self.assertEqual(self.call({'a':'x'},path='a',offset=0)['error'],'invalid_arguments')

    def test_unknown_file_no_filesystem_fallback(self):
        self.assertEqual(self.call({},path='/etc/passwd')['error'],'unknown_file')

    def test_bad_path(self):
        for path in [[],True,'',' '*3,'a'*4001]:
            self.assertEqual(self.call({},path=path)['error'],'invalid_arguments')

    def test_complete_lines_only_under_character_budget(self):
        r=self.call({'a':'x'*1990+'\n'+'y'*20},path='a')['data']
        self.assertEqual(r['last_line'],1)
        self.assertEqual(r['next_line'],2)
        self.assertEqual(len(r['text']),1990)

    def test_oversized_first_line_is_explicit_error(self):
        self.assertEqual(self.call({'a':'x'*2001},path='a')['error'],'line_too_long')
        self.assertEqual(len(self.call({'a':'é'*2000},path='a')['data']['text']),2000)

    def test_search_order_limit_and_narrowing(self):
        files={'z':'needle','a':'\n'.join(['needle']*6)}
        r=self.call(files,'search',query='needle')['data']
        self.assertEqual([m['line'] for m in r['matches']],[1,2,3,4,5])
        self.assertTrue(r['matches_omitted'])
        r=self.call(files,'search',query='needle',path='z')['data']
        self.assertEqual(r['matches'][0]['path'],'z')
        self.assertFalse(r['matches_omitted'])

    def test_exact_match_limit_not_truncated(self):
        r=self.call({'a':'\n'.join(['q']*5)},'search',query='q')['data']
        self.assertFalse(r['matches_omitted'])

    def test_search_preview_is_not_full_evidence(self):
        r=self.call({'a':'x'*200+'needle'},'search',query='needle')['data']
        self.assertEqual(len(r['matches'][0]['text']),160)
        self.assertTrue(r['matches'][0]['text_truncated'])

    def test_empty_search_and_unknown_search_path(self):
        self.assertEqual(self.call({'a':'X'},'search',query='x')['data']['matches'],[])
        self.assertEqual(self.call({},'search',query='x',path='a')['error'],'unknown_file')

    def test_unknown_tool(self):
        self.assertEqual(self.call({},'shell',command='echo hi')['error'],'unknown_tool')

if __name__=='__main__': unittest.main()
