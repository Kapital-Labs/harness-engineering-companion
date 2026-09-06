"""Trusted local MCP subprocess; exposes a fixed in-memory file only."""
from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

server = MCPServer('book-snapshot', version='1')
FILES = {'policy.py': 'def can_close(role):\n    return role == "maintainer"\n'}


class Snapshot(BaseModel):
    path: str
    text: str


@server.tool()
def read_snapshot(path: str) -> Snapshot:
    """Read one named file from the book's fixed sample snapshot."""
    if path not in FILES:
        raise ValueError('unknown_file')
    return Snapshot(path=path, text=FILES[path])


if __name__ == '__main__':
    server.run(transport='stdio')
