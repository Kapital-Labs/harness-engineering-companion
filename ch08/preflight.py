"""Report this checkpoint's local prerequisites without executing repository code."""
import json
from pathlib import Path
import platform
import sys


def check(root=None):
    here=Path(__file__).resolve().parent if root is None else Path(root)
    required=['navigation.py','experiment.py','test_navigation.py','test_experiment.py']
    missing=[name for name in required if not (here/name).is_file()]
    supported=sys.version_info >= (3,11)
    return {'status':'ready' if supported and not missing else 'not_ready',
            'python':platform.python_version(),'missing':missing,
            'dependencies':'standard_library','docker_required':False,
            'behavioral_tests':'not_run'}

if __name__=='__main__':
    result=check();print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='ready' else 1)
