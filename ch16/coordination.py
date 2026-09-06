"""Scripted coordination controls, not live model agents or OS isolation."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from threading import Lock

BASE = {'client.json': {'timeout': 10}, 'server.json': {'timeout': 10}}
MODES = ('single', 'parallel', 'reviewed')
CASES = ('correct', 'wrong_shared_assumption', 'conflict', 'stale', 'missing')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class Contract:
    worker: str
    paths: frozenset[str]
    base_digest: str


class Budget:
    """Atomic admission of known fixture work units, with no refunds."""
    def __init__(self, limit):
        if type(limit) is not int or limit < 0:
            raise ValueError('invalid_budget')
        self.remaining = limit
        self.lock = Lock()

    def admit(self, units):
        if type(units) is not int or units < 1:
            raise ValueError('invalid_units')
        with self.lock:
            if units > self.remaining:
                return False
            self.remaining -= units
            return True


def propose(contract, snapshot, value, budget):
    if digest(snapshot) != contract.base_digest:
        raise ValueError('worker_base_mismatch')
    if not budget.admit(len(contract.paths)):
        raise ValueError('budget_exhausted')
    # Only local copies are modified; no shared candidate writes.
    local = deepcopy(snapshot)
    for path in contract.paths:
        local[path] = {'timeout': value}
    return {'worker': contract.worker, 'base_digest': contract.base_digest,
            'changes': {p: local[p] for p in sorted(contract.paths)}}


# listing:integrate:start
def integrate(base, contracts, replies):
    owners = {c.worker: c for c in contracts}
    if len(owners) != len(contracts):
        raise ValueError('duplicate_contract')
    seen, changed = set(), {}
    for reply in replies:
        if type(reply) is not dict or set(reply) != {
            'worker', 'base_digest', 'changes'
        }:
            raise ValueError('invalid_reply')
        worker = reply['worker']
        if type(worker) is not str or worker not in owners or worker in seen:
            raise ValueError('unknown_or_duplicate_worker')
        contract = owners[worker]
        if reply['base_digest'] != digest(base) or (
            contract.base_digest != digest(base)
        ):
            raise ValueError('stale_reply')
        changes = reply['changes']
        if type(changes) is not dict or set(changes) != contract.paths:
            raise ValueError('scope_or_coverage_mismatch')
        for path, value in changes.items():
            if path not in base or path in changed:
                raise ValueError('conflicting_path')
            if (type(value) is not dict or set(value) != {'timeout'}
                    or type(value['timeout']) is not int
                    or not 1 <= value['timeout'] <= 120):
                raise ValueError('invalid_artifact')
            changed[path] = deepcopy(value)
        seen.add(worker)
    if seen != set(owners) or set(changed) != set(base):
        raise ValueError('incomplete_result')
    return {**deepcopy(base), **changed}
# listing:integrate:end


# listing:review:start
def consistency_review(candidate):
    # Deliberately incomplete: equal values can both be wrong.
    return len({v['timeout'] for v in candidate.values()}) == 1


def acceptance(candidate):
    return candidate == {
        'client.json': {'timeout': 30},
        'server.json': {'timeout': 30},
    }
# listing:review:end


def trial(mode, case):
    if mode not in MODES or case not in CASES:
        raise ValueError('unknown_trial')
    base = deepcopy(BASE)
    base_id = digest(base)
    contracts = ([Contract('single', frozenset(base), base_id)]
                 if mode == 'single' else
                 [Contract(path, frozenset({path}), base_id)
                  for path in sorted(base)])
    budget = Budget(3)
    value = 20 if case == 'wrong_shared_assumption' else 30
    if mode == 'single':
        replies = [propose(contracts[0], base, value, budget)]
    else:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(propose, c, base, value, budget)
                       for c in contracts]
            replies = [f.result() for f in futures]
    # Controller-side malformed handoff fixtures, applied to every topology.
    if case == 'conflict':
        extra = Contract('overlap', frozenset({'client.json'}), base_id)
        contracts.append(extra)
        replies.append(propose(extra, base, 40, budget))
    elif case == 'stale':
        replies[0]['base_digest'] = 'old'
    elif case == 'missing':
        replies.pop()
    review = None
    candidate = None
    status = 'assembled'
    try:
        candidate = integrate(base, contracts, replies)
        if mode == 'reviewed':
            if not budget.admit(1):
                raise ValueError('review_budget_exhausted')
            review = consistency_review(candidate)
        passed = acceptance(candidate) and review is not False
    except ValueError as exc:
        status = str(exc)
        passed = False
    return {'mode': mode, 'case': case, 'accepted': passed,
            'status': status, 'review_approved': review,
            'proposal_calls': len(contracts), 'reply_count': len(replies),
            'fixture_units_used': 3 - budget.remaining,
            'candidate': candidate, 'base_unchanged': base == BASE,
            'candidate_digest': digest(candidate) if candidate else None}
