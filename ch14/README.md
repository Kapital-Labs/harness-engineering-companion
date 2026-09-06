# Chapter 14 companion

Evaluation comparison mechanics using Chapter 3's runtime, deterministic controls, tasks, and grader. Keep Chapters 3 and 2 alongside this folder.

```sh
python3 -m unittest discover -v
python3 experiment.py
```

Python 3.11 or newer, standard library only. Actual version verification is in [Compatibility](../COMPATIBILITY.md#chapter-14).

`comparison.py` schedules three repeats of five tasks for each of three controls: fixed baseline, full task-specific script, and the same script with source reads removed. The runtime and grader actually execute; no model or external tool is called. `sample-report.json` retains 45 row verdicts, split summaries, paired task deltas, configuration/source fingerprints, and authored calibration examples.

Expected pass counts are 6/15 for the fixed workflow, 15/15 for the full script, and 3/15 for the no-read ablation. Full versus baseline yields three task wins, zero losses, and two ties. Removing reads keeps the scripted answers but causes evidence checks to fail on four tasks. These are not model rankings.

All five tasks were public in Chapter 3. The illustrative_holdout group demonstrates partition/reporting mechanics, not unseen evaluation. Repeats have identical outcomes. The actual comparison has no statistical confidence interval. A separate hypothetical 20/25 binomial example computes a Wilson interval for stated independent-trial assumptions.

`rubric.md` defines the evidence packet and diagnosis rubric. Calibration labels and supplied judge outputs are authored examples; no judge model or human-review study ran. The parser checks output structure and known evidence IDs, not the truth of the judgment. Unknown judgments remain visible. Code-based hard requirements remain separate.

The example retains per-trial checks and security attempt/execution counts but does not save every underlying transcript. Chapter 13 covers richer diagnostic records. Setup failure/retry policy, real holdout governance, and statistical study design require additional work for a live evaluation.

Before constructing the report, `validate_schedule` checks all configuration/task/repeat keys against the declared schedule. It rejects missing, duplicate, and unexpected records, including a repeat omitted from both sides of a paired comparison. An explicit unknown verdict still counts as a scheduled row. The summary helper assumes this coverage check has occurred. Tests distinguish shared record loss from a retained unknown; no interrupted-run recovery service is implemented.

Sources are centralized under [Evaluation and calibration](../REFERENCES.md#evaluation-and-calibration).
