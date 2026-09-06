# Chapter 13 companion

A local tracing and artifact-diagnosis example. It reuses Chapter 6's snapshot digest and its Chapter 5, 4, and 2 import dependencies. Keep those folders alongside this chapter.

```sh
python3 -m unittest discover -v
python3 experiment.py
```

Python 3.11 or newer; standard library only. See [Compatibility](../COMPATIBILITY.md#chapter-13) for the interpreter actually exercised.

`tracing.py` records a root and selection, fixed authorization, export-attempt, verification, and final-claim spans. It writes real candidate JSON files under temporary directories. Four scripted cases distinguish a matching export after a pre-write failure, an exporter substitution, a wrong selection, and an injected write failure. Every case claims success; artifact evidence determines the outcome.

`sample-report.json` retains traces, observed digests, version labels, dependency fingerprints, and real `perf_counter_ns` readings. Timings vary. `experiment.without_timing` removes only start/end values for stable reproduction comparison. These durations are not provider latency or a performance benchmark.

`replay` inspects records without running tools or writing files. `investigate` takes separately supplied artifact bytes and compares their digest with recorded expected/selected identities. The report does not preserve the raw files after temporary-directory cleanup. Reproduction creates new files; replay does not recreate old ones.

The trace format is original teaching code, not OpenTelemetry wire format. Input validation catches selected structural defects in controller-owned exports; it is not a hardened remote parser, authenticity system, or crash-persistent collector. The fixed authorization span is a fixture assumption, not Chapter 11's approval service. Verification checks exact snapshot bytes, not behavior of generated code.

All source content is synthetic. A fake private marker appears in the local artifacts but is excluded from trace attributes. Digests and identifiers still require appropriate handling in real systems. No network, live model, candidate execution, remote telemetry, automated retention, or publication occurs.

Background references are centralized under [Tracing and telemetry](../REFERENCES.md#tracing-and-telemetry).

Diagnosis requires one instance of each non-export stage. Conflicting selection records are inconclusive rather than resolved by taking the first row. Repeated export attempts remain supported; replanning with several selections would require explicit causal links.
