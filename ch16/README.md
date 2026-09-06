# Chapter 16 Companion

Compare a single scripted worker, two bounded threaded workers, and two workers followed by a deliberately incomplete consistency reviewer. All use the same integration and acceptance checks.

## Run

From this directory, with Python 3.11 or newer:

```sh
python3 experiment.py
python3 -m unittest discover -v
```

Standard library only; no provider, package installation, account, or external side effect. This chapter is self-contained. Earlier chapters provide the design context rather than imported implementation.

## Cases and Evidence

The target is two in-memory JSON-shaped files whose timeout values must both become 30. Five authored cases cover correct proposals, a shared wrong target of 20, overlapping ownership, a stale reply, and a missing reply. The conflict case adds a scripted overlapping proposal to every topology; it is a malformed-handoff control, not naturally occurring agent behavior. Missing replies are removed after work has consumed its units.

`sample-report.json` records 15 trials, dependency fingerprints, and Python version. All topologies accept only the correct case (1/5 each); this is a seeded test-case count, not user-task success probability. Single/parallel/reviewed proposal calls total 6/11/11; fixture work units total 11/11/13. The reviewed wrong-target case records review approval but failed final acceptance.

The parallel modes use a real two-thread pool. No latency measurement or model-performance claim follows. Workers modify copied snapshots; this is data ownership under trusted functions, not OS isolation. The coordinator validates exact reply schema, assignment identity, base digest, owned-path coverage, bounded integer artifact schema, duplicate/missing replies, and conflicts before returning a new candidate. Identity fields assume trusted in-process transport; hashes do not authenticate workers or prove source inspection.

The budget is a process-local lock-protected counter for known work units, with no refunds. A concurrent test confirms one of two two-unit admissions is rejected against three units. It is not a distributed reservation/settlement system. Executor worker crashes and blocked-call cancellation are discussed but not implemented as service recovery.

## Verification Limits

The independent acceptance oracle compares the candidate with the exact two-file requirement. The deliberately weak reviewer only checks equality of values, so it approves a shared wrong value. No live reviewer calibration, statistical independence, general coding quality, generated-code execution, real checkout merging, tenant authentication, network permissions, or durable worker lifecycle is measured.

Source-matched listings, exercise arithmetic, and report reproduction are recorded in the book's Chapter 16 verification notes. Shared source references and tested versions live in `../REFERENCES.md` and `../COMPATIBILITY.md`.
