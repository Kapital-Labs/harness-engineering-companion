# Chapter 17 Companion

Actual MCP standard-I/O client/server exchange through a PydanticAI agent with deterministic FunctionModel decisions. No model provider or remote tool service is called.

## Install and Run

Tested with Python 3.12.14 on macOS. Use Python 3.12 for the recorded checkpoint. Keep this chapter's dependencies separate from the standard-library examples:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python integration.py
.venv/bin/python -m unittest discover -v
```

Installation downloads packages. The experiment uses a local subprocess and does not require credentials. The lock pins the resolved package versions, including mcp 2.1.1 and pydantic-ai-slim 2.40.0; it does not contain package artifact hashes. The local .venv is a disposable environment, not companion source to publish.

The MCP SDK version uses `MCPServer` and snake_case Python result attributes. These are package APIs; the protocol's wire names and versioning are separate. The verified selected protocol version is 2025-11-25.

## Expected Evidence

`sample-report.json` records accepted answer `maintainer_only`, tool inventory `read_snapshot`, true missing-file and missing-argument error flags, local denial, interpreter/package versions, and source/lock fingerprints. Regeneration on the recorded environment matches exactly. Negative probes intentionally produce SDK error diagnostics on stderr; JSON report output remains on stdout.

The server exposes a fixed in-memory policy string. The runtime's bridge checks current local read allowance, calls the MCP tool with a timeout, and validates structured result shape/path/text size. Successful scripted execution takes a tool-request decision and a final-answer decision. PermissionError and result-validation ValueError propagate to the caller; the bridge implements no model-facing repair or retry for them.

Ten tests include actual SDK/runtime/subprocess execution and focused result validation, byte bounds, permission-before-transport, and validation-failure propagation. Unit-test fake result objects exercise application gates, not malformed wire decoding.

## Scope

Trusted local server and in-process run grant; no OAuth, authenticated HTTP endpoint, hostile-process isolation, provider calls, general code understanding, arbitrary catalog import, or remote effect. Post-parse text validation does not bound transport buffering. The runtime request limit and per-call timeout are not an end-to-end hard deadline.

Shared references distinguish specifications consulted from integrations tested. Chapter 17 was exercised on Python 3.12.14; no other interpreter/platform is claimed for its locked integration.
