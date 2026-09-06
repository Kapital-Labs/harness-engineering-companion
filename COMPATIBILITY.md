# Compatibility notes

This file records implementation configuration and actual verification separately from documentation access dates in [References](REFERENCES.md).

## Current Edition Verification

The first-edition companion passed 403 tests on September 5, 2026. Standard-library checkpoints used Python 3.14.6 on macOS; Chapter 17 used Python 3.12.14 with its pinned dependencies. All 42 book listings were checked against companion source, and retained reports reproduced apart from documented variable timing fields. No live-provider compatibility is claimed. A clean package also passed all 403 tests after a fresh installation of Chapter 17’s locked dependencies using Python 3.12.14. The per-chapter counts below describe the current release.

## Chapter 2

- Runtime used for the recorded offline checks: Python 3.14.6, September 5, 2026.
- Declared minimum: Python 3.11. Source passed a Python 3.11 grammar check; the minimum-version runtime has not been tested.
- Dependencies: Python standard library only.
- API version header in the optional adapter: `anthropic-version: 2023-06-01`. This is a version identifier, not a documentation access date.
- Offline verification: 23 tests passed, including loop behavior, tool dispatch, and synthetic provider request/response checks.
- Live provider verification: not performed. No model ID or account configuration has been verified.

Record future compatibility checks with their actual date, runtime and dependency versions, model ID where relevant, commands, and outcomes. A documentation review alone must not advance a live-verification date.

## Chapter 3

- Runtime used for offline checks: Python 3.14.6, September 5, 2026.
- Dependencies: Python standard library and the sibling Chapter 2 checkpoint. Keep both chapter folders together.
- Verification: 24 tests passed, including grader edge cases, malformed denied requests, repeated trials, CLI reports, and exit codes.
- Captured offline results: fixed workflow 2 of 5; task-specific scripted fixtures 5 of 5. These are deterministic controls, not model performance.
- Live provider verification: not performed. The Chapter 2 adapter is reused; requested model IDs are user-supplied and usage/cost remain unknown in live reports.
- The source parses with Python 3.11 grammar selection; no minimum-version runtime check has been performed.

## Chapter 4

- Runtime used: Python 3.14.6, September 5, 2026. Standard library plus the sibling Chapter 2 checkpoint.
- Verification: 19 offline tests passed for window bounds, omission semantics, provenance checks, and the complete 21-row comparison.
- Captured sufficient-inspection counts: dump 7/7, prefix 5/7, window 6/7. These are scripted retrieval controls, not answer accuracy or model capability.
- No live mode or provider verification in this checkpoint. Byte counts exclude prompts, schemas, requests, and repeated provider history.
- Source parses with Python 3.11 grammar selection; the Python 3.11 runtime has not been tested.

Additional Chapter 4 check: all 19 tests also passed on the bundled Python 3.12.14 runtime. Comparison results matched the recorded Python 3.14.6 report except for the runtime field.

## Chapter 5

- Controller runtime: Python 3.14.6, September 5, 2026. Standard library, sibling Chapters 2 and 4.
- 18 offline tests passed.
- Recorded authorization trace: two permitted reads, two permission denials, completed status, no synthetic private canary in trace. No model calls.
- Actual isolation smoke probe: Docker Engine 28.3.2 on local Docker Desktop, worker Python 3.12.3. Existing image mcr.microsoft.com/playwright:v1.62.1-noble, local ID sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e. No image pulled.
- Final selected probe checks passed; first interface-name assumption failed and is preserved separately. The final probe checks up-interface flags and IPv4 routes as well as one failed connection.
- No IPv6, container-escape, resource-exhaustion, or noexec-bypass assessment performed. Image choice is a local test convenience, not a minimal production-image recommendation.
- Python 3.11 grammar parsing passes; minimum-version runtime not exercised.

## Chapter 6

- Controller: Python 3.14.6 on macOS, September 5, 2026. Standard library with sibling Chapters 2, 4, and 5.
- 22 chapter tests pass, including stale/ambiguous edits, Unicode rejection before mutation, missing-final-newline diffs, strict result parsing, Docker launch-error classification, bounded output, and timeout.
- Actual Docker Engine 28.3.2 verification: before failed; intended candidate passed; overbroad candidate failed; syntax error failed. Five fixed checks pass for the intended candidate. All four worker containers confirmed absent afterward.
- Worker Python 3.12.3, same existing local image ID as Chapter 5. No model calls, image downloads, or publication actions. Source and worker hashes are in verification-report.json.
- Python 3.11 grammar passes; minimum-version runtime not exercised. The selector-based controller is tested on macOS/POSIX, not Windows.
- Tests execute alongside candidate Python in one process; this is not hostile-code attestation. CPU/memory/PID configuration is inherited, not stress-tested here. Controller death and durable recovery remain outside this checkpoint.

## Chapter 7

- Python 3.14.6/macOS, September 5, 2026. Standard library and sibling Chapters 2–6; 20 chapter tests pass.
- 24 deterministic retrieval/context rows reproduced exactly. Source fingerprints and the imported Chapter 6 verification-report fingerprint are recorded in sample-report.json.
- Actual saved Chapter 6 pass is current for the reproduced candidate and stale after a later source revision. No Docker rerun or model call in Chapter 7.
- Python 3.11 grammar checked; Python 3.11 runtime not exercised. Byte budgets are compact JSON UTF-8 measurements, not tokens or provider compatibility tests.
- Known limits: tailored retrieval plans, fixed answers, path-level readiness weaker than sufficient evidence, absence grading not exhaustive, no external-record parser or automated sensitive-data classification, candidate-only verification applicability.

## Chapter 8

- Python 3.14.6/macOS, September 5, 2026; standard library, no sibling imports needed for navigation/preflight/tests.
- 22 chapter tests pass. Fourteen fixed navigation rows and the preflight output are saved; no live model, Docker run, setup installation, or publication action.
- Source map handles top-level Python functions/async functions/classes. Parsing errors remain visible; resource-exhaustion handling for arbitrary source is outside scope.
- Minimum Python 3.11 grammar checked separately; Python 3.11 runtime not exercised. No provider integration.
- Registry only describes the Chapter 6 verification entry point. It does not adapt that checker to the moved-source fixture or report behavioral verification.

## Chapter 9

- Python 3.14.6/macOS, September 5, 2026. Standard library plus sibling Chapters 2, 4, 5, and 6.
- 24 chapter tests pass, including actual writer-process exits, fresh-reader recovery, current grants, stale summaries/verification, rejected commits, and corruption.
- Four process-recovery rows: before replacement restores revision 1 with one pending file; after replacement restores revision 2 with none. Read-only/revoked grants remain current; write probe denied in all cases.
- Misleading handoff and the actual saved Chapter 6 before-case failure remain stale for the edited candidate. No verification rerun or model call. Artifact corruption produces invalid_checkpoint/exit 2.
- Python 3.11 grammar checked; minimum-version runtime not exercised. Process-exit results do not establish power-loss durability, concurrency, rollback protection, remote consistency, or authentication.

## Chapter 10

- Python 3.14.6/macOS and SQLite 3.53.4, September 5, 2026. Standard library sqlite3; journal imports Chapter 9 utilities and their sibling dependencies.
- 27 chapter tests pass.
- Seven local retry scenarios plus a naive duplicate control. Same-key lost acknowledgement: one effect/two attempts; changed-key control: two effects. All states and stop reasons retained in sample-report.json.
- Reopened storage in the same OS process. No external review request, network fault experiment, model call, Docker, or behavioral verification. Verified-candidate hashes are synthetic precondition fixtures.
- Python 3.11 grammar checked; minimum-version runtime not exercised. Deadline checks are admission only; no scheduler or sleeping. No concurrent-load, receipt-expiry, power-loss, or remote reconciliation test.

## Chapter 11

- Python 3.14.6/macOS, September 5, 2026. Standard library plus sibling Chapters 5, 4, and 2.
- 20 chapter tests pass. Eight scripted delivery cases reproduced exactly with source fingerprints.
- Private model-facing read denied. Six delivery cases have zero effects; an exact approved summary and an intentionally mistaken approval each have one local outbox effect. The latter contains the fake private marker and demonstrates that approval binding is not content classification.
- Python 3.11 grammar checked; Python 3.11 runtime not exercised. No model/provider integration, real secret, network message, Docker run, UI authentication, firewall, persistence, or concurrency experiment.
- Controller owns policy, clock, run context, and approval issuance. Mutable policy collections are copied to immutable sets; approval actions are serialized copies. These conventions do not isolate hostile Python in the same process.

## Chapter 12

- Python 3.14.6/macOS, September 5, 2026; standard library and inherited Chapters 11, 5, 4, and 2.
- 25 chapter tests pass. Ten-case report and local incident reproduce exactly with implementation/dependency fingerprints.
- Nine forbidden cases: eight blocked, one deliberately approved disclosure correctly detected despite scripted refusal annotation. One exact approved-summary positive control succeeds.
- Containment preserves one prior effect while denying pending send and read. Fresh reduced recovery returns exact expected review content/provenance and blocks raw, encoded, and benign sends; zero new recovery effects.
- Four review regressions cover denied reads leaking text/errors, sanitized exports, and recovery success with missing/wrong contents. Literal fixture detection is not a general secret classifier.
- Python 3.11 grammar checked; minimum-version runtime not exercised. No model, external message, real secret, network control, concurrent cancellation, credential revocation, or durable forensic store tested. Events/outbox are local memory; captured JSON preserves sanitized outcomes.

## Chapter 13

- Python 3.14.6/macOS, September 5, 2026. Standard library plus Chapter 6 snapshot identity and inherited Chapters 5, 4, and 2.
- 21 chapter tests pass. Four actual temporary-file cases: correct export after injected pre-write failure, wrong exporter content, wrong selection, and injected write failure.
- Stable report fields reproduce exactly; only start/end counter readings are excluded from comparison. Captured report retains real perf_counter_ns values. These are not model/provider latency measurements.
- Passive replay leaves artifact bytes unchanged. Diagnosis hashes separately supplied bytes. Test coverage includes missing/open records, duplicate/orphan spans, bad durations, attribute restrictions, and unavailable artifacts.
- Python 3.11 grammar passes; minimum runtime not exercised. No model, network telemetry, OTel SDK, candidate execution, concurrency, durable collector, remote authentication, or retention automation. Temporary artifacts expire after experiment; trace retains digests/outcomes.

## Chapter 14

- Python 3.14.6/macOS, September 5, 2026. Standard library plus Chapters 3 and 2; actual runtime/grader execution.
- 26 chapter tests pass. 45 offline trials: fixed baseline 6/15, full script 15/15, no-read ablation 3/15. Three task wins/two ties for full versus baseline. Report reproduces exactly with source and rubric fingerprints.
- Five public tasks with illustrative split bookkeeping only; three deterministic repeats. No unseen holdout, provider call, model ranking, or human-review study. Actual comparison interval null.
- Seven authored calibration cases: four agreements/six resolved, one false acceptance, one false rejection, one unknown. Separately hypothetical 20/25 Wilson arithmetic checked, including boundaries. Paired unknown-task retention has a regression test.
- Python 3.11 grammar passes; minimum runtime not exercised. Grader limitations, missing-task abstention, output-parser semantic limits, environment controls, and live statistical design are documented.

## Chapter 15

- Python 3.14.6/macOS, September 5, 2026. Standard library with Chapters 14, 3, and 2 retained alongside. All execution is offline.
- 22 chapter tests pass. Saved report reproduces exactly, including dependency fingerprints and Python version. Python 3.11 grammar checked; minimum-version interpreter not exercised.
- 20 actual deterministic trials: full 5/5, fixed 2/5, no-read 1/5, declared route 5/5. Actual decision/request counts and a specified JSON/UTF-8 representation are measured; provider tokens are null. Invented resource weights imply no actual currency or comprehensive compute cost.
- Scoped cache tests cover current access before lookup, changed/removed source, scope/tool-version separation, copied results, dispatcher validation, and search disclosure. In-memory, trusted, single-threaded, unbounded; no speedup measured.
- Hypothetical FIFO schedules use fixed durations and no contention. Actual cooperative cancellation returns cancelled with one decision call and zero tool requests. No live model router, provider usage adapter, pricing integration, concurrent reservation ledger, remote cancellation, or production latency benchmark tested.

## Chapter 16

- Python 3.14.6/macOS, September 5, 2026; self-contained standard-library example. 24 chapter tests pass. Python 3.11 grammar checked; minimum-version runtime not exercised.
- Exact report reproduction with source fingerprints. Fifteen authored coordination trials use real in-memory transformations and bounded ThreadPoolExecutor execution. Single/parallel/reviewed accept 1/5 seeded cases each; proposal calls 6/11/11; known work units 11/11/13.
- Integration tests cover stale and changed bases, missing/duplicate/unknown workers, ownership expansion, incomplete scope, conflicting paths, invalid schema and extra instructions, duplicate contracts, copied output isolation, and exact final acceptance. Weak review deliberately approves shared wrong values.
- Concurrent known-unit admission test permits one of two two-unit requests against a three-unit balance. Failed admission preserves the balance. No refunds, usage estimates, distributed settlement, or persistence.
- No live models, provider cost/timing, generated-code execution, OS isolation, worktree merge, authenticated peer transport, remote cancellation, hard deadlines, or durable worker recovery. Chapter 16 discusses these boundaries without claiming to implement them.

## Chapter 17

- Python 3.12.14/macOS; MCP 2.1.1, pydantic-ai-slim 2.40.0, locked dependencies; negotiated protocol 2025-11-25; verified September 5, 2026. 10 passing tests.
- Actual MCP standard-I/O subprocess and PydanticAI FunctionModel runtime execution with deterministic decisions. Authorized fixed-policy read produces expected answer; missing file/argument error flags and local denial retained. Source, lock, interpreter, package, and protocol identity captured.
- Exact saved-report reproduction with source fingerprints; Python 3.11 source grammar checked. Minimum-version runtime not exercised. Chapter 17 uses its own locked Python 3.12.14 environment.
- No live model, OAuth/HTTP authentication, hostile-process isolation, general source interpretation, transport-buffer limit, arbitrary catalog integration, remote effect, or hard end-to-end deadline. Local output gate runs after SDK parsing. Dependency installation uses network; demonstration uses local communication. Lock pins versions but not package artifact hashes.

## Chapter 18

- Python 3.14.6/macOS; SQLite via standard library; verified September 5, 2026. 23 passing tests.
- Actual SQLite admission/lease/review lifecycle and real child exit23 after durable claim. Fresh connection reclaims generation2; stale generation submission rejected. One local artifact receipt after duplicate approval; cancellation rejects late submission. Logical clock is controlled, not wall-time waiting.
- Exact saved-report reproduction with source fingerprints; Python 3.11 source grammar checked. Minimum-version runtime not exercised. Chapter 17 uses its own locked Python 3.12.14 environment.
- Trusted tenant/reviewer/clock inputs; no authentication, fair dispatcher, renewals, full attempt journal, power-loss simulation, distributed fencing, external delivery, retention service, or production availability guarantee. State/effect atomicity holds because both records share one local SQLite transaction.

## Chapter 19

- Python 3.14.6/macOS; standard library; verified September 5, 2026. 20 passing tests.
- Nine actual state-budget computations over1/30/120seconds. Baseline/corrected migrations pass3/3; seeded bad migration passes0/3. Manifest identities, independently declared task-set gate, version-coverage rollback predicate, and deterministic tenant cohort arithmetic.
- Exact saved-report reproduction with source fingerprints; Python 3.11 source grammar checked. Minimum-version runtime not exercised. Chapter 17 uses its own locked Python 3.12.14 environment.
- No deployment, live canary, model comparison, interrupted durable migration, concurrent writers, fleet rollback, or external-effect reversal. Version coverage is a declared compatibility predicate, not full semantic proof. Cohort percentage is not an exact small-population allocation.

## Chapter 20

- Python 3.14.6/macOS; standard library plus Chapter18 service; verified September 5, 2026. 13 passing tests.
- Original structured research comparison preserves two conflicting values and provenance; absent question yields insufficient evidence. Support proposal produces one local SQLite review receipt after approval and zero real refunds. Three-row quality scan records two findings on one row, no mutation/deletion.
- Exact saved-report reproduction with source fingerprints; Python 3.11 source grammar checked. Minimum-version runtime not exercised. Chapter 17 uses its own locked Python 3.12.14 environment.
- No live research, semantic extraction, credibility scoring, real customer policy/payment, authentication, production remediation, or domain performance estimates. Inputs are trusted structured fixtures. Quality row positions are snapshot-local; findings do not determine justified repairs.
