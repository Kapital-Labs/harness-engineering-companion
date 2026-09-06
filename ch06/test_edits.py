import unittest
from edits import EditTools, ToolCall, digest

class EditTests(unittest.TestCase):
    def setUp(self):
        self.files={'tracker/policy.py':'return role == "maintainer"\n','tests/test_policy.py':'trusted test'}
        self.tools=EditTools(self.files,{'tracker/policy.py'},{'tracker/policy.py'})
    def edit(self,**overrides):
        args={'path':'tracker/policy.py','expected_sha256':digest(self.files['tracker/policy.py']),
              'old':'role == "maintainer"','new':'role in {"maintainer", "administrator"}'}
        args.update(overrides)
        return self.tools.execute(ToolCall('edit','apply_edit',args))
    def test_allowed_edit_and_source_hash(self):
        result=self.edit()
        self.assertTrue(result['ok'])
        self.assertIn('administrator',self.tools.snapshot()['tracker/policy.py'])
        self.assertEqual(result['data']['sha256'],digest(self.tools.snapshot()['tracker/policy.py']))
        self.assertNotIn('administrator',self.files['tracker/policy.py'])
    def test_stale_edit_does_not_mutate(self):
        self.edit();before=self.tools.snapshot()
        self.assertEqual(self.edit()['error'],'stale_source')
        self.assertEqual(before,self.tools.snapshot())
    def test_missing_text(self):
        self.assertEqual(self.edit(old='missing')['error'],'target_not_unique')
        self.assertEqual(self.tools.snapshot(),self.files)
    def test_ambiguous_text(self):
        self.tools=EditTools({'tracker/policy.py':'x x'},{'tracker/policy.py'},{'tracker/policy.py'})
        r=self.edit(expected_sha256=digest('x x'),old='x',new='y')
        self.assertEqual(r['error'],'target_not_unique')
    def test_test_file_not_writable(self):
        self.assertEqual(self.edit(path='tests/test_policy.py')['error'],'permission_denied')
    def test_write_requires_its_own_grant(self):
        self.tools=EditTools(self.files,{'tracker/policy.py'},set())
        self.assertEqual(self.edit()['error'],'permission_denied')
    def test_bad_arguments(self):
        for args in [{'old':''},{'expected_sha256':'bad'},{'new':True},{'approved':True},{'new':'x'*4001}]:
            with self.subTest(args=args):self.assertEqual(self.edit(**args)['error'],'invalid_arguments')
    def test_noop_rejected(self):
        self.assertEqual(self.edit(new='role == "maintainer"')['error'],'no_change')
    def test_read_exposes_current_hash(self):
        self.edit()
        r=self.tools.execute(ToolCall('read','read_file',{'path':'tracker/policy.py'}))
        self.assertEqual(r['data']['sha256'],digest(self.tools.snapshot()['tracker/policy.py']))
    def test_returned_snapshot_does_not_mutate_candidate(self):
        copy=self.tools.snapshot();copy['tracker/policy.py']='tampered'
        self.assertEqual(self.tools.snapshot(),self.files)
    def test_no_arbitrary_check_command(self):
        r=self.tools.execute(ToolCall('check','run_checks',{'command':'echo success'}))
        self.assertEqual(r['error'],'permission_denied')
    def test_traversal_denied(self):
        self.assertEqual(self.edit(path='../tracker/policy.py')['error'],'permission_denied')

class EncodingTests(unittest.TestCase):
    def test_invalid_unicode_never_mutates_candidate(self):
        files={'a':'old'}
        tools=EditTools(files,{'a'},{'a'})
        result=tools.execute(ToolCall('x','apply_edit',{'path':'a',
            'expected_sha256':digest('old'),'old':'old','new':'\ud800'}))
        self.assertEqual(result['error'],'invalid_arguments')
        self.assertEqual(tools.snapshot(),files)
    def test_overlapping_targets_are_ambiguous(self):
        tools=EditTools({'a':'aaa'},{'a'},{'a'})
        result=tools.execute(ToolCall('x','apply_edit',{'path':'a',
            'expected_sha256':digest('aaa'),'old':'aa','new':'b'}))
        self.assertEqual(result['error'],'target_not_unique')
    def test_diff_marks_missing_final_newlines(self):
        from edits import review_package
        package=review_package({'a':'old'},{'a':'new'},[])
        self.assertIn('-old\n',package['diff'])
        self.assertIn('+new\n',package['diff'])
        self.assertEqual(package['diff'].count('No newline at end of file'),2)

if __name__=='__main__':unittest.main()
