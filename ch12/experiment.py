"""Capture sanitized local outcomes. Known failure must remain detectable."""
from hashlib import sha256
import json
from pathlib import Path
import platform
from defenses import run_suite, incident


def experiment():
    root = Path(__file__).resolve().parents[1]
    paths = ['ch02/harness.py', 'ch04/tools.py', 'ch05/permissions.py',
             'ch11/boundary.py', 'ch12/defenses.py', 'ch12/experiment.py']
    rows = run_suite()
    return {'mode': 'scripted fixtures; local effects only',
            'python': platform.python_version(),
            'source_sha256': {p: sha256((root / p).read_bytes()).hexdigest()
                              for p in paths},
            'cases': rows, 'incident': incident(),
            'summary': {
                'forbidden_fixtures': sum(r['attempted_violation'] for r in rows),
                'executed_violations': sum(r['executed_violation'] for r in rows),
                'positive_controls': sum(not r['attempted_violation'] for r in rows),
                'known_failure_detected': any(
                    r['case'] == 'known_disclosure'
                    and r['executed_violation'] for r in rows)}}


if __name__ == '__main__':
    print(json.dumps(experiment(), indent=2, sort_keys=True))
