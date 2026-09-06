import tempfile
from pathlib import Path
import unittest
from retry import Receiver, Journal, attempt, UnknownOutcome, Conflict, TransientFailure

PAYLOAD={'candidate_sha256':'a'*64,'destination':'review-queue'}
class RetryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.receiver=Receiver(self.root/'receiver.db')
        self.journal=Journal(self.root/'client')
        self.journal.prepare('team-a','op-1',PAYLOAD)
    def send(self,**kw):
        opts=dict(authorized=True,verified_candidate='a'*64,
                  remaining_seconds=10,max_attempts=3)
        opts.update(kw);return attempt(self.journal,self.receiver,**opts)
    def test_same_key_one_effect(self):
        one=self.receiver.submit('team-a','x',PAYLOAD)
        two=self.receiver.submit('team-a','x',PAYLOAD)
        self.assertEqual(one,two);self.assertEqual(self.receiver.count(),1)
    def test_new_key_duplicates_intent(self):
        self.receiver.submit('team-a','x',PAYLOAD)
        self.receiver.submit('team-a','y',PAYLOAD)
        self.assertEqual(self.receiver.count(),2)
    def test_scope_is_part_of_identity(self):
        self.receiver.submit('team-a','x',PAYLOAD)
        self.receiver.submit('team-b','x',PAYLOAD)
        self.assertEqual(self.receiver.count(),2)
    def test_payload_conflict(self):
        self.receiver.submit('team-a','x',PAYLOAD)
        with self.assertRaises(Conflict):self.receiver.submit('team-a','x',{**PAYLOAD,'destination':'other'})
        self.assertEqual(self.receiver.count(),1)
    def test_lost_ack_reopened_receiver(self):
        self.assertEqual(self.send(fault='lost_ack')['status'],'unknown')
        self.receiver=Receiver(self.root/'receiver.db')
        self.journal=Journal(self.root/'client')
        self.assertEqual(self.send()['status'],'confirmed')
        self.assertEqual(self.receiver.count(),1)
        self.assertEqual(self.journal.load()['attempts'],2)
    def test_unknown_without_contract(self):
        self.send(fault='lost_ack')
        self.assertEqual(self.send(idempotent_contract=False)['status'],'reconcile')
        self.assertEqual(self.journal.load()['attempts'],1)
    def test_grant_revoked(self):
        self.send(fault='lost_ack')
        self.assertEqual(self.send(authorized=False)['status'],'blocked')
        self.assertEqual(self.receiver.count(),1)
        self.assertEqual(self.journal.load()['state'],'unknown')
    def test_candidate_precondition(self):
        self.assertEqual(self.send(verified_candidate='b'*64)['status'],'needs_verification')
        self.assertEqual(self.receiver.count(),0)
    def test_budget_before_send(self):
        self.assertEqual(self.send(remaining_seconds=0)['status'],'deadline')
        self.assertEqual(self.receiver.count(),0)
    def test_attempt_limit_persists(self):
        self.send(fault='transient',max_attempts=1)
        self.assertEqual(self.send(max_attempts=1)['status'],'attempt_limit')
    def test_transient_not_accepted(self):
        result=self.send(fault='transient')
        self.assertEqual(result['status'],'retryable')
        self.assertEqual(self.receiver.count(),0)
        self.assertEqual(self.send()['status'],'confirmed')
    def test_transaction_rollback(self):
        with self.assertRaises(TransientFailure):
            self.receiver.submit('team-a','x',PAYLOAD,fault='rollback')
        self.assertEqual(self.receiver.count(),0)
        self.receiver.submit('team-a','x',PAYLOAD)
        self.assertEqual(self.receiver.count(),1)
    def test_reprepare_cannot_change_intent(self):
        with self.assertRaises(Conflict):self.journal.prepare('team-a','op-1',{**PAYLOAD,'destination':'other'})
    def test_no_resend_confirmed(self):
        self.send();self.send()
        self.assertEqual(self.journal.load()['attempts'],1)
    def test_retry_delay_cap_and_jitter(self):
        from retry import delay
        self.assertEqual(delay(1,0.5),0.5)
        self.assertEqual(delay(10,1),8)
    def test_rejection_does_not_resolve_prior_unknown(self):
        self.send(fault='lost_ack')
        self.send(fault='transient')
        self.assertEqual(self.journal.load()['state'],'unknown')
        self.assertEqual(self.receiver.count(),1)
    def test_first_rejection_can_retry_without_idempotency(self):
        self.send(fault='transient',idempotent_contract=False)
        self.assertEqual(self.journal.load()['state'],'prepared')
        self.assertEqual(self.send(idempotent_contract=False)['status'],'confirmed')
    def test_receiver_rejects_null_identity(self):
        with self.assertRaises(ValueError):self.receiver.submit(None,'x',PAYLOAD)
        self.assertEqual(self.receiver.count(),0)
    def test_invalid_identity_never_persisted(self):
        for value in [123,True,None,'','x'*101]:
            with tempfile.TemporaryDirectory() as root:
                journal=Journal(root)
                with self.assertRaises(ValueError):journal.prepare(value,'key',PAYLOAD)
                self.assertFalse(journal.path.exists())
    def test_confirmed_requires_receipt(self):
        record=self.journal.load();record['state']='confirmed'
        self.journal.save(record)
        with self.assertRaises(ValueError):self.journal.load()
    def test_receipt_must_match_payload(self):
        self.send();record=self.journal.load()
        record['receipt']['request_sha256']='b'*64
        self.journal.save(record)
        with self.assertRaises(ValueError):self.journal.load()
    def test_receipt_requires_real_effect_and_attempt(self):
        self.send();record=self.journal.load()
        for field,value in [('effect_id',True),('effect_id',0)]:
            changed={**record,'receipt':{**record['receipt'],field:value}}
            self.journal.save(changed)
            with self.assertRaises(ValueError):self.journal.load()
        self.journal.save({**record,'attempts':0})
        with self.assertRaises(ValueError):self.journal.load()
    def test_unconfirmed_cannot_carry_receipt(self):
        self.send();record=self.journal.load();record['state']='unknown'
        self.journal.save(record)
        with self.assertRaises(ValueError):self.journal.load()
    def test_invalid_budget(self):
        for value in [True,-1,float('nan')]:
            with self.assertRaises(ValueError):self.send(remaining_seconds=value)

if __name__=='__main__':unittest.main()
