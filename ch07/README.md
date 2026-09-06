# Chapter 7 companion — Context composition

From this directory, using Python 3.11 or newer:

```sh
python3 experiment.py
python3 -m unittest discover -v
```

Standard library; keep sibling Chapters 2–6 in place. No API key, model call, Docker run, real repository mutation, or publication action. The freshness demonstration imports the saved Chapter 6 verification record and checks its candidate hash against the reproduced candidate.

## Files and evidence

- `context.py`: immutable observations and a deterministic composer. Checks current read/disclosure path sets, source identity, exact excerpt provenance, and compact UTF-8 JSON size. Core overflow returns no payload; omitted required paths return needs_context.
- `experiment.py`: complete-file and tailored search/window routes on the five Chapter 3 tasks plus a long-policy variant, at 700 and 1,800 bytes. Uses the unchanged Chapter 3 grader with fixed answers and an explicitly synthetic retained-read projection.
- `sample-report.json`: 24 actual offline comparison rows, acquired observations, original replay events and grade, selected context and omission manifest, retained-evidence grade, source hashes, and saved-result freshness cases.
- Tests cover boundary budgets, multibyte text, stale reads/results, revocation, separate disclosure, provenance corruption, duplicate identifiers, intact snapshots, missing evidence, and a ready payload that lacks the required function body.

## Interpretation limits

`ready` means required paths are represented and the payload fits, not that the evidence is sufficient. The grader catches the deliberately incomplete function-body case. A missing-implementation answer has no citations under the Chapter 3 contract; its passing grade does not establish exhaustive absence.

The retrieval routes are operator-written for public fixtures. They are neither a generic repository search algorithm nor live-model performance measurements. The original injection replay includes a denied shell request; the synthetic retained-read projection is only for evidence grading and must not be substituted for its security trace.

Byte counts measure two separate representations: retrieved observation arrays and selected payloads. They exclude provider wrappers/tool schemas, query arguments, search-response serialization (the searches are local), output tokens, and the controller-only manifest. Retrieval operation counts represent planned local searches/reads, not network latency or billed usage. No tokenizer or provider serialization is implemented.

The composer receives controller-owned typed observations and trusted verification records. It is not an external-record parser, secret detector, authorization service, prompt-injection defense, or provider adapter. Read and disclosure grants are supplied by trusted code. Only candidate identity is checked for verification applicability here; production also needs suite/environment/policy identity. Snapshot source is synthetic text. Audit retention and metadata disclosure require their own controls in a service.

See [central references](../REFERENCES.md) and [compatibility notes](../COMPATIBILITY.md).

The manuscript's derived-summary and context-rebuild examples are design walkthroughs. `Observation` stores source windows, not model-written summaries; the companion does not implement summary generation or a provider context-rebuild loop.
