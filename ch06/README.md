# Chapter 6 companion: controlled edits and verification

## Default preparation

From this directory:

```sh
python3 demo.py
python3 -m unittest discover -v
```

Use Python 3.11 or newer. Keep sibling ch02, ch04, and ch05 directories. Default preparation needs only the standard library. `workflow.py` holds the scripted route and synthetic source; the uniquely named module avoids collisions with earlier chapters' demo modules.

The fixture reads a policy, uses its whole-file SHA-256 as a precondition, and proposes one exact replacement. Read and write grants are distinct. Only tracker/policy.py is writable. The candidate remains an in-memory copy; no user repository is edited. The returned review-package.json contains the diff, changed paths, base/candidate hashes, and trace. Verification is not_run, publication is not_requested, even though the loop completes.

The edit operation is synchronous and single-threaded. It rejects stale source, non-unique targets including overlaps, no-ops, oversized requests/results, and non-UTF-8 replacement text. It is not a general unified-diff application API, a multi-file transaction, or a shared-filesystem concurrency primitive. Caller-supplied snapshots and harness Python are trusted. Output hashes are identities, not approvals.

## Explicit verification experiment

With the Chapter 5 local Docker prerequisites, run:

```sh
python3 checks.py --image-id sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e
```

That ID identifies the already available image used for this book's recorded run. Supply the full ID of your own trusted local Linux image containing /usr/bin/python3 if it differs. No implicit pull is allowed. The recorded image was mcr.microsoft.com/playwright:v1.62.1-noble; this tooling-rich image is a test convenience, not a recommended production base.

The command runs four fresh restricted workers, staging only synthetic candidate strings into separate temporary directories. Same confinement as Chapter 5: read-only root and workspace, non-root UID, no added network, dropped capabilities, no-new-privileges, limited scratch, CPU/memory/PID configuration. The fixed controller-owned check driver is supplied through stdin. It is not available for modification through the edit tool. No real tests from a user repository are loaded.

Expected outcomes: before failed; candidate passed; overbroad failed; syntax_error failed. Candidate passes five fixed checks. The command exits 0 if all four expected outcomes occur and every probe container is confirmed absent, 1 on outcome/cleanup mismatch, 2 on a top-level execution error. A successfully executed experiment deliberately includes three failing candidates.

Output is limited to 16,384 captured bytes, with a 45-second worker wait budget plus bounded cleanup calls. Reported statuses distinguish test failure, invalid output, timeout, output limit, and Docker launch failures. Cleanup is recorded as confirmed_absent, remaining, or unknown. No guarantee is made after controller death. The selector-based pipe reader is exercised on macOS/POSIX; Windows controller support has not been verified.

`verification-report.json` records the actual four runs, staged candidate hashes, worker definition/image/source identities, cleanup outcomes, and a review package carrying candidate verification. `review-package.json` intentionally remains the offline unverified package. Regenerate each with its corresponding command; do not manually change verification status.

The checks and candidate execute in the same Python worker process. Malicious candidate code may interfere with or forge these results. The report is fixed-fixture behavioral evidence, not adversarial attestation, permission to publish, or a comprehensive application-security assessment. No model call or remote publication occurs.

See [compatibility](../COMPATIBILITY.md) and [references](../REFERENCES.md) for runtime evidence and source dates.

The manuscript also works through repair decisions after failed checks. That continuation is design guidance over these recorded variants; the companion does not implement an autonomous edit/test/retry loop.
