"""Chapter 2: a bounded loop over a synthetic repository snapshot."""

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Callable, Protocol


# listing:actions:start
@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: dict


@dataclass(frozen=True)
class Final:
    text: str


@dataclass(frozen=True)
class Event:
    kind: str
    data: dict


@dataclass(frozen=True)
class RunResult:
    status: str
    answer: str | None
    events: tuple[Event, ...]


class Model(Protocol):
    def next(self, task: str, events: tuple[Event, ...]) -> ToolCall | Final:
        ...
# listing:actions:end


TOOL_SCHEMAS = [
    {
        "name": "search",
        "description": "Find a literal string in the supplied sample files. "
                       "Returns up to five matches with paths and line numbers.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "minLength": 1}},
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "read_file",
        "description": "Read the first 2000 characters of one sample file. "
                       "Use an exact path returned by search.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "minLength": 1}},
            "required": ["path"],
            "additionalProperties": False,
        },
    },
]


class SnapshotTools:
    """Only the supplied strings are accessible. This is not an OS sandbox."""

    def __init__(self, files: dict[str, str]):
        self.files = dict(files)

    # listing:dispatch:start
    def execute(self, call: ToolCall) -> dict:
        parameters = {"search": "query", "read_file": "path"}
        if call.name not in parameters:
            return {"ok": False, "error": "unknown_tool"}
        key = parameters[call.name]
        args = call.arguments
        if (not isinstance(args, dict) or set(args) != {key}
                or not isinstance(args[key], str)
                or not args[key].strip() or len(args[key]) > 4000):
            return {"ok": False, "error": "invalid_arguments"}
        if call.name == "search":
            return self._search(args[key])
        return self._read(args[key])
    # listing:dispatch:end

    def _search(self, query: str) -> dict:
        matches = []
        for path, text in sorted(self.files.items()):
            for line, content in enumerate(text.splitlines(), start=1):
                if query not in content:
                    continue
                if len(matches) == 5:
                    return {"ok": True, "data": {
                        "matches": matches, "truncated": True,
                    }}
                matches.append({
                    "path": path, "line": line, "text": content[:160],
                    "text_truncated": len(content) > 160,
                })
        return {"ok": True, "data": {"matches": matches, "truncated": False}}

    def _read(self, path: str) -> dict:
        if path not in self.files:
            return {"ok": False, "error": "unknown_file"}
        text = self.files[path]
        return {"ok": True, "data": {
            "path": path, "first_line": 1,
            "text": text[:2000], "truncated": len(text) > 2000,
        }}


def valid_action(action: object) -> bool:
    if isinstance(action, Final):
        return (isinstance(action.text, str) and bool(action.text.strip())
                and len(action.text) <= 4000)
    if isinstance(action, ToolCall):
        return (isinstance(action.call_id, str)
                and 0 < len(action.call_id) <= 100
                and isinstance(action.name, str)
                and 0 < len(action.name) <= 100
                and isinstance(action.arguments, dict))
    return False


# listing:loop:start
def run(
    model: Model,
    tools: SnapshotTools,
    task: str,
    max_steps: int = 6,
    cancelled: Callable[[], bool] = lambda: False,
) -> RunResult:
    if type(max_steps) is not int or not 1 <= max_steps <= 100:
        raise ValueError("max_steps must be an integer from 1 to 100")
    if not isinstance(task, str) or not task.strip() or len(task) > 4000:
        raise ValueError("task must contain 1 to 4000 characters")
    events = [Event("started", {"task": task, "max_steps": max_steps})]
    call_ids = set()

    def stop(status: str, answer: str | None = None) -> RunResult:
        events.append(Event("stopped", {"status": status}))
        return RunResult(status, answer, tuple(events))

    for step in range(1, max_steps + 1):
        if cancelled():
            return stop("cancelled")
        events.append(Event("model_call", {"step": step}))
        try:
            action = model.next(task, deepcopy(tuple(events)))
        except Exception as exc:
            events.append(Event("model_error", {"type": type(exc).__name__}))
            return stop("model_error")
        if cancelled():
            return stop("cancelled")
        if not valid_action(action):
            return stop("invalid_output")
        if isinstance(action, Final):
            events.append(Event("final", {"text": action.text}))
            return stop("completed", action.text)
        if action.call_id in call_ids:
            return stop("invalid_output")
        call_ids.add(action.call_id)
        events.append(Event("tool_call", deepcopy(asdict(action))))
        observation = tools.execute(action)
        events.append(Event("tool_result", {
            "call_id": action.call_id, "result": observation,
        }))
    return stop("step_limit")
# listing:loop:end
