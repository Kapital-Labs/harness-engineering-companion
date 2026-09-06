"""Read-only, in-memory tools. No filesystem, shell, network, or model calls."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ch02'))
from harness import ToolCall, SnapshotTools, Final, run

MAX_TEXT = 2000
MAX_LINES = 100
MAX_MATCHES = 5


def error(code, message):
    return {'ok': False, 'error': code, 'message': message}


def valid_string(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 4000


# Documentation contract; execute remains the enforcement point.
TOOL_SCHEMAS = [
    {'name': 'read_file', 'description': 'Read complete source lines from a snapshot path. '
     'At most 100 lines and 2000 source characters; use next_line to continue.',
     'input_schema': {'type': 'object', 'properties': {
         'path': {'type': 'string', 'minLength': 1, 'maxLength': 4000},
         'start_line': {'type': 'integer', 'minimum': 1, 'default': 1},
         'line_count': {'type': 'integer', 'minimum': 1, 'maximum': 100, 'default': 40},
     }, 'required': ['path'], 'additionalProperties': False}},
    {'name': 'search', 'description': 'Find a literal case-sensitive string, optionally '
     'within one exact snapshot path. Returns five previews; narrow the query or path '
     'if matches_omitted is true.',
     'input_schema': {'type': 'object', 'properties': {
         'query': {'type': 'string', 'minLength': 1, 'maxLength': 4000},
         'path': {'type': 'string', 'minLength': 1, 'maxLength': 4000},
     }, 'required': ['query'], 'additionalProperties': False}},
]


class WindowTools:
    """Trusted caller supplies a finite dictionary of source strings."""
    def __init__(self, files: dict[str, str]):
        self.files = dict(files)

    def execute(self, call: ToolCall) -> dict:
        if call.name not in {'search', 'read_file'}:
            return error('unknown_tool', 'Available tools: search, read_file.')
        args = call.arguments
        if not isinstance(args, dict):
            return error('invalid_arguments', 'Arguments must be an object.')
        if call.name == 'read_file':
            return self.read(args)
        return self.search(args)

    # listing:validate:start
    def read(self, args: dict) -> dict:
        if (set(args) - {'path', 'start_line', 'line_count'}
                or not valid_string(args.get('path'))):
            return error('invalid_arguments', 'Provide path and optional line window.')
        start = args.get('start_line', 1)
        count = args.get('line_count', 40)
        if (type(start) is not int or start < 1
                or type(count) is not int or not 1 <= count <= MAX_LINES):
            return error('invalid_arguments',
                         'start_line must be a positive integer; line_count: 1..100.')
        path = args['path']
        if path not in self.files:
            return error('unknown_file', 'Use a path from the supplied snapshot.')
        lines = self.files[path].splitlines()
        if start > max(1, len(lines)):
            return error('out_of_range', 'start_line is beyond the end of this file.')
        return self.window(path, lines, start, count)
    # listing:validate:end

    # listing:window:start
    def window(self, path: str, lines: list[str], start: int, count: int) -> dict:
        selected = []
        used = 0
        for line in lines[start - 1:start - 1 + count]:
            required = len(line) + (1 if selected else 0)
            if used + required > MAX_TEXT:
                break
            selected.append(line)
            used += required
        if not selected and lines:
            return error('line_too_long',
                         'The first requested line exceeds the source character limit.')
        last = start + len(selected) - 1 if selected else None
        return {'ok': True, 'data': {
            'path': path, 'text': '\n'.join(selected),
            'first_line': start if selected else None, 'last_line': last,
            'total_lines': len(lines), 'omitted_before': start > 1,
            'next_line': last + 1 if last is not None and last < len(lines) else None,
        }}
    # listing:window:end

    def search(self, args: dict) -> dict:
        if (set(args) - {'query', 'path'} or not valid_string(args.get('query'))
                or ('path' in args and not valid_string(args['path']))):
            return error('invalid_arguments', 'Provide query and optional exact path.')
        if 'path' in args and args['path'] not in self.files:
            return error('unknown_file', 'Use a path from the supplied snapshot.')
        matches = []
        for path, text in sorted(self.files.items()):
            if 'path' in args and path != args['path']:
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if args['query'] not in line:
                    continue
                if len(matches) == MAX_MATCHES:
                    return {'ok': True, 'data': {
                        'matches': matches, 'matches_omitted': True}}
                matches.append({'path': path, 'line': number, 'text': line[:160],
                                'text_truncated': len(line) > 160})
        return {'ok': True, 'data': {'matches': matches, 'matches_omitted': False}}
