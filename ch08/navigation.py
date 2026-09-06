"""Finite, controller-owned repository navigation fixtures; no source execution."""
import ast
import hashlib
import io
import json


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode('utf-8')


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# Operator-owned discovery registry. Entries describe actions; route() never executes them.
CHECKS={'policy-behavior': {'chapter':'ch06', 'entrypoint':'checks.py',
                          'requires':'approved local image ID and operator invocation'}}


# listing:map:start
def build_map(files, visible):
    identities, symbols, errors = {}, [], []
    for path in sorted(visible):
        if path not in files or not path.endswith('.py'):
            continue
        identities[path] = digest(files[path])
        try:
            tree = ast.parse(files[path], filename=path)
        except SyntaxError as error:
            errors.append({'path':path, 'line':error.lineno,
                           'kind':'syntax_error'})
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                symbols.append({'name':node.name, 'path':path,
                                'start':node.lineno, 'end':node.end_lineno})
    return {'source_sha256':identities, 'symbols':symbols, 'errors':errors}
# listing:map:end


def locate(index, files, symbol, visible=None):
    scope=set(files) if visible is None else set(visible)
    current={p for p in scope if p in files and p.endswith('.py')}
    if current != set(index['source_sha256']):
        return {'status':'stale_map'}
    if any(path not in files or digest(files[path]) != sha
           for path, sha in index['source_sha256'].items()):
        return {'status':'stale_map'}
    if index['errors']:
        return {'status':'incomplete_map'}
    hits=[item for item in index['symbols'] if item['name']==symbol]
    if len(hits)!=1:
        return {'status':'ambiguous' if hits else 'not_found'}
    return {'status':'found', **hits[0]}


def make_guide(files, policy_path):
    """Fixture author explicitly records a reviewed dependency, not automatic approval."""
    return {'owner':'issue-tracker-maintainers', 'entry_symbol':'can_close_issue',
            'reviewed_sources':{policy_path:digest(files[policy_path])},
            'check_id':'policy-behavior'}


# listing:route:start
def route(files, guide, index, visible=None):
    keys={'owner','entry_symbol','reviewed_sources','check_id'}
    if (not isinstance(guide,dict) or set(guide)!=keys
            or any(not isinstance(guide[k],str) or not guide[k].strip()
                   for k in ('owner','entry_symbol','check_id'))
            or not isinstance(guide['reviewed_sources'],dict)
            or not guide['reviewed_sources']):
        return {'status':'invalid_guidance'}
    if guide['check_id'] not in CHECKS:
        return {'status':'unknown_check'}
    if any(not isinstance(path,str) or not isinstance(sha,str)
           or path not in files or digest(files[path]) != sha
           for path,sha in guide['reviewed_sources'].items()):
        return {'status':'stale_guidance'}
    location=locate(index,files,guide['entry_symbol'],visible)
    if location['status']!='found':
        return location
    path=location['path']
    if path not in guide['reviewed_sources']:
        return {'status':'unreviewed_target'}
    lines=io.StringIO(files[path], newline='').readlines()
    text=''.join(lines[
        location['start']-1:location['end']])
    return {**location, 'text':text, 'source_sha256':digest(files[path]),
            'check':dict(CHECKS[guide['check_id']]), 'verification':'not_run'}
# listing:route:end
