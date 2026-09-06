import unittest
from isolation import command
class CommandTests(unittest.TestCase):
    def test_unpinned_and_option_like_images_rejected(self):
        for image in ['ubuntu:latest','--privileged','sha256:short']:
            with self.assertRaises(ValueError):command(image,'/tmp/stage','book-probe-one')
    def test_mount_option_injection_rejected(self):
        with self.assertRaises(ValueError):command('sha256:'+'a'*64,'/tmp/a,target=/','book-probe-one')
    def test_worker_receives_only_one_readonly_mount(self):
        args=command('sha256:'+'a'*64,'/tmp/stage','book-probe-one')
        self.assertEqual(args.count('--mount'),1)
        self.assertIn('type=bind,src=/tmp/stage,dst=/workspace,readonly',args)
        self.assertNotIn('--privileged',args)
        self.assertEqual(args[args.index('--network')+1],'none')

class AssessmentTests(unittest.TestCase):
    def test_unexpected_privilege_or_interface_fails(self):
        from isolation import assess
        good={'checks':{k:{'succeeded':v} for k,v in {
            'read_workspace':True,'write_workspace':False,'write_root':False,
            'write_scratch':True,'read_host_canary':False,'external_connect':False}.items()},
            'uid':65534,'credential_present':False,'interfaces':['lo'],
            'up_interfaces':['lo'], 'ipv4_routes':[],
            'process_controls':['CapEff:\t0000000000000000','NoNewPrivs:\t1'],
            'host_canary_unchanged':True,'workspace_unchanged':True}
        self.assertTrue(assess(good))
        for key,value in [('uid',0),('up_interfaces',['lo','eth0']),('credential_present',True),
                          ('process_controls',['CapEff:\t0000000000000001','NoNewPrivs:\t1'])]:
            self.assertFalse(assess(dict(good,**{key:value})))

if __name__=='__main__':unittest.main()
