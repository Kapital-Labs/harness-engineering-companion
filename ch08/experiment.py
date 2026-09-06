"""Fixed navigation routes under a three-read budget, with indexing cost separate."""
import hashlib
import json
from pathlib import Path
import platform
from navigation import build_map, make_guide, route, encoded

SOURCE='def can_close_issue(role):\n    return role == "maintainer"\n'
ORIGINAL={'tracker/policy.py':SOURCE, 'tracker/views.py':'# Caller fixture; not executed here.\n'}
MOVED={'core/rules.py':SOURCE, 'tracker/views.py':ORIGINAL['tracker/views.py']}
TASK='Locate the current definition of can_close_issue and inspect its body.'


def blind(files):
    acquired=[]
    for path in ['tracker/policy.py','legacy/policy.py','src/policy.py']:
        result={'path':path,'text':files[path]} if path in files else {'error':'unknown_file','path':path}
        acquired.append(result)
        if path in files:
            return {'status':'found','path':path,'text':files[path]}, acquired
    return {'status':'not_found'}, acquired


def report():
    original_map=build_map(ORIGINAL,set(ORIGINAL))
    old_guide=make_guide(ORIGINAL,'tracker/policy.py')
    duplicate={**MOVED,'other/rules.py':SOURCE}
    broken={**MOVED,'broken.py':'def broken(:'}
    cases=[('original',ORIGINAL,old_guide,original_map),
           ('moved_updated',MOVED,make_guide(MOVED,'core/rules.py'),build_map(MOVED,set(MOVED))),
           ('moved_stale_guide',MOVED,old_guide,build_map(MOVED,set(MOVED))),
           ('moved_stale_map',MOVED,make_guide(MOVED,'core/rules.py'),original_map),
           ('duplicate',duplicate,make_guide(duplicate,'core/rules.py'),build_map(duplicate,set(duplicate))),
           ('syntax_error',broken,make_guide(broken,'core/rules.py'),build_map(broken,set(broken))),
           ('unknown_check',ORIGINAL,{**old_guide,'check_id':'run-anything'},original_map)]
    rows=[]
    for name,files,guide,index in cases:
        for mode in ['guessed_paths','maintained_guidance']:
            if mode=='guessed_paths':
                result,acquired=blind(files)
            else:
                result=route(files,guide,index)
                acquired=[guide,index]
                if result['status']=='found': acquired.append(result)
            expected_path='tracker/policy.py' if files==ORIGINAL else 'core/rules.py'
            sufficient=(result['status']=='found' and result.get('path')==expected_path
                        and result.get('text')==SOURCE)
            rows.append({'case':name,'route':mode,'task':TASK,'read_budget':3,
                'reads':len(acquired),'response_bytes':len(encoded(acquired)),
                'index_build_source_bytes':sum(len(files[p].encode('utf-8')) for p in files if p.endswith('.py')) if mode=='maintained_guidance' and name!='moved_stale_map' else 0,
                'index_reused_stale':mode=='maintained_guidance' and name=='moved_stale_map',
                'result':result,'sufficient_definition':sufficient,
                'acquired':acquired,'verification':'not_run'})
    here=Path(__file__).resolve().parent
    return {'kind':'deterministic navigation controls, not model performance',
            'python':platform.python_version(),'rows':rows,
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(here.glob('*.py')) if not p.name.startswith('test_')}}

if __name__=='__main__':print(json.dumps(report(),indent=2))
