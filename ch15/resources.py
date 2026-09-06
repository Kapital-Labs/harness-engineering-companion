"""Offline resource accounting, immutable snapshot cache, and queue arithmetic."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import heapq
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ch14'))
from comparison import (NoReads, ReplayCandidate, FixedPolicyWorkflow,
                        SnapshotTools, run, grade, TASKS, ANSWER_CONTRACT)


class Meter:
    """Bytes of our declared JSON encoding, not provider tokens or wire bytes."""
    def __init__(self, base):
        self.base = base
        self.calls = 0
        self.input_bytes = 0

    def next(self, task, events):
        encoded = json.dumps({'task': task, 'events': [asdict(e) for e in events]},
                             sort_keys=True, ensure_ascii=False).encode('utf-8')
        self.calls += 1
        self.input_bytes += len(encoded)
        return self.base.next(task, events)


# listing:accounting:start
def accounting(rows):
    accepted = sum(row['passed'] is True for row in rows)
    unknown = sum(row['passed'] is None for row in rows)
    costs = [row['estimated_units'] for row in rows]
    total = None if any(c is None for c in costs) else sum(costs)
    return {
        'tasks': len(rows), 'accepted': accepted, 'unknown': unknown,
        'estimated_total_units': total,
        'estimated_units_per_accepted': (
            total / accepted if total is not None and accepted else None
        ),
    }
# listing:accounting:end


def resource_trials():
    rows = []
    for config in ('full', 'fixed', 'no_reads', 'declared_route'):
        for task in TASKS:
            route = config
            if config == 'declared_route':
                route = 'fixed' if task.id in {'policy', 'injection'} else 'full'
            base = (FixedPolicyWorkflow() if route == 'fixed' else
                    NoReads(task.id) if route == 'no_reads' else
                    ReplayCandidate(task.id))
            meter = Meter(base)
            result = run(meter, SnapshotTools(task.files),
                         task.question + ANSWER_CONTRACT)
            verdict = grade(task, result)
            requests = sum(e.kind == 'tool_call' for e in result.events)
            # Deliberately hypothetical weights, not currency or measured cost.
            units = 100 * meter.calls + meter.input_bytes + 10 * requests
            rows.append({'config': config, 'route': route, 'task': task.id,
                         'passed': verdict['passed'], 'checks': verdict['checks'],
                         'decision_calls': meter.calls, 'tool_requests': requests,
                         'serialized_input_bytes': meter.input_bytes,
                         'estimated_units': units, 'provider_tokens': None})
    return rows


class ReadCache(SnapshotTools):
    """Single-threaded, in-memory immutable-snapshot read cache demonstration."""
    def __init__(self, files, cache, scope, allowed, version='read-v1'):
        super().__init__(files)
        self.cache = cache
        self.scope = scope
        self.allowed = allowed
        self.version = version
        self.hits = 0
        self.misses = 0

    # listing:cache:start
    def _read(self, path):
        if path not in self.allowed:
            return {'ok': False, 'error': 'denied'}
        if path not in self.files:
            return {'ok': False, 'error': 'unknown_file'}
        digest = hashlib.sha256(self.files[path].encode('utf-8')).hexdigest()
        key = (self.scope, path, digest, self.version)
        if key in self.cache:
            self.hits += 1
            return deepcopy(self.cache[key])
        self.misses += 1
        value = super()._read(path)
        self.cache[key] = deepcopy(value)
        return value
    # listing:cache:end

    def _search(self, query):
        # Read permission also governs search disclosure.
        visible = {p: t for p, t in self.files.items() if p in self.allowed}
        return SnapshotTools(visible)._search(query)


def cache_example():
    from chapter2 import ToolCall
    cache = {}
    tool = ReadCache({'a.py': 'old\n'}, cache, 'tenant-a', {'a.py'})
    call = ToolCall('read', 'read_file', {'path': 'a.py'})
    cold = tool.execute(call)
    warm = tool.execute(call)
    tool.files['a.py'] = 'new\n'
    changed = tool.execute(call)
    tool.allowed.clear()
    denied = tool.execute(call)
    return {'cold': cold, 'warm': warm, 'changed': changed, 'denied': denied,
            'hits': tool.hits, 'misses': tool.misses}


def schedule(durations, workers):
    """FIFO jobs arriving together at t=0; fixed hypothetical service times."""
    if (type(workers) is not int or workers < 1 or
            any(type(d) is not int or d <= 0 for d in durations)):
        raise ValueError('positive_integer_workers_and_durations_required')
    available = [(0, i) for i in range(workers)]
    heapq.heapify(available)
    rows = []
    for job, duration in enumerate(durations):
        start, worker = heapq.heappop(available)
        end = start + duration
        rows.append({'job': job, 'worker': worker, 'queue_ms': start,
                     'service_ms': duration, 'completion_ms': end})
        heapq.heappush(available, (end, worker))
    return {'workers': workers, 'jobs': rows,
            'makespan_ms': max((r['completion_ms'] for r in rows), default=0),
            'service_ms_total': sum(durations)}


def cancellation_example():
    from chapter2 import ToolCall
    state = {'cancelled': False}

    class CancelDuringDecision:
        def next(self, task, events):
            state['cancelled'] = True
            return ToolCall('late', 'read_file', {'path': 'a.py'})

    meter = Meter(CancelDuringDecision())
    result = run(meter, SnapshotTools({'a.py': 'value'}), 'Read a.py',
                 cancelled=lambda: state['cancelled'])
    return {'status': result.status, 'decision_calls': meter.calls,
            'tool_requests': sum(e.kind == 'tool_call' for e in result.events)}
