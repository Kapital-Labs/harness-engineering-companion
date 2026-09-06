"""Actual local effects with simulated delivery failures; no external requests."""
import hashlib
import json
from pathlib import Path
import platform
import sqlite3
import tempfile
from retry import Receiver, Journal, attempt, UnknownOutcome, delay

PAYLOAD={'candidate_sha256':'a'*64,'destination':'review-queue'}


def report():
    cases=[('lost_ack_same_key','lost_ack',{}),
           ('known_rejection','transient',{}),
           ('grant_revoked','lost_ack',{'authorized':False}),
           ('no_idempotency_contract','lost_ack',{'idempotent_contract':False}),
           ('deadline_exhausted','lost_ack',{'remaining_seconds':0}),
           ('candidate_changed','transient',{'verified_candidate':'b'*64}),
           ('attempts_exhausted','transient',{'max_attempts':1})]
    rows=[]
    for name,fault,change in cases:
        with tempfile.TemporaryDirectory(prefix='book-ch10-') as root:
            root=Path(root)
            receiver=Receiver(root/'receiver.db');journal=Journal(root/'client')
            journal.prepare('team-a','review-1',PAYLOAD)
            args=dict(authorized=True,verified_candidate='a'*64,
                      remaining_seconds=10,max_attempts=3)
            first=attempt(journal,receiver,fault=fault,**args)
            # Reopen both durable records; this is not a fresh OS process.
            receiver=Receiver(root/'receiver.db');journal=Journal(root/'client')
            second=attempt(journal,receiver,**{**args,**change})
            rows.append({'case':name,'first':first,'second':second,
                         'effect_count':receiver.count()})
    with tempfile.TemporaryDirectory(prefix='book-ch10-naive-') as root:
        receiver=Receiver(Path(root)/'receiver.db')
        try:receiver.submit('team-a','first-key',PAYLOAD,fault='lost_ack')
        except UnknownOutcome:pass
        receiver.submit('team-a','new-key',PAYLOAD)
        naive={'case':'new_key_after_lost_ack','effect_count':receiver.count()}
    here=Path(__file__).resolve().parent
    sources=[p for directory in ['ch02','ch04','ch05','ch06','ch09','ch10']
             for p in (here.parent/directory).glob('*.py')]
    return {'kind':'local receiver simulation with actual SQLite effects; no model calls',
            'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,
            'verification':'synthetic hash precondition; no behavioral checks executed',
            'rows':rows,'naive_control':naive,
            'delay_examples_seconds':[delay(i,0.5) for i in range(1,7)],
            'source_sha256':{str(p.relative_to(here.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources) if not p.name.startswith('test_')}}

if __name__=='__main__':print(json.dumps(report(),indent=2))
