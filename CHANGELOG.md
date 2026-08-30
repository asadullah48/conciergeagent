# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0]

### Added

- **Optional LLM narration.** The concierge reply is still computed entirely
  by the deterministic rule engine; a model may now *restate* it in natural
  language before it reaches the customer (`conciergeagent/llm/`). Off by
  default - it only activates when `LLM_API_KEY` is set - and targets any
  OpenAI-compatible `/chat/completions` endpoint (Groq's free tier by
  default; Cerebras, OpenRouter, Together, or a local Ollama server all work
  by changing `LLM_BASE_URL`).
- **Faithfulness guardrail.** Every currency amount, percentage, ticket
  reference, and SLA guarantee in the deterministic reply is extracted and
  checked against the model's output; if any value was dropped, rounded, or
  altered, the narration is discarded and the deterministic reply is served
  instead. A model cannot turn `$50,000.00` into `$500,000.00` and have it
  reach a client.
- `narration_mode` on the response, reporting which path produced the reply:
  `DETERMINISTIC`, `LLM_NARRATED`, `LLM_FALLBACK_UNAVAILABLE`, or
  `LLM_FALLBACK_UNFAITHFUL` - a fallback is always visible, never silent.
- `response_language` request field (`en` / `ar`); narration honours it,
  letting the generated reply itself be produced in Arabic, not only the
  dashboard chrome around it.
- Dashboard now shows which path produced the on-screen reply (AI-narrated
  vs. deterministic, and why) next to the response.

### Changed

- Test suite expanded to 462 tests.

## [1.1.0]

### Fixed

- **Non-reproducible identifiers.** Session and ticket IDs were derived from the
  builtin `hash()`, which CPython seeds randomly per process. The same query
  produced a different ticket on every restart. Replaced with a BLAKE2b digest
  (`conciergeagent/core/identifiers.py`).
- **Unsafe CORS.** The gateway combined `allow_origins=["*"]` with
  `allow_credentials=True`, letting any site issue credentialed calls. Replaced
  with an explicit, environment-overridable allowlist.
- **Declared intent was silently overridden.** A `SUPPORT` interaction whose text
  happened to contain an advisory keyword was re-routed to the advisor. Routing
  is now driven solely by `intent_category`.
- **Perverse perk incentive.** A frustrated customer received a richer payout
  than a delighted one. Service recovery and loyalty rewards are now distinct
  instruments (`conciergeagent/core/loyalty_policy.py`).
- **Spec drift.** Neutral sentiment awarded a perk, contradicting SPEC.md
  section 4; and frustration triggered an executive handover, which the spec
  reserves for critical distress. Both now match the specification.
- **Empty CORS allowlist.** A whitespace-only `ALLOWED_ORIGINS` parsed to an
  empty list rather than falling back to the defaults.
- **Missing package marker.** `conciergeagent/core` had no `__init__.py` and
  relied on implicit namespace packaging.

### Added

- `LICENSE` (Apache 2.0) - the README advertised the licence without granting it.
- `/metrics` endpoint serving Prometheus text-format counters and a latency
  histogram, with no new dependency.
- Structured JSON logging (`conciergeagent/core/observability.py`).
- Environment-driven configuration (`conciergeagent/core/config.py`).
- `LOYALTY` intent lane, previously declared but unrouted.
- `intent_routed` on the response, reporting which lane handled an interaction.
- Enforced model constraints: sentiment range, query length, allocation weights
  summing to 1.0, ratings within 1-5, non-negative monetary fields.
- GitHub Actions CI: ruff lint, pytest across Python 3.10-3.13 with a coverage
  floor, and a Docker build that boots the image and smoke-tests the API.
- Dependabot configuration, `.dockerignore`, `.env.example`, `CONTRIBUTING.md`,
  `SECURITY.md`, and this changelog.

### Changed

- Test suite expanded from 13 to 382 tests at 99% statement coverage.
- Dockerfile is now multi-stage, ships no development dependencies, and runs as
  an unprivileged user (uid 10001).
- Helm chart adds pod and container security contexts, environment wiring, and
  Prometheus scrape annotations.
- `requirements.txt` holds runtime dependencies only; development tooling moved
  to `requirements-dev.txt` and the `dev` extra.
- Package metadata now names the actual author and links the repository,
  issue tracker, and portfolio.

## [1.0.0]

- Initial release: three specialist agents, tier-aware personalization engine,
  FastAPI gateway, and the bilingual (English / Arabic RTL) dashboard.
