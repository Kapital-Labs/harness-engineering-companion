# Chapter 4 companion: tool interfaces

Run from this directory with Python 3.11 or newer:

```sh
python3 compare.py
python3 -m unittest discover -v
```

Uses the standard library. Keep ch02 beside ch04: tools.py imports the earlier action types, runtime, and prefix reader. It does not modify them. No provider account, network request, shell tool, or filesystem read capability is exposed to the scripted routes. The program itself reads its own source files to fingerprint the report.

`tools.py` defines read_file(path, start_line=1, line_count=40) and literal search(query, path=None). Read windows return complete lines only, at most 100 lines and 2000 source characters; oversized initial lines return line_too_long. Empty files return no span. A next_line value identifies a continuation position, not guaranteed readability. Search returns at most five 160-character previews with separate preview and match omission flags. Schemas document the interface; Python validation enforces it. Limits apply to content, not the whole JSON envelope, tokens, scan work, or memory use.

`compare.py` retains 21 rows: seven public synthetic development cases times three scripted routes. Each task supplies the target path. The window route uses a search result to select its starting line; expected spans stay in evaluator-owned cases. The dump control is intentionally unbounded and must stay confined to this small corpus. It is not a proposed production tool.

Expected sufficient-inspection totals: dump 7/7, prefix 5/7, window 6/7. All routes complete. No answer is graded, and answer_correct remains null. Absence means complete inspection of the named file, not repository-wide absence. The misleading note case measures exposure, not injection resistance. The many_mentions case includes irrelevant occurrences outside the supplied target path, so it does not test autonomous path discovery.

`sample-report.json` contains actual offline output, full traces, source fingerprints, and exact byte-count conventions. Rerun with `python3 compare.py > sample-report.json` after intentional source changes. The report excludes prompts, requests, schemas, and provider history from byte counts. It cannot establish model accuracy, token use, latency, or cost. No live mode is implemented in this checkpoint.

The Chapter 4 evidence checker validates returned text against complete source spans. It does not change the Chapter 3 grader. Central source dates and runtime checks are in [REFERENCES.md](../REFERENCES.md) and [COMPATIBILITY.md](../COMPATIBILITY.md).
