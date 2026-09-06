"""Persisted retry intent and a local transactional receiver simulation."""
import hashlib
import math
from pathlib import Path
import sqlite3
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]/'ch09'))
from checkpoint import Store, encoded, read_json, is_ref

class UnknownOutcome(Exception):pass
class TransientFailure(Exception):pass
class Conflict(Exception):pass


def identity(payload):
    return hashlib.sha256(encoded(payload)).hexdigest()


def valid_identifier(value):
    return isinstance(value,str) and 0<len(value)<=100


def valid_payload(payload):
    return (isinstance(payload,dict)
            and set(payload)=={'candidate_sha256','destination'}
            and is_ref(payload['candidate_sha256'])
            and isinstance(payload['destination'],str)
            and 0<len(payload['destination'])<=100)


class Receiver:
    def __init__(self,path):
        self.path=Path(path)
        db=self.connect()
        try:
            db.execute('CREATE TABLE IF NOT EXISTS effects '
                       '(id INTEGER PRIMARY KEY, payload TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS receipts '
                       '(actor TEXT, op_key TEXT, fingerprint TEXT, '
                       'effect_id INTEGER, PRIMARY KEY(actor,op_key))')
        finally:
            db.close()

    def connect(self):
        return sqlite3.connect(self.path,isolation_level=None,timeout=1)

    # listing:receiver:start
    def submit(self,actor,key,payload,fault=None):
        if (not valid_payload(payload)
                or not all(valid_identifier(v) for v in (actor,key))):
            raise ValueError('Invalid review request')
        fingerprint=identity(payload)
        if fault=='transient':
            raise TransientFailure('Rejected before acceptance')
        db=self.connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            prior=db.execute(
                'SELECT fingerprint,effect_id FROM receipts '
                'WHERE actor=? AND op_key=?',(actor,key)).fetchone()
            if prior:
                if prior[0]!=fingerprint:
                    raise Conflict('Same operation key, different request')
                effect_id=prior[1]
            else:
                cursor=db.execute('INSERT INTO effects(payload) VALUES (?)',
                                  (encoded(payload).decode(),))
                effect_id=cursor.lastrowid
                if fault=='rollback':
                    raise TransientFailure('Transaction rolled back')
                db.execute('INSERT INTO receipts VALUES (?,?,?,?)',
                           (actor,key,fingerprint,effect_id))
            db.execute('COMMIT')
        except Exception:
            if db.in_transaction:
                db.execute('ROLLBACK')
            raise
        finally:
            db.close()
        if fault=='lost_ack':
            raise UnknownOutcome('Committed response not delivered')
        return {'effect_id':effect_id,'request_sha256':fingerprint}
    # listing:receiver:end

    def count(self):
        db=self.connect()
        try:return db.execute('SELECT COUNT(*) FROM effects').fetchone()[0]
        finally:db.close()


class Journal:
    """One controller-owned operation record; single writer, no schema migration."""
    def __init__(self,root):
        self.store=Store(root)
        self.path=self.store.root/'operation.json'

    def save(self,record):
        self.store.replace(self.path,encoded(record))

    def load(self):
        record,_=read_json(self.path)
        fields={'version','actor','key','payload','state','attempts','receipt'}
        if (not isinstance(record,dict) or set(record)!=fields
                or type(record['version']) is not int or record['version']!=1
                or not all(valid_identifier(record[k]) for k in ('actor','key'))
                or not valid_payload(record['payload'])
                or record['state'] not in ('prepared','unknown','confirmed','conflict')
                or type(record['attempts']) is not int or record['attempts']<0):
            raise ValueError('Invalid operation record')
        receipt=record['receipt']
        if record['state']=='confirmed':
            if (record['attempts']<1 or not isinstance(receipt,dict)
                    or set(receipt)!={'effect_id','request_sha256'}
                    or type(receipt['effect_id']) is not int
                    or receipt['effect_id']<1
                    or receipt['request_sha256']!=identity(record['payload'])):
                raise ValueError('Invalid confirmation receipt')
        elif receipt is not None:
            raise ValueError('Unconfirmed operation has a receipt')
        return record

    def prepare(self,actor,key,payload):
        if (not valid_payload(payload)
                or not all(valid_identifier(v) for v in (actor,key))):
            raise ValueError('Invalid intent')
        if self.path.exists():
            previous=self.load()
            if (previous['actor'],previous['key'],previous['payload'])!=(actor,key,payload):
                raise Conflict('Persisted operation intent cannot change')
            return previous
        record={'version':1,'actor':actor,'key':key,'payload':payload,
                'state':'prepared','attempts':0,'receipt':None}
        self.save(record)
        return record


def delay(attempts,jitter):
    if type(attempts) is not int or not 1<=attempts<=100:
        raise ValueError('Invalid attempt count')
    if type(jitter) not in (int,float) or not 0<=jitter<=1:
        raise ValueError('Jitter must be a fraction')
    return min(8,2**min(attempts-1,3))*jitter


# listing:attempt:start
def attempt(journal,receiver,*,authorized,verified_candidate,
            remaining_seconds,max_attempts,fault=None,
            idempotent_contract=True):
    if (type(remaining_seconds) not in (int,float)
            or not math.isfinite(remaining_seconds) or remaining_seconds<0
            or type(max_attempts) is not int or not 1<=max_attempts<=100):
        raise ValueError('Invalid retry budget')
    record=journal.load()
    if record['state'] in ('confirmed','conflict'):
        return {'status':record['state'],'record':record}
    if not authorized:
        return {'status':'blocked','record':record}
    if verified_candidate!=record['payload']['candidate_sha256']:
        return {'status':'needs_verification','record':record}
    if record['state']=='unknown' and not idempotent_contract:
        return {'status':'reconcile','record':record}
    if remaining_seconds==0:
        return {'status':'deadline','record':record}
    if record['attempts']>=max_attempts:
        return {'status':'attempt_limit','record':record}
    previous_state=record['state']
    record['attempts']+=1
    record['state']='unknown'
    journal.save(record)
    try:
        receipt=receiver.submit(record['actor'],record['key'],
                                record['payload'],fault=fault)
    except UnknownOutcome:
        return {'status':'unknown','record':record}
    except TransientFailure:
        # A later rejection cannot settle an earlier unknown attempt.
        record['state']=previous_state
        journal.save(record)
        return {'status':'retryable','record':record}
    except Conflict:
        record['state']='conflict'
    else:
        record.update(state='confirmed',receipt=receipt)
    journal.save(record)
    return {'status':record['state'],'record':record}
# listing:attempt:end
