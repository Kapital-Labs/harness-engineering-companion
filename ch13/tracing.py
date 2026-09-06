"""Local teaching trace format, not OpenTelemetry wire format."""
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ch06'))
from edits import snapshot_digest

NAMES = {'run', 'selection', 'authorization', 'export', 'verification', 'final'}
DIGESTS = {'expected_sha256', 'selected_sha256', 'observed_sha256'}
ATTRS = DIGESTS | {'claimed_success', 'matches'}


def artifact_bytes(files):
    return json.dumps(files, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':')).encode('utf-8')


def checked_attributes(attributes):
    if type(attributes) is not dict or set(attributes) - ATTRS:
        raise ValueError('unsupported_attributes')
    for key, value in attributes.items():
        if key in DIGESTS:
            if type(value) is not str or not re.fullmatch('[0-9a-f]{64}', value):
                raise ValueError('invalid_digest')
        elif type(value) is not bool:
            raise ValueError('invalid_boolean')
    return dict(attributes)


class Trace:
    def __init__(self, run_id, clock=time.perf_counter_ns):
        if type(run_id) is not str or not re.fullmatch('[a-z0-9_-]{1,64}', run_id):
            raise ValueError('invalid_run_id')
        self.run_id = run_id
        self.clock = clock
        self.spans = []

    # listing:start:start
    def start(self, name, *, parent=None, operation=None, attempt=1,
              attributes=None):
        attributes = checked_attributes(
            {} if attributes is None else attributes)
        if name not in NAMES or type(attempt) is not int or attempt < 1:
            raise ValueError('invalid_span')
        existing = {s['span_id'] for s in self.spans}
        if parent is not None and parent not in existing:
            raise ValueError('missing_parent')
        span_id = f's{len(self.spans) + 1}'
        self.spans.append({
            'span_id': span_id, 'parent_id': parent, 'name': name,
            'operation_id': operation, 'attempt': attempt,
            'start_ns': self.clock(), 'end_ns': None,
            'status': 'open', 'attributes': attributes})
        return span_id
    # listing:start:end

    def annotate(self, span_id, attributes):
        span = next(s for s in self.spans if s['span_id'] == span_id)
        if span['end_ns'] is not None:
            raise ValueError('closed_span')
        span['attributes'].update(checked_attributes(attributes))

    def end(self, span_id, status='ok'):
        span = next(s for s in self.spans if s['span_id'] == span_id)
        if status not in {'ok', 'error'} or span['end_ns'] is not None:
            raise ValueError('invalid_end')
        span['end_ns'] = self.clock()
        span['status'] = status

    def export(self):
        return json.loads(json.dumps({
            'schema': 1, 'run_id': self.run_id,
            'expected_span_count': len(self.spans), 'spans': self.spans,
            'versions': {'controller': 'ch13-v1', 'policy': 'review-v1',
                         'model': 'scripted-no-provider',
                         'adapter': 'local-json-v1'}}))


def replay(trace):
    """Validate local records and summarize them; no tools or writes."""
    if trace.get('schema') != 1 or type(trace.get('spans')) is not list:
        raise ValueError('invalid_trace')
    seen = {}; complete = len(trace['spans']) == trace.get('expected_span_count')
    for span in trace['spans']:
        sid = span['span_id']; parent = span['parent_id']
        if sid in seen or (parent is not None and parent not in seen):
            raise ValueError('invalid_span_graph')
        if span['name'] not in NAMES:
            raise ValueError('invalid_name')
        checked_attributes(span['attributes'])
        start, end = span['start_ns'], span['end_ns']
        if type(start) is not int or start < 0:
            raise ValueError('invalid_time')
        if end is None:
            complete = False
        elif type(end) is not int or end < start:
            raise ValueError('invalid_duration')
        if span['status'] not in {'open', 'ok', 'error'}:
            raise ValueError('invalid_status')
        if span['status'] == 'open':
            complete = False
        if parent is not None:
            p = seen[parent]
            if start < p['start_ns'] or (end is not None
                    and p['end_ns'] is not None and end > p['end_ns']):
                raise ValueError('outside_parent')
        seen[sid] = span
    roots = [s for s in seen.values() if s['parent_id'] is None]
    if len(roots) != 1 or roots[0]['name'] != 'run':
        raise ValueError('invalid_root')
    return {'span_count': len(seen), 'complete': complete,
            'failed_attempts': sum(s['name'] == 'export'
                                   and s['status'] == 'error'
                                   for s in seen.values())}


# listing:investigate:start
def investigate(trace, actual_bytes):
    summary = replay(trace)
    spans = trace['spans']
    if not summary['complete'] or not NAMES <= {s['name'] for s in spans}:
        return 'incomplete_trace'
    # This fixture has one decision; retries apply only to export.
    if any(sum(s['name'] == name for s in spans) != 1
           for name in NAMES - {'export'}):
        return 'incomplete_trace'
    selection = next(s for s in spans if s['name'] == 'selection')
    values = selection['attributes']
    expected = values.get('expected_sha256')
    selected = values.get('selected_sha256')
    if expected is None or selected is None:
        return 'incomplete_trace'
    exports = [s for s in spans if s['name'] == 'export']
    if actual_bytes is None:
        return ('write_failed' if all(s['status'] == 'error' for s in exports)
                else 'artifact_unavailable')
    observed = sha256(actual_bytes).hexdigest()
    if observed != selected:
        return 'export_mismatch'
    if selected != expected:
        return 'proposal_mismatch'
    return 'matching_artifact'
# listing:investigate:end


def run_case(directory, case):
    if case not in {'success', 'wrong_export', 'wrong_choice', 'write_failure'}:
        raise ValueError('unknown_case')
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'candidate.json'
    if target.exists():
        raise ValueError('fixture_requires_fresh_destination')
    base = {'review.txt': 'Old candidate', 'private.txt': 'FAKE_TRACE_SECRET'}
    candidate = {**base, 'review.txt': 'Candidate ready'}
    expected = snapshot_digest(candidate)
    trace = Trace('run-' + case)
    root = trace.start('run')
    span = trace.start('selection', parent=root,
                       attributes={'expected_sha256': expected})
    selected_files = base if case == 'wrong_choice' else candidate
    selected = snapshot_digest(selected_files)
    trace.annotate(span, {'selected_sha256': selected})
    trace.end(span)
    span = trace.start('authorization', parent=root)
    trace.end(span)  # Fixed trusted local-export permission in this fixture.
    attempts = 2 if case == 'success' else 1
    for attempt in range(1, attempts + 1):
        span = trace.start('export', parent=root, operation='export-1',
                           attempt=attempt,
                           attributes={'selected_sha256': selected})
        try:
            if case == 'write_failure' or (case == 'success' and attempt == 1):
                raise OSError('injected-before-write')
            outgoing = base if case == 'wrong_export' else selected_files
            target.write_bytes(artifact_bytes(outgoing))
        except OSError:
            trace.end(span, 'error')
        else:
            trace.end(span)
    span = trace.start('verification', parent=root)
    actual = target.read_bytes() if target.exists() else None
    observed = sha256(actual).hexdigest() if actual is not None else None
    matches = actual == artifact_bytes(candidate)
    attributes = {'expected_sha256': expected, 'matches': matches}
    if observed is not None:
        attributes['observed_sha256'] = observed
    trace.annotate(span, attributes)
    trace.end(span, 'ok' if matches else 'error')
    span = trace.start('final', parent=root, attributes={'claimed_success': True})
    trace.end(span)
    trace.end(root)  # Execution finished; task acceptance is separate.
    saved = trace.export()
    return {'case': case, 'claimed_success': True, 'artifact_matches': matches,
            'actual_sha256': observed, 'trace': saved,
            'diagnosis': investigate(saved, actual)}
