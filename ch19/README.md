# Chapter 19 Companion

Controlled state-unit upgrade, manifest identities, strict regression gate, declared reader-version admission, and stable cohort arithmetic. No deployment or provider calls.

## Run

Python 3.11 or newer; standard library only:

```sh
python3 experiment.py
python3 -m unittest discover -v
```

Nine actual local trials compare baseline, a seeded seconds-to-milliseconds migration defect, and its correction against independent expectations for 1/30/120 seconds. Baseline and corrected versions pass 3/3; bad upgrade passes 0/3. Original dictionaries stay unchanged. The report reproduces exactly with source/manifest fingerprints.

The gate requires an independent nonempty expected-task set and exact matching passing results for baseline and candidate. A regression verifies rejection when both result maps omit the same required task. Missing or unknown evidence blocks promotion. Twenty tests cover semantic duration, schema bounds, non-object reader input rejection, double migration, gate completeness, manifest identity, and cohort boundaries.

Reader-version admission only checks declared versions; it is not a whole-record compatibility proof. The old version1 reader is rejected for version2 state; the mixed reader is admitted. Cohort selection hashes tenant names into 100 buckets; small samples need not match the nominal percentage exactly.

## Scope

No service rollout, live canary, statistical model comparison, provider change, interrupted storage migration, mixed concurrent writers, snapshot restore, or external-effect rollback is performed. Manifests contain authored teaching identifiers; source hashes identify code, not an immutable remote model. The migration failure is deliberately seeded and measured locally, not a reported production incident.
