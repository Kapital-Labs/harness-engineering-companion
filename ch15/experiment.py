"""Measured offline counts, hypothetical weights and scheduling; no provider."""
import hashlib
import json
from pathlib import Path
import platform
from resources import (resource_trials, accounting, cache_example, schedule,
                       cancellation_example)


def experiment():
    rows = resource_trials()
    root = Path(__file__).resolve().parents[1]
    paths = ['ch02/harness.py', 'ch02/demo.py', 'ch02/anthropic_adapter.py',
             'ch03/chapter2.py', 'ch03/candidates.py', 'ch03/evaluation.py',
             'ch03/tasks.py', 'ch14/comparison.py', 'ch15/resources.py',
             'ch15/experiment.py']
    return {
        'mode': 'offline scripted controls; estimated units and queue times',
        'python': platform.python_version(),
        'weights': {'decision_call': 100, 'serialized_input_byte': 1,
                    'tool_request': 10, 'currency': None},
        'trials': rows,
        'summaries': {c: accounting([r for r in rows if r['config'] == c])
                      for c in sorted({r['config'] for r in rows})},
        'cache': cache_example(), 'cancellation': cancellation_example(),
        'hypothetical_schedules': [schedule([100, 100, 100, 1000], n)
                                   for n in (1, 2, 4)],
        'source_sha256': {p: hashlib.sha256((root / p).read_bytes()).hexdigest()
                          for p in paths},
    }


if __name__ == '__main__':
    print(json.dumps(experiment(), indent=2, sort_keys=True))
