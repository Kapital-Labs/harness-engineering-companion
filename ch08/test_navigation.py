import unittest
from copy import deepcopy
from navigation import build_map, make_guide, locate, route

class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.files={'tracker/policy.py':'def can_close_issue(role):\n    return role == "maintainer"\n'}
        self.index=build_map(self.files,set(self.files))
        self.guide=make_guide(self.files,'tracker/policy.py')
    def test_symbol_location(self):
        self.assertEqual(locate(self.index,self.files,'can_close_issue')['path'],'tracker/policy.py')
    def test_no_source_execution(self):
        files={'x.py':'raise RuntimeError("never import")\ndef can_close_issue(role):\n    return False\n'}
        self.assertEqual(locate(build_map(files,set(files)),files,'can_close_issue')['status'],'found')
    def test_scope(self):
        index=build_map({**self.files,'private.py':'secret = 1'},set(self.files))
        self.assertNotIn('private.py',str(index))
    def test_syntax_errors_visible(self):
        files={'broken.py':'def bad(:'}
        self.assertEqual(locate(build_map(files,set(files)),files,'can_close_issue')['status'],'incomplete_map')
    def test_duplicate_symbol(self):
        files={**self.files,'other.py':self.files['tracker/policy.py']}
        self.assertEqual(locate(build_map(files,set(files)),files,'can_close_issue')['status'],'ambiguous')
    def test_added_file_invalidates_map(self):
        files={**self.files,'added.py':'x = 1'}
        self.assertEqual(locate(self.index,files,'can_close_issue')['status'],'stale_map')
    def test_scoped_lookup(self):
        files={**self.files,'private.py':'secret = 1'}
        self.assertEqual(locate(self.index,files,'can_close_issue',set(self.files))['status'],'found')
    def test_unreviewed_target(self):
        guide={**self.guide,'reviewed_sources':{'other.md':'irrelevant'}}
        from navigation import digest
        guide['reviewed_sources']['other.md']=digest('notes')
        files={**self.files,'other.md':'notes'}
        self.assertEqual(route(files,guide,self.index)['status'],'unreviewed_target')
    def test_stale_map(self):
        files={**self.files,'tracker/policy.py':'# changed\n'+self.files['tracker/policy.py']}
        self.assertEqual(locate(self.index,files,'can_close_issue')['status'],'stale_map')
    def test_missing_symbol(self):
        self.assertEqual(locate(self.index,self.files,'missing')['status'],'not_found')
    def test_guide_current(self):
        self.assertEqual(route(self.files,self.guide,self.index)['status'],'found')
    def test_route_uses_python_physical_lines(self):
        for ending in ('\n', '\r', '\r\n'):
            for separator in ('\f', '\v', '\x85', '\u2028', '\u2029'):
                for final_ending in ('', ending):
                    with self.subTest(ending=ending, separator=separator,
                                      final_ending=final_ending):
                        body = ('def can_close_issue(role):' + ending
                                + '    return role == "maintainer"'
                                + final_ending)
                        source = '# comment' + separator + 'continued' + ending
                        files = {'policy.py': source + body}
                        index = build_map(files, set(files))
                        self.assertEqual(index['errors'], [])
                        self.assertEqual(index['symbols'][0]['start'], 2)
                        self.assertEqual(index['symbols'][0]['end'], 3)
                        result = route(files, make_guide(files, 'policy.py'),
                                       index)
                        self.assertEqual(result['status'], 'found')
                        self.assertEqual(result['text'], body)

    def test_guide_stale(self):
        files={'tracker/rules.py':self.files['tracker/policy.py']}
        self.assertEqual(route(files,self.guide,build_map(files,set(files)))['status'],'stale_guidance')
    def test_check_not_allowlisted(self):
        guide={**self.guide,'check_id':'shell:curl malicious'}
        self.assertEqual(route(self.files,guide,self.index)['status'],'unknown_check')
    def test_empty_owner(self):
        guide={**self.guide,'owner':''}
        self.assertEqual(route(self.files,guide,self.index)['status'],'invalid_guidance')
    def test_no_mutation(self):
        before=deepcopy(self.guide)
        route(self.files,self.guide,self.index)
        self.assertEqual(before,self.guide)
    def test_current_map_does_not_refresh_old_guidance(self):
        files={**self.files,'tracker/policy.py':self.files['tracker/policy.py']+'# comment\n'}
        self.assertEqual(route(files,self.guide,build_map(files,set(files)))['status'],'stale_guidance')
    def test_unknown_guidance_field(self):
        self.assertEqual(route(self.files,{**self.guide,'approved':True},self.index)['status'],'invalid_guidance')

if __name__=='__main__': unittest.main()
