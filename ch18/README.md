# Chapter 18 Companion

Durable SQLite job admission, leases/generations, tenant-scoped storage, active-job quota, cancellation, candidate review, and atomic local publication.

## Run

Python 3.11 or newer; standard library only. From this directory:

```sh
python3 experiment.py
python3 -m unittest discover -v
```

The experiment creates a temporary database, launches a subprocess that claims a job and exits with code 23, then reopens/reclaims the job. Explicit logical times exercise lease expiry without waiting. It publishes one artifact into a local database table, not an external service.

## Evidence

The saved report retains running generation 1 after exit, replacement generation 2, false stale submission, true replacement submission/approval, false duplicate approval, exactly one local receipt, cancellation followed by false late submission, and an empty other-tenant receipt list. Twenty-three tests cover concurrent claims, lease boundaries, tenant scoping, quota, duplicates, review identity, cancellation states, actual process exit, connection cleanup, and rejection of coerced submission generations and clock values without state mutation.

`enqueue` returns True for new admission and False for an identical existing request; inspect retrieves state. Changed payload under the same key raises a conflict. Claim/approval validate prior state under a serialized write transaction; submit additionally conditions its update on state, generation, and deadline. Read/schema connections close explicitly, separately from transaction commit semantics.

## Scope

Tenant strings, reviewer authority, candidate semantics, clock inputs, and database access are trusted. No public authentication, fair scheduler, worker renewal, full attempt journal, retention service, hard timeout, power-loss test, remote effect, or distributed fencing guarantee. Active quota counts queued/running/review jobs; generation rejection protects this database boundary only.

Completed publication and state are atomic because both live in the same SQLite transaction. External delivery requires its own operation identity and reconciliation. Temporary databases are removed after each experiment; JSON retains sanitized fixture evidence and source fingerprints.
