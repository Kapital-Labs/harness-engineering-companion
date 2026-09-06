"""Trusted per-run authorization over synthetic snapshots; not process isolation."""
from dataclasses import dataclass
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ch04'))
from tools import WindowTools, ToolCall, Final, run


def canonical(path):
    return (isinstance(path, str) and 0 < len(path) <= 4000
            and '\\' not in path and '\x00' not in path
            and all(part not in {'', '.', '..'} for part in path.split('/')))


@dataclass(frozen=True)
class Grant:
    paths: frozenset[str]
    def __post_init__(self):
        paths = frozenset(self.paths)
        if not all(canonical(p) for p in paths):
            raise ValueError('Grant paths must be canonical relative snapshot keys')
        object.__setattr__(self, 'paths', paths)


# listing:authorize:start
class AuthorizedTools:
    def __init__(self, files: dict[str, str], grant: Grant):
        self.grant = grant
        visible = {p: text for p, text in files.items() if p in grant.paths}
        self.tools = WindowTools(visible)

    def execute(self, call: ToolCall) -> dict:
        denied = {'ok': False, 'error': 'permission_denied'}
        if call.name not in {'read_file', 'search'}:
            return denied
        args = call.arguments
        if not isinstance(args, dict):
            return denied
        if call.name == 'read_file' or 'path' in args:
            path = args.get('path')
            if not canonical(path) or path not in self.grant.paths:
                return denied
        return self.tools.execute(call)
# listing:authorize:end
