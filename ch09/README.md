# Chapter 9 companion — Checkpoints and resumption

From this directory, with Python 3.11 or newer:

```sh
python3 experiment.py
python3 -m unittest discover -v
```

Keep sibling Chapters 2, 4, 5, and 6 in place. Standard library only. The experiment creates temporary controller-owned stores, launches writer processes that deliberately exit, and starts fresh reader processes. Parent cleanup removes the temporary stores afterward. No live model, Docker, external publication, or real repository mutation.

## Contents

- `checkpoint.py`: bounded JSON, duplicate-key rejection, versioned schema, content-addressed objects, single-file checkpoint replacement, current-grant tool construction, verification/summary applicability.
- `experiment.py`: exits immediately before and after checkpoint replacement, read-only/revoked recovery cases, misleading handoff, reused Chapter 6 before-case verification failure, and artifact corruption.
- `sample-report.json`: actual four recovery rows, process exit codes, pending-file counts, fresh-reader results, handoff/corruption outcomes, and implementation/evidence fingerprints.
- Tests cover malformed and oversized records, schema/task identity, content hashes, missing objects, unsafe keys, stale evidence, authority fields, poisoning, actual process exits, and fresh-reader denials.

## Interpretation

Writer exit 70 means the test stopped before replacement; 71 means it stopped afterward. These are experiment-defined codes. A pending file is ignored by the ordinary reader. Both normal revision cases report verification not_run because they prepare an edit without checking it. The misleading-handoff case imports the actual saved Chapter 6 before-case failure and correctly marks it stale for the edited candidate.

The resume function's read and nonmutating write probe are teaching instrumentation. The write probe is denied under the current empty write grant; it is not an actual continuation edit. `next_step` names supported unfinished work but does not execute that work. No provider session or live model conversation is resumed.

## Storage limits

One writer, trusted local directory outside candidate control, small synthetic snapshots. File fsync plus same-directory replacement is tested against process exit, not power loss; directories are not fsynced. No concurrent-writer coordination, rollback protection, schema migration, garbage collection, remote storage, symlink-attack containment against a hostile storage owner, authentication, or complete audit persistence.

References are hashes, not arbitrary paths. A matching hash establishes identity relative to its reference, not authorship. The loader rejects invalid artifacts and does not infer completion from prose. Current authorization and disclosure still belong to the surrounding controller. Candidate-only verification matching assumes an authentic record for the applicable check configuration.

See [references](../REFERENCES.md) and [compatibility](../COMPATIBILITY.md).
