"""Operator-only Docker isolation probe; never exposed as an agent tool."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

# listing:container:start
def command(image_id, stage, name):
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image_id):
        raise ValueError('Use a full local image ID, not a mutable tag')
    if not Path(stage).is_absolute() or any(c in stage for c in ',\n\r'):
        raise ValueError('Staging path must be absolute and contain no mount delimiters')
    return [
        'docker', 'run', '--rm', '--pull', 'never', '--name', name,
        '--network', 'none', '--read-only', '--user', '65534:65534',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--memory', '128m', '--memory-swap', '128m', '--cpus', '0.5',
        '--pids-limit', '32', '--log-driver', 'none',
        '--tmpfs', '/scratch:rw,noexec,nosuid,size=16m,mode=1777',
        '--mount', f'type=bind,src={stage},dst=/workspace,readonly',
        '--workdir', '/workspace', '--entrypoint', '/usr/bin/python3',
        '-i', image_id, '-I', '-',
    ]
# listing:container:end

PROBE = r'''
import fcntl, json, os, pathlib, socket, struct, sys
checks = {}
def attempt(name, action):
    try:
        action()
        checks[name] = {'succeeded': True}
    except OSError as exc:
        checks[name] = {'succeeded': False, 'error': type(exc).__name__, 'errno': exc.errno}
attempt('read_workspace', lambda: pathlib.Path('/workspace/policy.txt').read_text())
attempt('write_workspace', lambda: pathlib.Path('/workspace/new.txt').write_text('synthetic'))
attempt('write_root', lambda: pathlib.Path('/new.txt').write_text('synthetic'))
attempt('write_scratch', lambda: pathlib.Path('/scratch/new.txt').write_text('synthetic'))
attempt('read_host_canary', lambda: pathlib.Path(HOST_CANARY).read_text())
def connect():
    with socket.socket() as client:
        client.settimeout(1)
        client.connect(('192.0.2.1', 80))
attempt('external_connect', connect)
status = pathlib.Path('/proc/self/status').read_text().splitlines()
interfaces = sorted(name for _, name in socket.if_nameindex())
up = []
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    for name in interfaces:
        reply = fcntl.ioctl(sock.fileno(), 0x8913, struct.pack('256s', name.encode()))
        flags = struct.unpack_from('H', reply, 16)[0]
        if flags & 1:
            up.append(name)
print(json.dumps({'checks':checks,'uid':os.getuid(),
 'credential_present':'BOOK_FAKE_CREDENTIAL' in os.environ,
 'interfaces':interfaces, 'up_interfaces':up,
 'ipv4_routes':pathlib.Path('/proc/net/route').read_text().splitlines()[1:],
 'process_controls':[s for s in status if s.startswith(('CapEff:', 'NoNewPrivs:'))],
 'python':sys.version.split()[0]}))
'''


def assess(result):
    expected={'read_workspace':True,'write_workspace':False,'write_root':False,
              'write_scratch':True,'read_host_canary':False,'external_connect':False}
    return (all(result['checks'][k]['succeeded']==v for k,v in expected.items())
                      and result['uid']==65534 and not result['credential_present']
                      and result['up_interfaces']==['lo'] and result['ipv4_routes']==[] and result['host_canary_unchanged']
                      and result['workspace_unchanged']
                      and set(result['process_controls']) == {
                          'CapEff:\t0000000000000000', 'NoNewPrivs:\t1'})


def probe(image_id):
    # Local Docker context is an operator prerequisite: bind paths belong to its host.
    name='book-probe-'+uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='book-isolation-') as temporary:
        root=Path(temporary).resolve()
        stage=root/'stage';stage.mkdir(mode=0o755)
        (stage/'policy.txt').write_text('maintainer\n')
        (stage/'policy.txt').chmod(0o644)
        canary=root/'host-only.txt';canary.write_text('SYNTHETIC_HOST_CANARY')
        script='HOST_CANARY = '+repr(str(canary))+'\n'+PROBE
        env=dict(os.environ, BOOK_FAKE_CREDENTIAL='SYNTHETIC_CREDENTIAL')
        try:
            completed=subprocess.run(command(image_id,str(stage),name),input=script,
                text=True,capture_output=True,timeout=45,env=env,check=True)
            result=json.loads(completed.stdout)
        finally:
            # Only this randomly named probe container can be removed here.
            subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=10)
        result['host_canary_unchanged']=canary.read_text()=='SYNTHETIC_HOST_CANARY'
        result['workspace_unchanged']=not (stage/'new.txt').exists()
    result['passed']=assess(result)
    result['image_id']=image_id
    result['docker_server']=subprocess.check_output(
        ['docker','version','--format','{{.Server.Version}}'],text=True,timeout=10).strip()
    result['probe_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['kind']='executed isolation smoke probe; not an escape-resistance assessment'
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-id',required=True,help='Trusted local Linux image with /usr/bin/python3')
    args=parser.parse_args()
    try:
        result=probe(args.image_id)
    except (ValueError,OSError,subprocess.SubprocessError,json.JSONDecodeError) as exc:
        print(json.dumps({'status':'probe_error','error_type':type(exc).__name__}))
        raise SystemExit(2)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['passed'] else 1)
