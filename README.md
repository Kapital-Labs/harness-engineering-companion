# Harness Engineering Companion

Runnable checkpoints for *Harness Engineering: Building, Evaluating, and Operating Reliable AI Agents*.

Start with Chapter 2's small execution loop. Later folders either reuse an earlier component or isolate a new engineering mechanism. Keep the complete companion directory together: sibling imports and saved evidence are part of the examples. Chapter 1 introduces the source strings used in `ch02`; it has no separate executable folder.

## Download

Get the [first-edition release](https://github.com/Kapital-Labs/harness-engineering-companion/releases/tag/first-edition-v1.0.1) and download `harness-engineering-first-edition-v1.0.1.zip`. Extract the ZIP and open its top-level directory before following the commands below. You do not need Git to use the examples.

If you prefer Git:

```sh
git clone https://github.com/Kapital-Labs/harness-engineering-companion.git
cd harness-engineering-companion
git checkout first-edition-v1.0.1
```

The release preserves the examples for the first edition. The default branch may contain later corrections; use a numbered release for reproducibility.

## First Run

From this companion directory:

```sh
cd ch02
python3 demo.py
python3 -m unittest discover -v
```

The default demo uses synthetic source and scripted decisions. It makes no provider request and requires no credentials. Its trace shows the real loop dispatching a search and source read, then returning an answer. Compare the result with `expected-scripted-run.json`.

A completed run is an execution result. Chapter 3 adds an independent answer grader. Some later experiments deliberately include failed tasks, rejected actions, or incorrect candidates; a successful experiment may require observing those failures.

## Runtime Choices

Most checkpoints use the Python standard library and declare Python 3.11 or newer. See [compatibility notes](COMPATIBILITY.md) for the exact interpreters and platforms exercised; a declared minimum is not a claim of testing every supported version.

Chapter 17 uses a separate Python 3.12 environment and pinned third-party dependencies. Follow [its installation instructions](ch17/README.md) before running that checkpoint or the full suite. Package installation downloads dependencies. The subsequent protocol experiment uses a local subprocess and scripted runtime decisions.

Chapters 5 and 6 have separate operator-invoked Docker experiments. Their default demos and unit tests do not require starting containers. Read their instructions for a trusted local image and the scope of the saved isolation/verification evidence.

Only the optional live modes in Chapters 2 and 3 call a model provider. Their instructions identify the required model argument, credentials, transmitted synthetic data, and charges. Start with the default offline modes.

## Chapter Map

Run the command in the named chapter directory. Each linked README explains the complete procedure and expected evidence.

| Chapter | Main Command | Engineering Question |
|---|---|---|
| [2: Execution loop](ch02/README.md) | `python3 demo.py` | How does a proposed action become an observation or a terminal result? |
| [3: First evaluator](ch03/README.md) | `python3 evaluate.py` | Does the completed answer satisfy its evidence contract? |
| [4: Tool interfaces](ch04/README.md) | `python3 compare.py` | Can the caller reach the required source within the interface's bounds? |
| [5: Permissions](ch05/README.md) | `python3 demo.py` | Which snapshot requests does the current grant permit? |
| [6: Controlled edits](ch06/README.md) | `python3 demo.py` | Which candidate was prepared, and what verification applies? |
| [7: Context composition](ch07/README.md) | `python3 experiment.py` | Which current, disclosable evidence fits the next decision? |
| [8: Navigation](ch08/README.md) | `python3 experiment.py` | Does maintained guidance still locate the relevant definition? |
| [9: Checkpoints](ch09/README.md) | `python3 experiment.py` | Which task state survives interruption, under current authority? |
| [10: Retry and reconciliation](ch10/README.md) | `python3 experiment.py` | What is known about the effect after a response is lost? |
| [11: Security boundaries](ch11/README.md) | `python3 experiment.py` | Which proposals reach a local outbound effect? |
| [12: Defense testing](ch12/README.md) | `python3 experiment.py` | Did the protected property hold, and what does containment restore? |
| [13: Tracing](ch13/README.md) | `python3 experiment.py` | Where did the selected and observed artifacts diverge? |
| [14: Comparative evaluation](ch14/README.md) | `python3 experiment.py` | Are trials complete, comparisons paired, and judgments checked? |
| [15: Resources](ch15/README.md) | `python3 experiment.py` | What work was consumed per accepted outcome? |
| [16: Coordination](ch16/README.md) | `python3 experiment.py` | Does delegation or review improve the combined candidate? |
| [17: Protocol integration](ch17/README.md) | `.venv/bin/python integration.py` | Where do runtime, transport, and application responsibilities meet? |
| [18: Durable jobs](ch18/README.md) | `python3 experiment.py` | Which worker may submit, and which candidate was approved? |
| [19: Release changes](ch19/README.md) | `python3 experiment.py` | Does migrated state preserve its intended meaning? |
| [20: Domain comparisons](ch20/README.md) | `python3 experiment.py` | How do evidence and effect contracts change by domain? |

The early checkpoints develop the coding-agent interfaces. The later examples retain those engineering concerns while simplifying inputs to expose a particular failure. For example, Chapter 16 coordinates timeout proposals, Chapter 17 connects a fixed policy tool, and Chapter 18 submits authored candidates to a durable queue. Chapter 18 does not invoke Chapter 17's agent automatically. The manuscript identifies where an application would connect those components.

## Tests and Saved Reports

Within a standard-library chapter, run:

```sh
python3 -m unittest discover -v
```

After installing Chapter 17's environment, run the complete suite from this companion directory:

```sh
python3 verify.py
```

The verifier uses a separate process for each chapter so imports from one checkpoint cannot silently replace another chapter's implementation. It stops when a suite fails. Chapter 17's expected negative probes may write SDK diagnostics to standard error; use the test summary to distinguish a successful rejection test from a suite failure.

Check the relevant README before comparing reports. Some outputs reproduce exactly in the recorded environment. Others retain elapsed times or timestamps that change on each execution. Compare stable fields only where the chapter defines that comparison. Do not remove mismatched source fingerprints to manufacture agreement: they identify the implementation that produced the result.

Saved Docker reports record the earlier executed probes. An offline test run does not refresh that evidence. Likewise, scripted decisions exercise software behavior without measuring a language model's capability.

## References and Editions

[REFERENCES.md](REFERENCES.md) contains shared documentation links and access dates. [COMPATIBILITY.md](COMPATIBILITY.md) records implementation versions, test environments, and evidence limits. A documentation date and an executed compatibility check answer different questions.

Use the release matching your book edition when reproducing printed examples. Consult compatibility notes before using changed examples from a later release. The chapter folders, source files, tests, and retained reports belong together; local virtual environments and caches are disposable runtime artifacts.

## License

The companion code and accompanying repository documentation are available under the [MIT license](LICENSE). The textbook manuscript and cover artwork are separate works and are not included in this repository or its license.
