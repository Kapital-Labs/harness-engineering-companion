"""Fixed behavioral checks in disposable workers; not adversarial attestation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import time
import uuid
from edits import canonical, snapshot_digest
from workflow import FILES, prepare
from isolation import command

NAMES={'maintainer','administrator','viewer','unknown','caller'}
LIMIT=16384
WORKER='''import json, sys
sys.path.insert(0, '/workspace')
from tracker.policy import can_close_issue
from tracker.views import close_button_enabled
checks = {
    'maintainer': can_close_issue('maintainer') is True,
    'administrator': can_close_issue('administrator') is True,
    'viewer': can_close_issue('viewer') is False,
    'unknown': can_close_issue('unrecognized-role') is False,
    'caller': close_button_enabled('administrator') is True,
}
print(json.dumps({'checks': checks, 'python': sys.version.split()[0]}))
raise SystemExit(0 if all(checks.values()) else 1)
'''


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate key')
        result[key]=value
    return result


# listing:classify:start
def classify(exit_code, output):
    if len(output.encode('utf-8')) > LIMIT:
        return {'status': 'invalid_output'}
    if exit_code in {125, 126, 127}:
        return {'status': 'execution_error', 'exit_code': exit_code, 'output': output}
    if exit_code != 0:
        return {'status': 'failed', 'exit_code': exit_code, 'output': output}
    try:
        data = json.loads(output, object_pairs_hook=unique_object)
        checks = data['checks']
        if (set(data) != {'checks', 'python'} or not isinstance(checks, dict)
                or set(checks) != NAMES or not isinstance(data['python'], str)
                or any(type(value) is not bool for value in checks.values())):
            raise ValueError('Unexpected check result')
    except (ValueError, TypeError, KeyError, RecursionError):
        return {'status': 'invalid_output'}
    return {'status': 'passed' if all(checks.values()) else 'failed',
            'exit_code': exit_code, **data}
# listing:classify:end


def bounded_run(argv, script, timeout=45, limit=LIMIT):
    started=time.monotonic()
    process=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    chunks=bytearray()
    status=None
    try:
        try:
            process.stdin.write(script.encode());process.stdin.close()
        except BrokenPipeError:
            pass
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout,selectors.EVENT_READ)
            while selector.get_map():
                remaining=timeout-(time.monotonic()-started)
                if remaining<=0:
                    status='timeout';break
                for key,_ in selector.select(min(remaining,0.1)):
                    chunk=os.read(key.fileobj.fileno(),min(4096,limit+1-len(chunks)))
                    if not chunk:
                        selector.unregister(key.fileobj);break
                    chunks.extend(chunk)
                    if len(chunks)>limit:
                        status='output_limit';break
                if status:break
        if status is None:
            try:process.wait(timeout=max(.001,timeout-(time.monotonic()-started)))
            except subprocess.TimeoutExpired:status='timeout'
    finally:
        if process.poll() is None:process.kill()
        process.wait()
        process.stdout.close()
        if not process.stdin.closed:process.stdin.close()
    return {'transport_status':status or 'finished','exit_code':process.returncode,
            'output':bytes(chunks[:limit]).decode('utf-8',errors='replace')}


def verify(files,image_id):
    if not all(canonical(p) and isinstance(t,str) for p,t in files.items()):
        raise ValueError('Only canonical text snapshot files can be staged')
    name='book-check-'+uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='book-check-') as temporary:
        stage=Path(temporary).resolve();stage.chmod(0o755)
        for path,text in files.items():
            target=stage/path;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(text,encoding='utf-8',newline='');target.chmod(0o644)
        # Hash what was written, not just the input dictionary.
        staged={p:(stage/p).read_bytes().decode('utf-8') for p in files}
        if snapshot_digest(staged)!=snapshot_digest(files):raise ValueError('Staging mismatch')
        try:
            execution=bounded_run(command(image_id,str(stage),name),WORKER)
        finally:
            cleanup_status='unknown'
            try:
                subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=10)
                remaining=subprocess.run(['docker','ps','-a','--filter','name='+name,
                    '--format','{{.Names}}'],capture_output=True,text=True,timeout=10)
                if remaining.returncode==0:
                    cleanup_status=('remaining' if name in remaining.stdout.splitlines()
                                    else 'confirmed_absent')
            except (OSError,subprocess.SubprocessError):
                pass
        result=(classify(execution['exit_code'],execution['output'])
                if execution['transport_status']=='finished'
                else {'status':execution['transport_status']})
        result.update({'candidate_sha256':snapshot_digest(staged),'image_id':image_id,
                       'worker_sha256':hashlib.sha256(WORKER.encode()).hexdigest(),
                       'transport_status':execution['transport_status'],'cleanup_status':cleanup_status})
        return result


def experiment(image_id):
    candidate,package=prepare()
    variants={'before':FILES,'candidate':candidate,
              'overbroad':dict(candidate,**{'tracker/policy.py':'def can_close_issue(role):\n    return True\n'}),
              'syntax_error':dict(candidate,**{'tracker/policy.py':'def can_close_issue(role)\n    return True\n'})}
    checks={name:verify(files,image_id) for name,files in variants.items()}
    assert checks['candidate']['candidate_sha256']==package['candidate_sha256']
    package['verification']=checks['candidate']
    expected={'before':'failed','candidate':'passed','overbroad':'failed','syntax_error':'failed'}
    here=Path(__file__).resolve().parent
    sources=[here/'checks.py',here/'edits.py',here/'demo.py',here/'workflow.py',here.parent/'ch05/isolation.py',
             here.parent/'ch05/permissions.py',here.parent/'ch04/tools.py',here.parent/'ch02/harness.py']
    return {'kind':'executed fixed-fixture verification; not a model benchmark',
            'docker_server':subprocess.check_output(['docker','version','--format','{{.Server.Version}}'],text=True,timeout=10).strip(),
            'source_sha256':{str(p.relative_to(here.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            'cases':checks,'expected_outcomes_met':all(checks[n]['status']==s and checks[n]['cleanup_status']=='confirmed_absent'
                                        for n,s in expected.items()),
            'review_package':package}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--image-id',required=True)
    args=parser.parse_args()
    try:result=experiment(args.image_id)
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        print(json.dumps({'status':'execution_error','error_type':type(exc).__name__}));raise SystemExit(2)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['expected_outcomes_met'] else 1)
