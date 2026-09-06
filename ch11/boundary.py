"""Offline boundary fixture. Trusted controller state, no OS isolation."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ch05'))
from permissions import AuthorizedTools, Grant, ToolCall


def digest(text):
    return sha256(text.encode('utf-8')).hexdigest()


def normalize(proposal):
    if not isinstance(proposal, dict) or set(proposal) != {
        'tool', 'destination', 'body'
    }:
        raise ValueError('invalid_proposal')
    if proposal['tool'] != 'send_summary':
        raise ValueError('unknown_tool')
    if not all(type(proposal[k]) is str for k in proposal):
        raise ValueError('invalid_proposal')
    if not 1 <= len(proposal['destination']) <= 100:
        raise ValueError('invalid_destination')
    if not 1 <= len(proposal['body'].encode('utf-8')) <= 2000:
        raise ValueError('invalid_body')
    return dict(proposal)


@dataclass(frozen=True)
class Policy:
    revision: str
    readable: frozenset[str]
    disclosable: frozenset[str]
    destinations: frozenset[str]

    def __post_init__(self):
        if type(self.revision) is not str or not self.revision:
            raise ValueError('invalid_revision')
        for name in ('readable', 'disclosable', 'destinations'):
            values = frozenset(getattr(self, name))
            if not all(type(v) is str and v for v in values):
                raise ValueError('invalid_policy')
            object.__setattr__(self, name, values)
        Grant(self.readable)


@dataclass(frozen=True)
class Approval:
    run_id: str
    revision: str
    action: str
    expires_at: int


def action_identity(proposal):
    return json.dumps(proposal, sort_keys=True, ensure_ascii=True,
                      separators=(',', ':'))


class Boundary:
    def __init__(self, files, policy):
        self.files = dict(files)
        self.policy = policy
        self.approvals = {}
        self.used = set()
        self.outbox = []

    def read_for_model(self, path):
        policy = self.policy
        if type(path) is not str or path not in policy.disclosable:
            return {'ok': False, 'error': 'not_disclosable'}
        tools = AuthorizedTools(self.files, Grant(policy.readable))
        result = tools.execute(ToolCall('read-1', 'read_file', {'path': path}))
        if not result['ok']:
            return result
        return {'ok': True, 'trust': 'untrusted_source',
                'source_sha256': digest(self.files[path]), **result['data']}

    def approve(self, approval_id, run_id, proposal, expires_at):
        """Trusted UI callback only; never expose this as a model tool."""
        if (type(approval_id) is not str or not approval_id
                or approval_id in self.approvals or approval_id in self.used
                or type(run_id) is not str or not run_id
                or type(expires_at) is not int):
            raise ValueError('invalid_approval')
        action = normalize(proposal)
        if action['destination'] not in self.policy.destinations:
            raise ValueError('destination_denied')
        self.approvals[approval_id] = Approval(
            run_id, self.policy.revision, action_identity(action), expires_at)

    # listing:execute:start
    def execute(self, proposal, *, run_id, approval_id, now):
        # run_id and now come from the controller, not model arguments.
        try:
            action = normalize(proposal)
        except ValueError as exc:
            return {'ok': False, 'error': str(exc)}
        policy = self.policy
        if action['destination'] not in policy.destinations:
            return {'ok': False, 'error': 'destination_denied'}
        if (type(approval_id) is not str or type(run_id) is not str
                or type(now) is not int):
            return {'ok': False, 'error': 'invalid_context'}
        approval = self.approvals.get(approval_id)
        if approval is None or approval_id in self.used:
            return {'ok': False, 'error': 'approval_required'}
        if (approval.run_id != run_id
                or approval.revision != policy.revision
                or approval.action != action_identity(action)
                or now >= approval.expires_at):
            return {'ok': False, 'error': 'approval_mismatch'}
        self.used.add(approval_id)
        self.outbox.append(action)  # Local effect, no network transport.
        return {'ok': True, 'receipt': len(self.outbox)}
    # listing:execute:end
