"""Actual temporary file exports, scripted decisions and injected faults."""
from hashlib import sha256
import json
from pathlib import Path
import platform
import tempfile
from tracing import run_case


def experiment():
    root = Path(__file__).resolve().parents[1]
    paths = ['ch02/harness.py', 'ch04/tools.py', 'ch05/permissions.py',
             'ch06/edits.py', 'ch13/tracing.py', 'ch13/experiment.py']
    with tempfile.TemporaryDirectory() as directory:
        cases = [run_case(Path(directory) / case, case) for case in
                 ('success', 'wrong_export', 'wrong_choice', 'write_failure')]
    return {'mode': 'scripted decisions; local artifact writes',
            'python': platform.python_version(),
            'timing': 'actual perf_counter_ns; not model or service latency',
            'source_sha256': {p: sha256((root / p).read_bytes()).hexdigest()
                              for p in paths}, 'cases': cases}


def without_timing(report):
    copy = json.loads(json.dumps(report))
    for case in copy['cases']:
        for span in case['trace']['spans']:
            span.pop('start_ns'); span.pop('end_ns')
    return copy


if __name__ == '__main__':
    print(json.dumps(experiment(), indent=2, sort_keys=True))
