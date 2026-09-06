"""Single-writer local checkpoint store for bounded synthetic task artifacts."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
sys.path.append(str(Path(__file__).resolve().parents[1]/'ch06'))
from edits import EditTools, ToolCall, canonical

LIMIT=65536
FIELDS={'version','task_id','task','revision','base_ref','candidate_ref',
        'verification_ref','next_step','summary','summary_candidate_ref'}

class InvalidCheckpoint(ValueError):pass


def encoded(value):
    try:
        raw=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
    except (ValueError,TypeError,UnicodeError,RecursionError) as error:
        raise InvalidCheckpoint('Invalid JSON value') from error
    if len(raw)>LIMIT:raise InvalidCheckpoint('Artifact exceeds byte limit')
    return raw


def unique(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise InvalidCheckpoint('Duplicate JSON key')
        value[key]=item
    return value


def read_json(path):
    try:
        with path.open('rb') as f:raw=f.read(LIMIT+1)
        if len(raw)>LIMIT:raise InvalidCheckpoint('Artifact exceeds byte limit')
        value=json.loads(raw,object_pairs_hook=unique,
                         parse_constant=lambda _: (_ for _ in ()).throw(InvalidCheckpoint('Nonfinite number')))
        return value,raw
    except (OSError,ValueError,UnicodeError,RecursionError) as error:
        raise InvalidCheckpoint('Unreadable or invalid artifact') from error


def is_ref(value):
    return isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value) is not None


def files_valid(value):
    return (isinstance(value,dict) and len(value)<=100
            and all(canonical(k) and isinstance(v,str) for k,v in value.items()))


class Store:
    def __init__(self,root):
        self.root=Path(root)
        self.objects=self.root/'objects'
        self.objects.mkdir(parents=True,exist_ok=True)
        self.head=self.root/'checkpoint.json'

    def get(self,ref):
        if not is_ref(ref):raise InvalidCheckpoint('Invalid artifact reference')
        value,raw=read_json(self.objects/ref)
        if hashlib.sha256(raw).hexdigest()!=ref:
            raise InvalidCheckpoint('Artifact identity mismatch')
        return value

    def put(self,value):
        raw=encoded(value);ref=hashlib.sha256(raw).hexdigest()
        path=self.objects/ref
        if path.exists():self.get(ref)
        else:self.replace(path,raw)
        return ref

    # listing:replace:start
    def replace(self,path,raw,before_commit=None):
        fd,name=tempfile.mkstemp(prefix='.pending-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as f:
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
            if before_commit is not None:
                before_commit()
            os.replace(name,path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    # listing:replace:end

    def validate(self,cp,task_id):
        if (not isinstance(cp,dict) or set(cp)!=FIELDS
                or type(cp['version']) is not int or cp['version']!=1
                or cp['task_id']!=task_id
                or not isinstance(cp['task_id'],str) or not cp['task_id']
                or not isinstance(cp['task'],str) or not cp['task']
                or type(cp['revision']) is not int or cp['revision']<1
                or cp['next_step'] not in ('inspect_candidate','verify_candidate')
                or not isinstance(cp['summary'],str)
                or not is_ref(cp['summary_candidate_ref'])):
            raise InvalidCheckpoint('Unsupported checkpoint schema or task')
        for key in ('base_ref','candidate_ref'):
            files=self.get(cp[key])
            if not files_valid(files):raise InvalidCheckpoint('Invalid snapshot')
            encoded(files)
        if cp['verification_ref'] is not None:
            v=self.get(cp['verification_ref'])
            if (not isinstance(v,dict) or set(v)!={'status','candidate_sha256'}
                    or v['status'] not in ('passed','failed','not_run')
                    or not is_ref(v['candidate_sha256'])):
                raise InvalidCheckpoint('Invalid verification record')

    def commit(self,cp,before_commit=None):
        self.validate(cp,cp.get('task_id') if isinstance(cp,dict) else None)
        self.replace(self.head,encoded(cp),before_commit)

    def load(self,task_id):
        cp,_=read_json(self.head)
        self.validate(cp,task_id)
        return cp


def make_checkpoint(store,base,candidate,revision,verification=None):
    base_ref=store.put(base);candidate_ref=store.put(candidate)
    return {'version':1,'task_id':'issue-closure',
            'task':'Permit maintainers and administrators; deny other roles.',
            'revision':revision,'base_ref':base_ref,'candidate_ref':candidate_ref,
            'verification_ref':store.put(verification) if verification else None,
            'next_step':'verify_candidate',
            'summary':'Candidate prepared. Verification remains a separate step.',
            'summary_candidate_ref':candidate_ref}


# listing:resume:start
def resume(store,task_id,read_paths,write_paths):
    cp=store.load(task_id)
    files=store.get(cp['candidate_ref'])
    tools=EditTools(files,read_paths,write_paths)
    verification='not_run'
    if cp['verification_ref'] is not None:
        v=store.get(cp['verification_ref'])
        verification=(v['status']
                      if v['candidate_sha256']==cp['candidate_ref']
                      else 'stale')
    path='tracker/policy.py'
    source_sha=hashlib.sha256(files.get(path,'').encode()).hexdigest()
    read=tools.execute(ToolCall('resume-read','read_file',{'path':path}))
    write_probe=tools.execute(ToolCall('resume-write','apply_edit',{
        'path':path, 'expected_sha256':source_sha,
        'old':'role', 'new':'role',
    }))
    summary_status=('current_reference'
                    if cp['summary_candidate_ref']==cp['candidate_ref']
                    else 'stale')
    return {'revision':cp['revision'],
            'candidate_sha256':cp['candidate_ref'],
            'next_step':cp['next_step'],'verification':verification,
            'summary_status':summary_status,
            'summary_trust':'derived_text_not_authority',
            'read':read,'write_probe':write_probe,
            'publication':'not_requested'}
# listing:resume:end
