import hashlib
import json
from pathlib import Path
import platform
from releases import experiment


def report():
    root = Path(__file__).resolve().parent
    return {**experiment(), 'python': platform.python_version(),
            'source_sha256': {p: hashlib.sha256((root/p).read_bytes()).hexdigest()
                              for p in ('releases.py', 'experiment.py')}}


if __name__ == '__main__':
    print(json.dumps(report(), indent=2, sort_keys=True))
