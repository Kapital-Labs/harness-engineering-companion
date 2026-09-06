"""Actual process exit after durable claim; logical clock controls expiry."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from service import Queue, fingerprint


def experiment():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'jobs.sqlite'
        queue = Queue(path)
        queue.enqueue('alpha', 'job', {'task': 'propose timeout 30'})
        command = ('import os,sys; from service import Queue; '
                   'Queue(sys.argv[1]).claim("alpha","job",0); os._exit(23)')
        child = subprocess.run([sys.executable, '-c', command, str(path)],
                               cwd=Path(__file__).resolve().parent)
        persisted = queue.inspect('alpha', 'job')
        replacement = Queue(path).claim('alpha', 'job', 10)
        stale = queue.submit('alpha', 'job', 1, {'timeout': 20}, 11)
        fresh = queue.submit('alpha', 'job', replacement, {'timeout': 30}, 11)
        approved = queue.approve('alpha', 'job', fingerprint({'timeout': 30}))
        duplicate = queue.approve('alpha', 'job', fingerprint({'timeout': 30}))
        queue.enqueue('alpha', 'cancelled', {'task': 'cancel me'})
        token = queue.claim('alpha', 'cancelled', 20)
        cancelled = queue.cancel('alpha', 'cancelled')
        late = queue.submit('alpha', 'cancelled', token, {'timeout': 30}, 21)
        result = {'child_exit': child.returncode,
                  'persisted_after_exit': {'state': persisted['state'],
                                           'generation': persisted['generation']},
                  'replacement_generation': replacement, 'stale_submit': stale,
                  'fresh_submit': fresh, 'approved': approved,
                  'duplicate_approval': duplicate, 'cancelled': cancelled,
                  'late_submit': late, 'effects': queue.effects('alpha'),
                  'other_tenant_effects': queue.effects('beta')}
    root = Path(__file__).resolve().parent
    return {**result, 'python': platform.python_version(),
            'clock': 'explicit logical seconds; no wall-clock waiting',
            'source_sha256': {p: hashlib.sha256((root/p).read_bytes()).hexdigest()
                              for p in ('service.py', 'experiment.py')}}


if __name__ == '__main__':
    print(json.dumps(experiment(), indent=2, sort_keys=True))
