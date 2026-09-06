# Chapter 11 companion

An offline example of the model–tool boundary: restricted model-facing reads, fixed destination identifiers, and approval bound to an exact action. It reuses Chapter 5's reader and its Chapter 4 and Chapter 2 dependencies. Keep the chapter folders together.

From this directory, run:

```sh
python3 -m unittest discover -v
python3 experiment.py
```

Python 3.11 or newer; standard library only. See [Compatibility](../COMPATIBILITY.md#chapter-11) for versions actually exercised.

`boundary.py` contains the trusted policy, observation wrapper, approval record, and executor. `experiment.py` arranges eight scripted delivery cases and prints the results. `sample-report.json` retains a captured run with source fingerprints. `test_boundary.py` checks changed content/destination/run/revision, expiry, single use, malformed arguments, and the read/disclosure distinction.

The note is an attack fixture, not an instruction for you to follow. No model reads it during this experiment. Every sensitive value is fake. Sends append to an in-memory local outbox; no network request or external message occurs.

Expected results: the private-file read is denied; six delivery cases produce no effect; the exact approved summary produces one effect. A final intentionally mistaken approval permits the fake private marker into the outbox. That control demonstrates that exact-action binding does not classify content or correct an approver's judgment.

`approve` represents a trusted UI callback. Do not expose it as a model tool. `run_id`, time, policy, and the source snapshot are controller inputs. The example has no authentication service, real approval UI, credential broker, network firewall, persistence, concurrency protection, or live-model security measurement. It assumes a trusted controller process. Approval consumption and outbox append do not replace Chapter 10's durable retry design for remote effects.

Background sources are centralized in [Companion references](../REFERENCES.md#security-boundary-and-approval). Numbered textbook citations remain in the book's shared bibliography.
