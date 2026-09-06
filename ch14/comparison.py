"""Paired evaluation mechanics over public deterministic Chapter 3 tasks."""
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ch03'))
from candidates import ReplayCandidate, FixedPolicyWorkflow
from evaluation import grade, unique_object
from chapter2 import SnapshotTools, run, ToolCall
from tasks import TASKS, ANSWER_CONTRACT

SPLITS={'development':['policy','caller'], 'regression':['injection'],
        'illustrative_holdout':['missing','conflict']}
CONFIGS=('fixed_baseline','scripted_full','scripted_no_reads')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def validate_splits(splits):
    ids=[task for group in splits.values() for task in group]
    if len(ids)!=len(set(ids)) or set(ids)!={t.id for t in TASKS}:
        raise ValueError('splits_must_partition_tasks')


def validate_schedule(rows, configs, task_ids, repeats):
    expected={(c,t,r) for c in configs for t in task_ids
              for r in range(1,repeats+1)}
    actual=[(row['config'],row['task'],row['repeat']) for row in rows]
    if len(actual)!=len(set(actual)):
        raise ValueError('duplicate_trial')
    if not expected or set(actual)!=expected:
        raise ValueError('incomplete_trial_schedule')


class NoReads:
    def __init__(self, task):self.base=ReplayCandidate(task)
    def next(self, task, events):
        action=self.base.next(task,events)
        while isinstance(action,ToolCall) and action.name=='read_file':
            action=self.base.next(task,events)
        return action


def summarize(rows):
    count=len(rows); passed=sum(r['passed'] is True for r in rows)
    unknown=sum(r['passed'] is None for r in rows)
    resolved=count-unknown
    by_task={t:[r['passed'] for r in rows if r['task']==t]
             for t in sorted({r['task'] for r in rows})}
    return {'trials':count,'passed':passed,'unknown':unknown,
            'success_per_scheduled_trial':passed/count if count else None,
            'success_among_resolved':passed/resolved if resolved else None,
            'tasks':len(by_task),
            'tasks_with_mixed_outcomes':sum(
                True in values and False in values for values in by_task.values())}


# listing:paired:start
def paired(rows, candidate, baseline):
    indexed={}
    for row in rows:
        if row['config'] not in {candidate,baseline}:
            continue
        key=(row['config'],row['task'],row['repeat'])
        if key in indexed:
            raise ValueError('duplicate_trial')
        indexed[key]=row['passed']
    left={(t,r) for c,t,r in indexed if c==candidate}
    right={(t,r) for c,t,r in indexed if c==baseline}
    if not left or left!=right:
        raise ValueError('unpaired_trials')
    deltas={}
    for task in sorted({t for t,r in left}):
        pairs=[(indexed[candidate,t,r],indexed[baseline,t,r])
               for t,r in sorted(left) if t==task]
        if any(a is None or b is None for a,b in pairs):
            deltas[task]=None
        else:
            deltas[task]=sum(int(a)-int(b) for a,b in pairs)/len(pairs)
    known=[v for v in deltas.values() if v is not None]
    return {'tasks':len(deltas),'unknown_tasks':len(deltas)-len(known),
            'wins':sum(v>0 for v in known),
            'losses':sum(v<0 for v in known),
            'ties':sum(v==0 for v in known),'task_deltas':deltas,
            'mean_task_delta':sum(known)/len(known) if known else None}
# listing:paired:end


# listing:judge:start
def judge_verdict(raw):
    try:
        value=json.loads(raw,object_pairs_hook=unique_object)
    except (ValueError,TypeError,RecursionError):
        return None
    if type(value) is not dict or set(value)!={
        'grounded','limitations','evidence'
    }:
        return None
    scores=[value['grounded'],value['limitations']]
    if any(type(v) is not int or v not in {0,1,2} for v in scores):
        return None
    evidence=value['evidence']
    if (type(evidence) is not list or not evidence
            or any(type(e) is not str or e not in {'e1','e2'}
                   for e in evidence)):
        return None
    return scores==[2,2]
# listing:judge:end


def calibration():
    # Authored reference labels and judge outputs, not human/model measurements.
    cases=[('both_accept',True,(2,2)),('both_reject',False,(0,2)),
           ('false_accept',False,(2,2)),('false_reject',True,(1,2)),
           ('good_limit',True,(2,2)),('missing_limit',False,(2,0)),
           ('unknown',True,(None,2))]
    answers = {
        'both_accept': 'The file differs from the selected candidate. '
                       'Selection matches the expected candidate. '
                       'The trace does not establish why the file changed.',
        'both_reject': 'The exported candidate is correct.',
        'false_accept': 'The model selected the wrong candidate.',
        'false_reject': 'Observed and selected bytes differ despite correct '
                        'selection. The cause remains unconfirmed.',
        'good_limit': 'Inspect the export and later writes: selection was '
                      'correct, but the observed artifact differs.',
        'missing_limit': 'The exporter was malicious; the hash proves intent.',
        'unknown': 'Selection matches expectation; the observed artifact '
                   'differs. More evidence is needed to attribute the cause.'}
    rows=[]
    for name,reference,scores in cases:
        raw=json.dumps({'grounded':scores[0],'limitations':scores[1],
                        'evidence':['e1','e2']})
        verdict=judge_verdict(raw)
        rows.append({'case':name,'answer':answers[name],
                     'authored_reference':reference,
                     'judge_output':json.loads(raw),'verdict':verdict})
    resolved=[r for r in rows if r['verdict'] is not None]
    return {'mode':'authored calibration arithmetic, not a reviewer study',
            'cases':len(rows),'unknown':sum(r['verdict'] is None for r in rows),
            'false_acceptances':sum(r['verdict'] is True
                                   and not r['authored_reference'] for r in rows),
            'false_rejections':sum(r['verdict'] is False
                                  and r['authored_reference'] for r in rows),
            'agreement_resolved':sum(r['verdict']==r['authored_reference']
                                    for r in resolved)/len(resolved),
            'rows':rows}


def wilson(successes, count):
    """Illustrative 95% interval for a stated binomial sampling model."""
    if (type(successes) is not int or type(count) is not int
            or count < 1 or not 0 <= successes <= count):
        raise ValueError('invalid_binomial_counts')
    z=1.959963984540054
    p=successes/count; denominator=1+z*z/count
    center=(p+z*z/(2*count))/denominator
    half=z*math.sqrt(p*(1-p)/count+z*z/(4*count*count))/denominator
    return [max(0.0,center-half),min(1.0,center+half)]


def run_comparison():
    validate_splits(SPLITS)
    rows=[]
    for config in CONFIGS:
        for task in TASKS:
            for repeat in range(1,4):
                model=(FixedPolicyWorkflow() if config=='fixed_baseline'
                       else ReplayCandidate(task.id) if config=='scripted_full'
                       else NoReads(task.id))
                result=run(model,SnapshotTools(task.files),
                           task.question+ANSWER_CONTRACT)
                verdict=grade(task,result)
                rows.append({'config':config,'task':task.id,'repeat':repeat,
                             'split':next(k for k,v in SPLITS.items()
                                          if task.id in v),
                             'status':result.status,**verdict})
    validate_schedule(rows, CONFIGS, [t.id for t in TASKS], 3)
    return {'mode':'deterministic controls, public tasks',
            'splits':SPLITS,'repeats':3,'confidence_interval':None,
            'hypothetical_interval':{'successes':20,'trials':25,
                                     'wilson_95':wilson(20,25)},
            'suite_sha256':fingerprint([asdict(t) for t in TASKS]),
            'contract_sha256':fingerprint(ANSWER_CONTRACT),
            'summaries':{c:summarize([r for r in rows if r['config']==c])
                         for c in CONFIGS},
            'by_split':{c:{s:summarize([r for r in rows
                                       if r['config']==c and r['split']==s])
                           for s in SPLITS} for c in CONFIGS},
            'paired_full_vs_baseline':paired(rows,'scripted_full','fixed_baseline'),
            'paired_full_vs_no_reads':paired(rows,'scripted_full','scripted_no_reads'),
            'trials':rows,'calibration':calibration()}
