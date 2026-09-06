"""Fixed retrieval controls; neither a model run nor an answer-generation benchmark."""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import platform
import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'ch03'))
from chapter2 import Event, RunResult, SnapshotTools, run
from candidates import ReplayCandidate
from evaluation import grade
from tasks import TASKS
from context import compose, observe, encoded
from workflow import prepare, FILES

# Operator-written retrieval plans, not evaluator-provided evidence spans.
PLANS = {
    'policy': [('tracker/policy.py', 'def can_close_issue')],
    'caller': [('tracker/views.py', 'def close_button_enabled')],
    'missing': [],
    'conflict': [('tracker/policy.py', 'def can_close_issue'), ('docs.md', None)],
    'injection': [('README.md', None), ('tracker/policy.py', 'def can_close_issue')],
}


def retrieve(task, route):
    observations, calls = [], 0
    paths = sorted(task.files) if route == 'whole' else [p for p, _ in PLANS[task.id]]
    if route == 'targeted' and task.id == 'missing':
        # One literal search over the complete finite snapshot; no general absence proof.
        calls += 1
        assert not any('delete' in text for text in task.files.values())
    for i, path in enumerate(paths):
        lines = task.files[path].splitlines(keepends=True)
        start, count = 1, max(1, len(lines))
        query = dict(PLANS[task.id]).get(path) if route == 'targeted' else None
        if query:
            calls += 1
            hits = [n for n, line in enumerate(lines, 1) if query in line]
            if not hits:
                continue
            start, count = hits[0], 2
        calls += 1
        observations.append(observe(task.files, path, start, count, f'read-{i}'))
    return observations, calls


def projected_result(answer, evidence):
    """Synthetic grader input for retained evidence, never presented as the audit trace."""
    events = []
    for item in evidence:
        events.extend([
            Event('tool_call', {'call_id': item['id'], 'name': 'read_file',
                                'arguments': {'path': item['path']}}),
            Event('tool_result', {'call_id': item['id'], 'result': {'ok': True, 'data': {
                'path': item['path'], 'first_line': item['first_line'],
                'text': item['text'], 'truncated': False,
            }}}),
        ])
    return RunResult('completed', answer, tuple(events))


def comparison():
    long = replace(TASKS[0], files={**TASKS[0].files,
                   'tracker/policy.py': TASKS[0].files['tracker/policy.py'] + '# unrelated\n' * 300})
    rows = []
    for label, task in [(t.id, t) for t in TASKS] + [('long_policy', long)]:
        fixed = run(ReplayCandidate(task.id), SnapshotTools(task.files), task.question)
        for route in ['whole', 'targeted']:
            observations, calls = retrieve(task, route)
            for budget in [700, 1800]:
                selected = compose(task=task.question, files=task.files,
                    observations=observations, readable=set(task.files),
                    disclosable=set(task.files), required={p for p, _ in PLANS[task.id]},
                    budget=budget)
                evidence = selected['payload']['evidence'] if selected['payload'] else []
                retained = grade(task, projected_result(fixed.answer, evidence))
                rows.append({'task': label, 'route': route, 'budget': budget,
                    'retrieval_operations': calls, 'retrieved_bytes': len(encoded([asdict(o) for o in observations])),
                    'context': selected, 'retained_evidence_grade': retained,
                    'acquired_observations': [asdict(o) for o in observations],
                    'original_replay_events': [asdict(e) for e in fixed.events],
                    'fixed_answer': fixed.answer, 'original_replay_grade': grade(task, fixed)})
    return rows


def freshness_demo():
    candidate, package = prepare()
    saved = json.loads((HERE.parent / 'ch06/verification-report.json').read_text())
    verification = saved['cases']['candidate']
    if verification['candidate_sha256'] != package['candidate_sha256']:
        raise ValueError('Saved Chapter 6 result does not match reproduced candidate')
    old = observe(FILES, 'tracker/policy.py', 1, 2, 'old-read')
    fresh = observe(candidate, 'tracker/policy.py', 1, 2, 'new-read')
    revised = {**candidate, 'tracker/policy.py': candidate['tracker/policy.py'] + '# later revision\n'}
    result = {}
    for name, files, observations in [('current', candidate, [old, fresh]),
                                      ('later_revision', revised, [old, fresh])]:
        result[name] = compose(task='Assess the candidate verification status.', files=files,
            observations=observations, readable=set(files), disclosable=set(files),
            required={'tracker/policy.py'}, budget=1800, verification=verification)
    return result


def report():
    paths = [p for folder in ['ch02', 'ch03', 'ch04', 'ch05', 'ch06', 'ch07']
             for p in sorted((HERE.parent / folder).glob('*.py')) if not p.name.startswith('test_')]
    paths.append(HERE.parent / 'ch06/verification-report.json')
    return {'kind': 'deterministic context/retrieval controls; not model performance',
            'python': platform.python_version(),
            'source_sha256': {str(p.relative_to(HERE.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'rows': comparison(), 'freshness': freshness_demo()}

if __name__ == '__main__':
    print(json.dumps(report(), indent=2, ensure_ascii=False))
