# Chapter 10 companion — Retry intent and idempotency

From this directory, run with Python 3.11 or newer and its sqlite3 module:

```sh
python3 experiment.py
python3 -m unittest discover -v
```

Keep sibling Chapters 2, 4, 5, 6, and 9 available: the journal reuses Chapter 9's bounded JSON/file-replacement utility and its imports. No external request, model call, Docker, review notification, or behavioral verification. Temporary SQLite effects are local simulation records and are removed afterward.

## Files

- `retry.py`: transactional receiver, scoped operation identity and payload conflict, persisted client intent, one-attempt admission policy, and a bounded delay calculation.
- `experiment.py`: seven two-stage scenarios with reopened journals/connections, plus a naive new-key duplicate control. Reopening occurs in the same OS process.
- `sample-report.json`: actual local effects, decisions, attempt counts, Python/SQLite versions, and source fingerprints.
- Tests cover deduplication, actor scope, changed payloads, transaction rollback, lost acknowledgement, revoked grants, preconditions, budgets, and preserved uncertainty after a later rejection.

The safe lost-acknowledgement route creates one effect across two attempts. The naive route changes the key and creates two. The receiver commits its simulated effect and receipt in one database transaction. This does not make an effect in another external system atomic with SQLite.

## Boundaries

`remaining_seconds` is supplied admission information, not an interrupting timeout. The example does not sleep, schedule retries, measure elapsed service time, or randomize traffic; delay examples use a fixed jitter fraction. The controller must implement real deadline/transport/scheduler behavior.

Authorization, the verified-candidate hash, and the idempotency-contract flag are trusted controller inputs. The experiment uses synthetic verification hashes, not executed checks. Actor labels scope keys but are not authenticated identities. The journal uses one trusted local writer and inherits Chapter 9 storage limits; the receiver assumes trusted local calls and receipts. No network-response validation, durable multi-worker scheduling, receipt expiry, concurrent-load test, remote reconciliation endpoint, or compensation workflow is implemented.

See [references](../REFERENCES.md) and [compatibility](../COMPATIBILITY.md).
