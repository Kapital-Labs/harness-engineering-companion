# Chapter 3 companion

This chapter evaluates the Chapter 2 harness on five synthetic development tasks. It reuses the sibling ch02 directory; download the complete companion rather than copying this folder alone. There are no third-party dependencies.

## Run offline

```sh
python3 evaluate.py
python3 -m unittest discover -v
```

The default compares a fixed policy-lookup workflow with task-specific scripted fixtures. Neither candidate is a language model. The workflow passes two of five tasks; the deliberately constructed fixtures pass five. Those fractions describe deterministic controls, not model performance. The fixtures include one unsupported tool request that the dispatcher denies.

Capture a report and exercise repeated-trial bookkeeping:

```sh
python3 evaluate.py > report.json
python3 evaluate.py --candidate scripted --repeats 2
```

Reports contain all trial traces, named grading checks, task and source fingerprints, interpreter version, timestamps, and elapsed time. The checked-in sample-report.json is actual captured offline output. Timestamps and elapsed times differ on reruns; compare task verdicts and stable configuration fingerprints rather than the entire JSON byte for byte.

Default exit code 0 means the evaluation completed, even if some tasks failed. To use the report as a pass gate:

```sh
python3 evaluate.py --candidate baseline --require-pass
```

That command exits 1 for the expected baseline failures. Invalid CLI configuration exits 2. The scripted fixture with --require-pass exits 0.

## What the grader checks

The final answer must be JSON with a conclusion label and citation spans. This is a constrained task, not a general free-text answer grader. Expected labels and evidence remain in evaluator-owned task metadata and are not included in the live model prompt. The offline scripted fixture is intentionally tailored to those public cases.

The grader checks completion, structure, expected conclusion, valid snapshot ranges, coverage of required source spans, and observations from successful read_file calls. For the known absence task, empty citations are allowed; that does not demonstrate exhaustive search of an arbitrary repository. This chapter deliberately requires read_file for cited evidence; alternative evidence interfaces would need an updated contract and grader.

Unauthorized requests and successful unauthorized operations are separate diagnostics. A denied request does not fail the sample's no-unauthorized-execution check. Reading the project note is optional in this task; exposure is recorded separately. The injection fixture's passing outcome does not certify model robustness: its bad request was scripted, the dispatcher exposed no shell, and the fixed baseline never read the attack document. These candidates do not provide a fair attack-resistance comparison.

Grading trusts traces emitted by the in-process runtime. It is not a validator for hostile uploaded traces or a cryptographic audit log. Task metadata is separated from the model's input, not isolated from arbitrary Python code in the same process.

## Optional live evaluation

Live evaluation is billable. Configure ANTHROPIC_API_KEY using your normal credential manager, then provide an exact model ID available to your account:

```sh
python3 evaluate.py --candidate live --model YOUR_AVAILABLE_MODEL_ID --repeats 2
```

The example makes up to six model calls per trial across five tasks. Two repeats can therefore attempt up to 60 model calls. The command runs sequentially and does not retry failures automatically. The adapter's socket timeout is not a whole-suite deadline.

Live reports retain the requested model ID and code/task fingerprints. The current adapter does not export usage totals, so live token usage and provider cost are null. Offline provider charges are zero; this is not an estimate of CPU, electricity, or labor cost. No live trial has been executed for this release.

See shared [References](../REFERENCES.md) for documentation dates and [Compatibility notes](../COMPATIBILITY.md) for actual verification.
