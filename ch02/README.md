# Chapter 2 companion

Use Python 3.11 or newer. There are no third-party dependencies to install. The sample works with synthetic source strings in demo.py; it does not search your computer or execute repository code.

From this directory:

```sh
python3 demo.py
python3 -m unittest discover -v
```

The default is a **scripted fixture**, not a language model. It exercises the real loop, tool dispatcher, and event log without network access or credentials. Its output should match expected-scripted-run.json. The result names the mode so that the fixture cannot be mistaken for a live experiment.

To exercise the step budget:

```sh
python3 demo.py --max-steps 1
```

That command returns a step_limit result and exit code 1. Normal completion returns 0; invalid CLI configuration returns 2. A completed answer can still be wrong. Chapter 3 introduces independent outcome checks.

## Optional live model

Live mode makes billable requests to Anthropic and sends the synthetic task and tool observations. Configure ANTHROPIC_API_KEY in your environment using your normal credential-management method. Then supply an exact Messages API model ID available to your account:

```sh
python3 demo.py --live --model YOUR_AVAILABLE_MODEL_ID
```

YOUR_AVAILABLE_MODEL_ID is a command argument you must replace, not a published or tested model identifier. No live model identifier is pinned or verified by these offline examples. Record the exact model and run date when using live mode.

The adapter uses the documented native tool-use protocol. It supports one client tool call per turn and text final answers. It rejects unsupported blocks and incomplete output rather than silently treating a partial reply as a completed answer. Extended thinking, server tools, streaming, and parallel tool calls are outside this chapter's adapter contract.

**Verification boundary:** Offline tests cover request construction and response handling with synthetic provider fixtures. No live provider call has been made for this release. These tests do not establish account compatibility or real-model task performance.

## What this small harness does and does not enforce

- Only search and read_file are dispatchable; paths are keys in a supplied dictionary. There is no host-filesystem fallback.
- Tool output and the number of model turns are bounded. A step limit is not a total wall-clock or monetary budget. The HTTP adapter uses a 30-second socket timeout, which is not a whole-run deadline.
- Cancellation is cooperative, checked before and after each model call. It does not interrupt a blocking call already in progress.
- The in-process tools and model adapter are trusted application code. A copied history prevents accidental mutation of prior events; it is not process isolation.
- The local JSON trace contains the synthetic task, arguments, observations, and final answer. It omits private model reasoning and provider prose accompanying tool calls. It is a normalized trace, not an exact API transcript.
- The sample does not automatically redact arbitrary task or file content. Keep the synthetic dataset for this chapter; data minimization, trace redaction, and retention get fuller treatment later.
- Model-adapter exceptions become model_error with an exception class name. Tool implementation defects propagate to the developer instead of being disguised as ordinary “file not found” observations.

See the manuscript for the walk-through and exercises. Files marked test_ contain offline tests and do not require an API key.

## Reference documentation

See the shared references for [Messages API](../REFERENCES.md#messages-api), [tool-call handling](../REFERENCES.md#handling-tool-calls), and [single versus parallel calls](../REFERENCES.md#single-and-parallel-tool-calls). Documentation access dates live there; implementation versions and test dates live in [Compatibility notes](../COMPATIBILITY.md#chapter-2).
