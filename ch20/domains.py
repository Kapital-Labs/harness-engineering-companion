"""Synthetic domain examples; exact fixture checks, no live or external work."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'ch18'))
from service import Queue, fingerprint


# listing:research:start
def research_summary(sources, question):
    relevant = [s for s in sources if s['question'] == question]
    if not relevant:
        return {'status': 'insufficient_evidence',
                'claims': [], 'sources': []}
    values = sorted({s['value'] for s in relevant})
    status = 'conflict' if len(values) > 1 else 'supported_in_fixture'
    return {'status': status,
            'claims': values,
            'sources': [{'id': s['id'], 'revision': s['revision'],
                         'value': s['value'],
                         'digest': fingerprint(s)} for s in relevant]}
# listing:research:end


def support_proposal(ticket, account, policy):
    if ticket['account'] != account['id']:
        raise ValueError('account_mismatch')
    amount = ticket['amount_cents']
    if (type(amount) is not int or amount <= 0
            or amount > policy['max_refund_cents']):
        return {'status': 'needs_specialist'}
    if ticket['order'] not in account['orders']:
        raise ValueError('order_not_owned')
    return {'status': 'proposal', 'account': account['id'],
            'order': ticket['order'], 'amount_cents': amount,
            'policy_version': policy['version']}


# listing:quality:start
def quality_report(rows, snapshot):
    seen, issues = set(), []
    for position, row in enumerate(rows):
        if row['id'] in seen:
            issues.append({'row': position, 'rule': 'duplicate_id'})
        seen.add(row['id'])
        if row['email'] is None:
            issues.append({'row': position, 'rule': 'missing_email'})
    return {'snapshot': snapshot, 'input_digest': fingerprint(rows),
            'rows_checked': len(rows), 'issues': issues,
            'proposed_action': 'review_quarantine', 'rows_deleted': 0}
# listing:quality:end


def support_flow(path):
    ticket = {'account': 'a', 'order': 'o', 'amount_cents': 1200}
    account = {'id': 'a', 'orders': ['o']}
    policy = {'version': 'refund-fixture-v1', 'max_refund_cents': 2000}
    proposal = support_proposal(ticket, account, policy)
    queue = Queue(path)
    queue.enqueue('a', 'refund-o', ticket)
    generation = queue.claim('a', 'refund-o', 0)
    queue.submit('a', 'refund-o', generation, proposal, 1)
    before = len(queue.effects('a'))
    approved = queue.approve('a', 'refund-o', fingerprint(proposal))
    duplicate = queue.approve('a', 'refund-o', fingerprint(proposal))
    return {'proposal': proposal, 'before_approval': before,
            'approved': approved, 'duplicate_approval': duplicate,
            'local_receipts': len(queue.effects('a')),
            'real_refunds': 0}
