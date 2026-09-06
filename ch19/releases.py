"""State-upgrade regression experiment; no deployment or provider calls."""
from copy import deepcopy
import hashlib
import json

TASKS = [(1, 1000), (30, 30000), (120, 120000)]
BASE_MANIFEST = {'prompt': 'timeout-task-v1', 'tool': 'reader-v1',
                 'model': 'scripted', 'policy': 'read-only-v1',
                 'state_schema': 1, 'environment': 'offline-python',
                 'grader': 'elapsed-budget-v1'}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def validate_v1(state):
    if (type(state) is not dict or set(state) != {'version', 'timeout_seconds'}
            or type(state['version']) is not int or state['version'] != 1
            or type(state['timeout_seconds']) is not int
            or not 1 <= state['timeout_seconds'] <= 120):
        raise ValueError('invalid_v1')


def migrate_bad(state):
    validate_v1(state)
    return {'version': 2, 'timeout_ms': state['timeout_seconds']}


# listing:migrate:start
def migrate(state):
    validate_v1(state)
    return {'version': 2, 'timeout_ms': state['timeout_seconds'] * 1000}


def read_budget(state):
    if type(state) is not dict:
        raise ValueError('unsupported_state')
    if state.get('version') == 1:
        validate_v1(state)
        return state['timeout_seconds'] * 1000
    if (set(state) == {'version', 'timeout_ms'}
            and type(state['version']) is int and state['version'] == 2
            and type(state['timeout_ms']) is int
            and 1 <= state['timeout_ms'] <= 120000):
        return state['timeout_ms']
    raise ValueError('unsupported_state')
# listing:migrate:end


# listing:gate:start
def release_gate(baseline, candidate, expected):
    if not expected or set(baseline) != set(expected):
        return False
    if set(candidate) != set(expected):
        return False
    if any(value is not True for value in baseline.values()):
        return False
    return all(value is True for value in candidate.values())
# listing:gate:end


def can_read_all(supported, states):
    return all(type(s.get('version')) is int and s['version'] in supported
               for s in states)


def cohort(tenant, percent):
    if type(percent) is not int or not 0 <= percent <= 100:
        raise ValueError('invalid_percent')
    bucket = int(hashlib.sha256(tenant.encode()).hexdigest()[:8], 16) % 100
    return bucket < percent


def experiment():
    rows = []
    verdicts = {}
    for config in ('baseline', 'bad_upgrade', 'fixed_upgrade'):
        verdicts[config] = {}
        for seconds, expected_ms in TASKS:
            state = {'version': 1, 'timeout_seconds': seconds}
            before = deepcopy(state)
            candidate = (state if config == 'baseline' else
                         migrate_bad(state) if config == 'bad_upgrade' else
                         migrate(state))
            actual = read_budget(candidate)
            passed = actual == expected_ms
            verdicts[config][str(seconds)] = passed
            rows.append({'config': config, 'timeout_seconds': seconds,
                         'expected_ms': expected_ms, 'actual_ms': actual,
                         'passed': passed, 'original_unchanged': before == state})
    manifests = {name: {**BASE_MANIFEST,
                       'state_schema': 1 if name == 'baseline' else 2,
                       'migration': name} for name in verdicts}
    v2 = migrate({'version': 1, 'timeout_seconds': 30})
    return {'trials': rows,
            'gates': {c: release_gate(verdicts['baseline'], verdicts[c],
                                   {str(t[0]) for t in TASKS})
                      for c in ('bad_upgrade', 'fixed_upgrade')},
            'old_reader_rollback_admitted': can_read_all({1}, [v2]),
            'bridge_reader_admitted': can_read_all({1, 2}, [v2]),
            'manifests': manifests,
            'manifest_sha256': {k: fingerprint(v) for k, v in manifests.items()},
            'cohort_20_percent': {t: cohort(t, 20) for t in
                                  ('tenant-a', 'tenant-b', 'tenant-c')}}
