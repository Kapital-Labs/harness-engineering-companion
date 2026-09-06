# Chapter 12 companion

Deterministic defense tests and a local containment exercise over Chapter 11's boundary. Keep Chapters 11, 5, 4, and 2 alongside this directory for the inherited implementation.

```sh
python3 -m unittest discover -v
python3 experiment.py
```

Requires Python 3.11 or newer and the standard library. Actual runtime checks appear in [Compatibility](../COMPATIBILITY.md#chapter-12).

`defenses.py` defines ten cases, a small outcome evaluator, a session wrapper, and the incident exercise. `test_defenses.py` tests their behavior. `experiment.py` prints sanitized outcomes and dependency fingerprints; `sample-report.json` preserves a captured run.

Nine cases propose actions that the scenario forbids. Eight produce no prohibited effect. The intentionally mistaken approval produces one disclosure of a fake marker, and the evaluator must report that failure even though the case carries a scripted refusal annotation. The permitted-summary control requires one exact outbox entry. A passing unit suite includes correct detection of the deliberately failing security property; it does not mean every demonstration row is secure.

The incident preserves one existing disclosure, closes local admission, empties permissions, and clears approvals. The pending send and later read are denied. A fresh, reduced recovery session reads the benign review file and rejects raw, encoded, and benign sends. Recovery restores a read-only task, not publishing.

No real secret, external message, live model, network transport, asynchronous worker, credential revocation, or process-isolation experiment occurs. The outbox and events are in memory. Capturing the report preserves sanitized results, not a raw forensic archive. The evaluator's literal marker check is fixture-specific; unknown authoritative effects use an inconclusive result rather than an empty effect list.

The handoff text and marker are test data, not instructions to follow. Controller-owned policy and event methods are not model tools. See the shared [Incident response and security logging references](../REFERENCES.md#incident-response-and-security-logging) for background.

The read oracle compares protected text in the same JSON representation as the complete reply, so newlines, quotes, and backslashes do not hide a literal disclosure. It does not decode arbitrary attacker transformations.
