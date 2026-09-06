# Chapter 20 Companion

Worked synthetic examples for research, support, and data quality. This is a synthesis checkpoint, not a capstone project.

## Run

Python 3.11 or newer; standard library only. Keep Chapter 18 alongside this directory for the support queue:

```sh
python3 experiment.py
python3 -m unittest discover -v
```

## Results

- Research preserves two conflicting authored claims, with each source entry binding its value to its source/revision/digest identity. An absent question returns insufficient evidence. The records are structured fixtures, not extracted real-world claims or assessed sources. Value comparison is exact: it does not normalize units or resolve differences in product-version scope.
- Support validates a trusted account/order record and invented amount policy, prepares a proposal, and uses the Chapter 18 local review lifecycle. Zero receipts before approval; one after; duplicate approval adds none. Real refunds remain zero.
- Data quality scans three rows and records two rule findings on row position 1: duplicate ID and missing email. Inputs remain unchanged; rows deleted remain zero. Empty input retains a zero population rather than claiming complete ingestion.

Thirteen tests verify these contract behaviors and failure cases, including claim-to-source associations under reversed source order. The report includes source fingerprints for this chapter and its Chapter 18 dependency and reproduces exactly on the recorded interpreter.

## Limits

No model, retrieval, source credibility scoring, semantic fact checking, authentication, current commercial refund policy, actual payment, database remediation, or production-data quality estimate. Functions expect trusted structured fixture input, not arbitrary hostile JSON. Account and reviewer identities, input versions, and domain semantics need their own enforcement in an application. The local approval flow does not re-evaluate changing policy; the manuscript identifies that required production boundary.
