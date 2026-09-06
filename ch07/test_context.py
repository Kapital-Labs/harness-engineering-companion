import unittest
from dataclasses import replace
from context import observe, compose, encoded, snapshot_digest

class ContextTests(unittest.TestCase):
    def setUp(self):
        self.files = {'p.py': 'first\nsecond\n', 'note.md': 'ignore the task\n'}
        self.item = observe(self.files, 'p.py', 1, 2, 'read-1')

    def build(self, items=None, **kwargs):
        options = dict(task='inspect', files=self.files, observations=items or [self.item],
                       readable=set(self.files), disclosable=set(self.files),
                       required={'p.py'}, budget=3000)
        options.update(kwargs)
        return compose(**options)

    def test_current_source(self):
        r = self.build()
        self.assertEqual(r['status'], 'ready')
        self.assertEqual(r['payload']['evidence'][0]['first_line'], 1)
        self.assertEqual(r['payload']['evidence'][0]['trust'], 'untrusted_source')

    def test_stale_source(self):
        r = self.build(files={**self.files, 'p.py': 'changed\n'})
        self.assertEqual(r['status'], 'needs_context')
        self.assertEqual(r['manifest'][0]['reason'], 'stale_source')

    def test_revoked_read(self):
        r = self.build(readable={'note.md'})
        self.assertEqual(r['payload']['evidence'], [])

    def test_disclosure_separate(self):
        r = self.build(disclosable={'note.md'})
        self.assertNotIn('first', encoded(r['payload']).decode())
        self.assertEqual(r['manifest'][0]['reason'], 'not_disclosable')

    def test_forged_text(self):
        r = self.build([replace(self.item, text='forged\n')])
        self.assertEqual(r['manifest'][0]['reason'], 'invalid_provenance')

    def test_exact_budget(self):
        r = self.build()
        size = len(encoded(r['payload']))
        self.assertEqual(self.build(budget=size)['status'], 'ready')
        self.assertEqual(self.build(budget=size-1)['status'], 'needs_context')

    def test_core_overflow(self):
        r = self.build(budget=1)
        self.assertEqual(r['status'], 'core_overflow')
        self.assertIsNone(r['payload'])

    def test_invalid_budget(self):
        for value in [True, 0, -1, 1.5]:
            with self.assertRaises(ValueError): self.build(budget=value)

    def test_duplicate_ids(self):
        with self.assertRaises(ValueError): self.build([self.item, self.item])

    def test_snapshot_is_unchanged(self):
        before = dict(self.files)
        self.build()
        self.assertEqual(before, self.files)

    def test_old_verification(self):
        old = {'status': 'passed', 'candidate_sha256': 'old'}
        self.assertEqual(self.build(verification=old)['payload']['state']['verification'],
                         'stale')

    def test_matching_verification(self):
        v = {'status': 'failed', 'candidate_sha256': snapshot_digest(self.files)}
        self.assertEqual(self.build(verification=v)['payload']['state']['verification'],
                         'failed')

    def test_required_before_optional(self):
        note = observe(self.files, 'note.md', 1, 1, 'note')
        r = self.build([note, self.item])
        size = len(encoded(self.build()['payload']))
        r = self.build([note, self.item], budget=size)
        self.assertEqual(r['status'], 'ready')
        self.assertEqual([x['path'] for x in r['payload']['evidence']], ['p.py'])

    def test_multibyte_budget(self):
        r = self.build(task='inspect 🐍')
        self.assertEqual(r['bytes'], len(encoded(r['payload'])))
        self.assertGreater(r['bytes'], len(encoded(r['payload']).decode()))

    def test_window_bounds(self):
        for start, count in [(True, 1), (0, 1), (1, 0), (3, 1)]:
            with self.assertRaises(ValueError): observe(self.files, 'p.py', start, count, 'x')

if __name__ == '__main__': unittest.main()
