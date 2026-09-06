import hashlib
import json
from pathlib import Path
import platform
import tempfile
from domains import research_summary, quality_report, support_flow


SOURCES = [
    {'id': 'release-note', 'revision': 'r1', 'question': 'default timeout',
     'value': '30 seconds'},
    {'id': 'config-reference', 'revision': 'r2', 'question': 'default timeout',
     'value': '20 seconds'},
]
ROWS = [{'id': 1, 'email': 'a@example.test'},
        {'id': 1, 'email': None}, {'id': 2, 'email': 'b@example.test'}]


def experiment():
    with tempfile.TemporaryDirectory() as folder:
        support = support_flow(Path(folder)/'support.sqlite')
    root = Path(__file__).resolve().parents[1]
    return {'research': research_summary(SOURCES, 'default timeout'),
            'research_missing': research_summary(SOURCES, 'retention period'),
            'support': support,
            'quality': quality_report(ROWS, 'batch-fixture-v1'),
            'python': platform.python_version(),
            'source_sha256': {p: hashlib.sha256((root/p).read_bytes()).hexdigest()
                              for p in ('ch20/domains.py', 'ch20/experiment.py',
                                        'ch18/service.py')}}


if __name__ == '__main__':
    print(json.dumps(experiment(), indent=2, sort_keys=True))
