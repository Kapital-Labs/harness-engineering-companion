# Chapter 15 Companion

Resource accounting with fixed acceptance checks, an immutable-snapshot read cache, hypothetical FIFO scheduling, and cooperative cancellation.

## Run

From this directory, using Python 3.11 or newer:

```sh
python3 experiment.py
python3 -m unittest discover -v
```

Keep Chapters 2, 3, and 14 alongside this directory. All imports and execution are offline and use the standard library. No provider configuration is needed.

## Evidence

`sample-report.json` retains 20 actual scripted runtime/grader trials: full 5/5, fixed 2/5, no-read 1/5, declared route 5/5. The meter counts decision invocations and bytes of its specified task/history JSON encoding; request totals include denied tool requests. Provider tokens are unavailable, not inferred from bytes.

Estimated units use invented weights: 100 per decision call, one per input byte, ten per tool request. They exclude output generation, machine costs, and human review; they are not dollars. Estimated totals are 25,414 full, 30,107 fixed, 11,737 no-read, and 25,179 declared route. Routing is authored from public task identifiers; no classifier or model selection is measured.

The cache performs actual reads of in-memory snapshot strings. Tests cover source/version/scope changes, revocation, search disclosure, removal, invalid requests, and mutation isolation. The cache is single-threaded, unbounded, assumes trusted scope/policy and storage, and claims no measured speedup. It does not cache effects or implement provider prompt caching.

Scheduling uses hypothetical fixed durations with simultaneous arrivals, FIFO dispatch, and no contention. Makespans at one/two/four workers are 1,300/1,100/1,000 ms; service work stays 1,300 ms. No threads, provider latency, or rate limits are measured. Cancellation runs the actual Chapter 2 loop: one decision completes after requesting cancellation, and its late tool action is never dispatched. It is cooperative, not an interrupt or refund.

## Reproduction and Limits

Source fingerprints and Python version are retained. Re-running on the recorded Python version reproduces the report exactly. Version differences must be inspected, not silently removed from provenance. The manuscript discusses live routing, price snapshots, atomic reservations, and cancellation propagation; those service mechanisms are not implemented here.

Shared source references and tested environments appear in `../REFERENCES.md` and `../COMPATIBILITY.md`. No public model ranking or generalization claim follows from these five public tasks.
