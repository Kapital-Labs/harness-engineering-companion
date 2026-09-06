"""SQLite job lifecycle and local artifact publication, not a remote service."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager, closing
from pathlib import Path


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


class Queue:
    def __init__(self, path):
        self.path = str(path)
        with closing(self.connect()) as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS jobs(
                tenant TEXT, id TEXT, request TEXT, request_hash TEXT,
                state TEXT, generation INTEGER DEFAULT 0, lease_until INTEGER,
                candidate TEXT, candidate_hash TEXT,
                PRIMARY KEY(tenant,id));
            CREATE TABLE IF NOT EXISTS effects(
                tenant TEXT, id TEXT, artifact TEXT, artifact_hash TEXT,
                PRIMARY KEY(tenant,id));
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def enqueue(self, tenant, job, request, quota=2):
        if not tenant or not job or type(quota) is not int or quota < 1:
            raise ValueError('invalid_admission')
        raw = json.dumps(request, sort_keys=True)
        key = fingerprint(request)
        with self.transaction() as db:
            old = db.execute('SELECT * FROM jobs WHERE tenant=? AND id=?',
                             (tenant, job)).fetchone()
            if old:
                if old['request_hash'] != key:
                    raise ValueError('idempotency_conflict')
                return False
            active = db.execute("SELECT count(*) FROM jobs WHERE tenant=? "
                                "AND state IN ('queued','running','review')",
                                (tenant,)).fetchone()[0]
            if active >= quota:
                raise ValueError('tenant_quota')
            db.execute('INSERT INTO jobs(tenant,id,request,request_hash,state) '
                       'VALUES(?,?,?,?,?)', (tenant, job, raw, key, 'queued'))
            return True

    # listing:claim:start
    def claim(self, tenant, job, now, lease=10):
        if type(now) is not int or type(lease) is not int or lease < 1:
            raise ValueError('invalid_clock_or_lease')
        with self.transaction() as db:
            row = db.execute('SELECT * FROM jobs WHERE tenant=? AND id=?',
                             (tenant, job)).fetchone()
            if row is None or not (
                row['state'] == 'queued' or
                (row['state'] == 'running' and row['lease_until'] <= now)
            ):
                return None
            generation = row['generation'] + 1
            db.execute("UPDATE jobs SET state='running', generation=?, "
                       'lease_until=? WHERE tenant=? AND id=?',
                       (generation, now + lease, tenant, job))
            return generation
    # listing:claim:end

    def submit(self, tenant, job, generation, candidate, now):
        if (type(generation) is not int or generation < 1
                or type(now) is not int):
            raise ValueError('invalid_submission')
        with self.transaction() as db:
            changed = db.execute(
                "UPDATE jobs SET state='review', candidate=?, candidate_hash=? "
                "WHERE tenant=? AND id=? AND state='running' "
                'AND generation=? AND lease_until>?',
                (json.dumps(candidate, sort_keys=True), fingerprint(candidate),
                 tenant, job, generation, now)).rowcount
            return changed == 1

    def cancel(self, tenant, job):
        with self.transaction() as db:
            return db.execute("UPDATE jobs SET state='cancelled' "
                              "WHERE tenant=? AND id=? AND state IN "
                              "('queued','running','review')",
                              (tenant, job)).rowcount == 1

    # listing:approve:start
    def approve(self, tenant, job, expected_hash):
        with self.transaction() as db:
            row = db.execute('SELECT * FROM jobs WHERE tenant=? AND id=?',
                             (tenant, job)).fetchone()
            if row is None or row['state'] != 'review':
                return False
            if row['candidate_hash'] != expected_hash:
                raise ValueError('review_candidate_changed')
            db.execute('INSERT INTO effects VALUES(?,?,?,?)',
                       (tenant, job, row['candidate'], expected_hash))
            db.execute("UPDATE jobs SET state='completed' "
                       'WHERE tenant=? AND id=?', (tenant, job))
            return True
    # listing:approve:end

    def inspect(self, tenant, job):
        with closing(self.connect()) as db:
            row = db.execute('SELECT * FROM jobs WHERE tenant=? AND id=?',
                             (tenant, job)).fetchone()
            return dict(row) if row else None

    def effects(self, tenant):
        with closing(self.connect()) as db:
            return [dict(row) for row in db.execute(
                'SELECT * FROM effects WHERE tenant=? ORDER BY id', (tenant,))]
