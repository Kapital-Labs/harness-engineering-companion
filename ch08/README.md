# Chapter 8 companion — Repository navigation

From this directory, run with Python 3.11 or newer:

```sh
python3 preflight.py
python3 -m unittest discover -v
python3 experiment.py
```

Standard library only. No installation, key, Docker service, or sibling imports required for these commands. Preflight reports prerequisites, not test success. The saved reports record the runtime actually exercised.

## Contents

- `navigation.py`: generated top-level Python symbol map, scope/source freshness, guide dependency checks, unique-symbol resolution, and a controller-owned check-description registry. No source imports or command execution.
- `experiment.py`: 14 fixed navigation rows over seven cases, two routes, and a three-read budget. Retains acquisitions, failure states, definition checks, response bytes, and separate index input sizes.
- `preflight.py`: current runtime and required local-file checks; meaningful exit code and not_run test status.
- `sample-report.json`, `preflight-report.json`: actual offline outputs.
- Tests: map scope/additions, parse errors, duplicate symbols, stale guidance/maps, unreviewed targets, unknown checks, no source execution, fixture results, and missing setup files.

The experiment starts from the issue-closing policy used throughout the book. The caller here is only a comment fixture. No runtime dependency graph or behavioral verification is claimed for the moved file. Guessed paths and guide routes are tailored controls, not model performance.

## Check discovery

The registry advertises the Chapter 6 `checks.py` experiment by identifier. To run that separate checkpoint, use its [documented operator command](../ch06/README.md), including the approved local image ID. Chapter 8 does not run it. The Chapter 6 checker targets its own original fixtures; adapting it to a moved module is separate work. A recognized identifier does not grant execution authority or establish a pass.

## Limits

All source snapshots and maps are controller-owned finite data. Scope/disclosure authorization must precede indexing and context assembly; the map is not an authorization mechanism. The generator omits nested symbols, decorators from function spans, runtime bindings, call graphs, and non-Python files. It is not a sandboxed indexing service for unbounded hostile inputs.

Guide hashes record declared reviewed dependencies, not proof that a human review happened. Matching metadata cannot establish that prose or requirements are correct. A fresh generated map does not refresh a reviewed guide. `owner` is a maintenance label, not authenticated authority.

Response bytes use compact JSON arrays and exclude request/provider overhead. Index input bytes describe per-case source sizes, not parser time or aggregate work; the stale-map case reuses its saved map. No latency, token, billing, or model capability measurement.

See [references](../REFERENCES.md) and [compatibility](../COMPATIBILITY.md).
