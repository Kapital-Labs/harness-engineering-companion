"""Actual MCP stdio and PydanticAI execution with deterministic decisions."""
import asyncio
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.usage import UsageLimits


# listing:gate:start
def validate_result(result, path):
    if result.is_error:
        raise ValueError('remote_tool_error')
    data = result.structured_content
    if (type(data) is not dict or set(data) != {'path', 'text'}
            or data['path'] != path or type(data['text']) is not str
            or len(data['text'].encode('utf-8')) > 4096):
        raise ValueError('invalid_remote_result')
    return data
# listing:gate:end


def scripted(messages, info):
    returns = [part for message in messages for part in message.parts
               if isinstance(part, ToolReturnPart)]
    if not returns:
        return ModelResponse(parts=[ToolCallPart('read_policy', {})])
    data = returns[-1].content
    # Known fixture interpretation, not a general source-code analyzer.
    answer = ('maintainer_only' if 'role == "maintainer"' in data['text']
              else 'unsupported')
    return ModelResponse(parts=[TextPart(answer)])


# listing:bridge:start
async def run_agent(session, allowed):
    agent = Agent(FunctionModel(scripted))

    @agent.tool_plain
    async def read_policy() -> dict:
        """Read policy.py from the authorized sample server."""
        if 'policy.py' not in allowed:
            raise PermissionError('read_not_granted')
        result = await session.call_tool(
            'read_snapshot', {'path': 'policy.py'}, read_timeout_seconds=5
        )
        return validate_result(result, 'policy.py')

    result = await agent.run('Who can close an issue?',
                             usage_limits=UsageLimits(request_limit=3))
    return result.output
# listing:bridge:end


async def experiment():
    root = Path(__file__).resolve().parent
    params = StdioServerParameters(command=sys.executable,
                                   args=[str(root/'server.py')], env={})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=5) as session:
            initialized = await session.initialize()
            if initialized.protocol_version != '2025-11-25':
                raise ValueError('unreviewed_protocol_version')
            listed = await session.list_tools()
            names = sorted(t.name for t in listed.tools)
            if names != ['read_snapshot'] or listed.next_cursor is not None:
                raise ValueError('unexpected_tool_inventory')
            if initialized.capabilities.tools is None:
                raise ValueError('missing_tools_capability')
            good = await run_agent(session, {'policy.py'})
            missing = await session.call_tool('read_snapshot', {'path': 'missing'})
            malformed = await session.call_tool('read_snapshot', {})
            denied = False
            try:
                await run_agent(session, set())
            except PermissionError:
                denied = True
            return {'answer': good, 'accepted': good == 'maintainer_only',
                    'protocol_version': initialized.protocol_version,
                    'server': initialized.server_info.name, 'tools': names,
                    'missing_file_is_error': missing.is_error,
                    'missing_argument_is_error': malformed.is_error,
                    'local_denial': denied, 'python': platform.python_version(),
                    'packages': {p: importlib.metadata.version(p)
                                 for p in ('mcp', 'pydantic-ai-slim')},
                    'source_sha256': {p: hashlib.sha256((root/p).read_bytes())
                                      .hexdigest() for p in
                                      ('server.py','integration.py',
                                       'requirements.lock')}}


if __name__ == '__main__':
    print(json.dumps(asyncio.run(experiment()), indent=2, sort_keys=True))
