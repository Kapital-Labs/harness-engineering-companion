# References

Shared documentation references for the companion repository. Chapter READMEs link to the relevant entries here so dates and source details are maintained in one place.

Access dates record when a page was consulted. A source's publication date or specification version, when supplied, identifies a different fact. Actual implementation checks belong in [Compatibility notes](COMPATIBILITY.md).

## Messages API

Anthropic, [Create a Message](https://platform.claude.com/docs/en/api/messages/create). Accessed September 5, 2026. Used by the Chapter 2 adapter.

## Handling tool calls

Anthropic, [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls). Accessed September 5, 2026. Covers native tool requests and paired results used in Chapter 2.

## Single and parallel tool calls

Anthropic, [Parallel tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/parallel-tool-use). Accessed September 5, 2026. Covers the single-call setting used in Chapter 2.

## Agent evaluation

Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents). Published January 9, 2026; accessed September 5, 2026. Task, trial, grader, and outcome terminology used in Chapter 3. The companion's narrow grading rules are book-specific implementation choices.

## Tool-interface design

Yang et al., [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering](https://arxiv.org/html/2405.15793v3), arXiv:2405.15793v3, November 11, 2024. Sections 2–3 and 5.1 inform the Chapter 4 discussion of interface design. Accessed September 5, 2026. Our window reader and scripted comparison are teaching implementations, not a reproduction of the paper's experiment.

## Authorization and execution isolation

- OWASP, [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): least privilege, default denial, per-request checks.
- Docker, [Running containers](https://docs.docker.com/engine/containers/run/): users, mounts, network and resource options.
- Docker, [None network driver](https://docs.docker.com/engine/network/drivers/none/): network isolation configuration.
- Docker, [Engine security](https://docs.docker.com/engine/security/): kernel/runtime and daemon trust boundaries.

All accessed September 5, 2026. Actual local probe versions and limits are recorded in COMPATIBILITY.md; documentation consultation alone does not establish runtime enforcement.

## Controlled edits and verification

- Python Software Foundation, [subprocess](https://docs.python.org/3/library/subprocess.html): process arguments, pipes, exit codes, and timeout handling.
- Python Software Foundation, [difflib](https://docs.python.org/3/library/difflib.html): unified-diff generation and line-ending conventions.

Accessed September 5, 2026. Chapter 6 reuses the Chapter 5 Docker runtime documentation and configuration; executed versions are recorded separately.

## Context composition

- Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), September 29, 2025: context organization and dynamic retrieval.
- Liu et al., [Lost in the Middle](https://arxiv.org/abs/2307.03172v3), arXiv:2307.03172v3, November 20, 2023: position-sensitive use of evidence in the paper's experiments.
- OWASP, [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/): indirect injection and limits of textual controls.

Accessed September 5, 2026. No protocol integration or model performance is verified by the Chapter 7 offline example. Byte accounting and selection rules are book-specific; measured runtimes remain in COMPATIBILITY.md.

## Repository navigation and setup

- OpenAI, [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/), February 11, 2026: short repository entry documents, structured guidance, and maintenance checks. Attributed case study, not a controlled result for this book.
- Python Software Foundation, [ast](https://docs.python.org/3/library/ast.html) and [unittest](https://docs.python.org/3/library/unittest.html): source parsing, node positions, and test discovery.

Accessed September 5, 2026. Chapter 8's generated map and navigation controls are original teaching implementations. No protocol or live model was tested.

## Checkpoints and resumption

- Anthropic, [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), November 26, 2025: continuity through progress records and incremental sessions.
- Python Software Foundation, [os](https://docs.python.org/3/library/os.html): file synchronization, replacement, and immediate exit; [json](https://docs.python.org/3/library/json.html): parsing hooks and serialization.

Accessed September 5, 2026. The checkpoint store is an original, single-writer local teaching implementation. Actual runtime and process-exit results are recorded separately; no power-loss or model-performance claim.

## Retries and operation identity

- Malcolm Featonby, Amazon Builders' Library, [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/): explicit operation identity and parameter equivalence.
- Python Software Foundation, [sqlite3](https://docs.python.org/3/library/sqlite3.html): transaction control and bound SQL parameters.
- AWS Well-Architected Framework, [REL05-BP03 Control and limit retry calls](https://docs.aws.amazon.com/wellarchitected/2023-04-10/framework/rel_mitigate_interaction_failure_limit_retries.html): retry limits, backoff, jitter, and layer ownership.

Accessed September 5, 2026. Chapter 10 simulates delivery failures against local SQLite effects. No AWS API, network service, model, or real review workflow was exercised.

## Security Boundary and Approval

OWASP Gen AI Security Project, [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/), 2025 taxonomy; accessed September 5, 2026. Direct/indirect input and mitigation guidance.

Kai Greshake et al., [Indirect Prompt Injection](https://arxiv.org/abs/2302.12173v2), arXiv:2302.12173v2, May 5, 2023; accessed September 5, 2026. Research background; Chapter 11 does not run the paper's model experiments.

OWASP Cheat Sheet Series, [Transaction Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Transaction_Authorization_Cheat_Sheet.html), accessed September 5, 2026. Action details, modification protection, execution checks, and expiry. The companion demonstrates local binding, not authenticated approval.

Anthropic, [Beyond permission prompts: making Claude Code more secure and autonomous](https://www.anthropic.com/engineering/claude-code-sandboxing), October 20, 2025; accessed September 5, 2026. Filesystem/network isolation and trusted proxy architecture. No product sandbox was exercised for Chapter 11.

## Incident Response and Security Logging

NIST, [SP 800-61 Revision 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final), final April 3, 2025; accessed September 5, 2026. Incident response recommendations within cybersecurity risk management. Chapter 12 demonstrates local containment only.

OWASP Cheat Sheet Series, [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html), accessed September 5, 2026. Selected event attributes, exclusion of sensitive data, and validation/sanitization. The companion has no remote logging or forensic archive.

## Tracing and Telemetry

OpenTelemetry, [Traces](https://opentelemetry.io/docs/concepts/signals/traces/), accessed September 5, 2026. Span relationships, context, timestamps, status, and attributes. The companion uses its own local teaching format.

Python Software Foundation, [time](https://docs.python.org/3/library/time.html), accessed September 5, 2026. `perf_counter_ns` and duration measurement. The report retains actual local counter values; they are not provider benchmarks.

OpenTelemetry, [Handling sensitive data](https://opentelemetry.io/docs/security/handling-sensitive-data/), accessed September 5, 2026. Minimization and treatment of sensitive attributes. No SDK, collector, or network exporter is exercised.

## Evaluation and Calibration

Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), January 9, 2026; accessed September 5, 2026. Regression/capability distinction and grader choices; Chapter 14 extends the earlier offline evaluation checkpoint.

Zheng et al., [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685v4), December 24, 2023; accessed September 5, 2026. Primary judge research. No human/model calibration study is performed by the companion.

NIST/SEMATECH, [Confidence intervals for proportions](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm), accessed September 5, 2026. Wilson formula used in a separately labeled hypothetical example.

## Resource Accounting and Latency

Google SRE, Rob Ewaschuk, [Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/), accessed September 5, 2026. Successful and failed request latency require separate interpretation. Chapter 15's byte counts are locally measured; weighted costs and scheduling times are hypothetical. Python duration-measurement documentation is listed under Tracing and Telemetry above. No provider price or model integration was tested for this chapter.

## Multi-Agent Coordination

Anthropic, [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system), June 13, 2025; accessed September 5, 2026. Delegation, context boundaries, and task-dependency tradeoffs. Chapter 16 uses authored proposals and does not reproduce the research system or its model evaluations.

Python Software Foundation, [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html), accessed September 5, 2026. Actual local ThreadPoolExecutor use; future cancellation does not stop already running calls. Documentation access is not minimum-version runtime verification.

## Protocol and Runtime Integration

MCP specification revision 2025-11-25: [Lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle), [Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools), and [Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization); accessed September 5, 2026. Local standard-I/O lifecycle/tool exchange tested; HTTP authentication consulted but not exercised.

Pydantic, [FunctionModel](https://pydantic.dev/docs/ai/api/models/function/), accessed September 5, 2026. Actual runtime with scripted decisions. Chapter 17 pins mcp 2.1.1 and pydantic-ai-slim 2.40.0 and locks resolved dependency versions; tested Python 3.12.14.

## Service Transactions and Releases

SQLite, [Transaction](https://sqlite.org/lang_transaction.html), accessed September 5, 2026. BEGIN IMMEDIATE and writer serialization. Python, [Connection context manager](https://docs.python.org/3/library/sqlite3.html#how-to-use-the-connection-context-manager), accessed September 5, 2026, distinguishes transaction handling from connection closure.

Google SRE Workbook, [Canarying Releases](https://sre.google/workbook/canarying-releases/), accessed September 5, 2026. Deployment design background; Chapter 19 does not deploy a canary. Chapter 20's domain rules and fixtures are original teaching examples, not sourced commercial policies.
