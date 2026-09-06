"""Actual offline runtime/grader execution; no model provider or judged prose."""
import hashlib
import json
from pathlib import Path
import platform
from comparison import run_comparison


def experiment():
    root=Path(__file__).resolve().parents[1]
    paths=['ch02/harness.py','ch02/demo.py','ch02/anthropic_adapter.py',
           'ch03/chapter2.py','ch03/candidates.py','ch03/evaluation.py',
           'ch03/tasks.py','ch14/comparison.py','ch14/experiment.py',
           'ch14/rubric.md']
    return {**run_comparison(),'python':platform.python_version(),
            'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest()
                             for p in paths}}


if __name__=='__main__':print(json.dumps(experiment(),indent=2,sort_keys=True))
