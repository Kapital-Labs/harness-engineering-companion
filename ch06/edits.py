"""Scoped exact-text edits on a single-threaded in-memory candidate."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ch05'))
from permissions import AuthorizedTools, Grant, canonical, ToolCall, Final, run


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def snapshot_digest(files):
    return digest(json.dumps(files,sort_keys=True,ensure_ascii=False,separators=(',',':')))


class EditTools:
    def __init__(self, files, read_paths, write_paths):
        self.read_grant=Grant(read_paths)
        self.write_grant=Grant(write_paths)
        if not self.write_grant.paths <= self.read_grant.paths:
            raise ValueError('This checkpoint requires read access to every writable path')
        self._files=dict(files)

    def snapshot(self):
        return dict(self._files)

    def execute(self, call):
        if call.name=='apply_edit':
            return self.apply(call.arguments)
        result=AuthorizedTools(self._files,self.read_grant).execute(call)
        if call.name=='read_file' and result.get('ok'):
            path=result['data']['path']
            result['data']['sha256']=digest(self._files[path])
        return result

    # listing:edit:start
    def apply(self, args):
        denied = {'ok': False, 'error': 'permission_denied'}
        if not isinstance(args, dict):
            return denied
        path = args.get('path')
        if not canonical(path) or path not in self.write_grant.paths:
            return denied
        keys = {'path', 'expected_sha256', 'old', 'new'}
        if (set(args) != keys
                or not isinstance(args['expected_sha256'], str)
                or not re.fullmatch(r'[0-9a-f]{64}', args['expected_sha256'])
                or not isinstance(args['old'], str) or not args['old']
                or not isinstance(args['new'], str)
                or max(len(args['old']), len(args['new'])) > 4000):
            return {'ok': False, 'error': 'invalid_arguments'}
        if path not in self._files:
            return {'ok': False, 'error': 'unknown_file'}
        before = self._files[path]
        if digest(before) != args['expected_sha256']:
            return {'ok': False, 'error': 'stale_source'}
        start = before.find(args['old'])
        if start < 0 or before.find(args['old'], start + 1) >= 0:
            return {'ok': False, 'error': 'target_not_unique'}
        after = before[:start] + args['new'] + before[start + len(args['old']):]
        if after == before:
            return {'ok': False, 'error': 'no_change'}
        if len(after) > 16000:
            return {'ok': False, 'error': 'file_limit'}
        try:
            after_sha256 = digest(after)
        except UnicodeEncodeError:
            return {'ok': False, 'error': 'invalid_arguments'}
        self._files[path] = after
        return {'ok': True, 'data': {
            'path': path, 'before_sha256': digest(before), 'sha256': after_sha256,
        }}
    # listing:edit:end


def review_package(base, candidate, trace):
    paths=sorted(p for p in set(base)|set(candidate) if base.get(p)!=candidate.get(p))
    lines=[]
    for path in paths:
        for line in difflib.unified_diff(
                base.get(path,'').splitlines(keepends=True),
                candidate.get(path,'').splitlines(keepends=True),
                fromfile='a/'+path,tofile='b/'+path):
            lines.append(line if line.endswith('\n')
                         else line+'\n\\ No newline at end of file\n')
    diff=''.join(lines)
    return {'base_sha256':snapshot_digest(base),'candidate_sha256':snapshot_digest(candidate),
            'changed_paths':paths,'diff':diff,'trace':trace,
            'verification':{'status':'not_run'},'publication':{'status':'not_requested'}}
