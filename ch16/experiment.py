import hashlib
import json
from pathlib import Path
import platform
from coordination import MODES, CASES, trial


def experiment():
    root = Path(__file__).resolve().parent
    rows = [trial(mode, case) for mode in MODES for case in CASES]
    return {'mode': 'scripted proposals; actual bounded thread execution',
            'python': platform.python_version(), 'trials': rows,
            'summaries': {m: {
                'accepted': sum(r['accepted'] for r in rows if r['mode'] == m),
                'trials': len(CASES),
                'fixture_units': sum(r['fixture_units_used'] for r in rows
                                     if r['mode'] == m),
                'proposal_calls': sum(r['proposal_calls'] for r in rows
                                      if r['mode'] == m),
            } for m in MODES},
            'source_sha256': {name: hashlib.sha256((root/name).read_bytes())
                              .hexdigest() for name in
                              ('coordination.py', 'experiment.py')}}


if __name__ == '__main__':
    print(json.dumps(experiment(), indent=2, sort_keys=True))
