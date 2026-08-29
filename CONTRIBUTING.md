# Contributing to ConciergeAgent

Thanks for taking a look. This is a portfolio-grade reference implementation, so
the bar is "would this survive a code review at work", not "does it run".

## Setup

```bash
git clone https://github.com/asadullah48/conciergeagent.git
cd conciergeagent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## The checks CI runs

Run these before opening a pull request; they are exactly what `.github/workflows/ci.yml` runs.

```bash
ruff check conciergeagent tests            # lint
pytest tests -v --cov=conciergeagent       # tests + coverage
coverage report --fail-under=90            # coverage floor
docker build -t conciergeagent:dev .       # image builds
```

## Expectations for a change

- **Tests come with the change.** Coverage must stay at or above 90%. A bug fix
  should add a regression test named after the bug it prevents - see
  `test_ids_survive_hash_randomisation_across_processes` for the pattern.
- **Constraints belong in the type, not in a comment.** If a value has a valid
  range, express it as a Pydantic `Field(...)` constraint or a `model_validator`
  so invalid input is rejected at the API boundary.
- **Keep the dependency surface small.** The runtime depends on five packages.
  Adding a sixth needs a reason in the pull request description.
- **Do not widen CORS.** The gateway sends credentials; `allow_origins=["*"]`
  is a security defect here, not a convenience. Add origins to
  `DEFAULT_ALLOWED_ORIGINS` or set `ALLOWED_ORIGINS` at deploy time.
- **Match the specification.** `SPEC.md` is the source of truth for the tier
  privilege matrix and the sentiment escalation tree. If behaviour should
  change, change the spec in the same pull request.

## Project layout

| Path | Responsibility |
| :--- | :--- |
| `conciergeagent/core/models.py` | Domain types and their invariants |
| `conciergeagent/core/config.py` | Environment-driven settings |
| `conciergeagent/core/identifiers.py` | Reproducible session and ticket IDs |
| `conciergeagent/core/loyalty_policy.py` | Perk entitlement decisions |
| `conciergeagent/core/personalization_engine.py` | Sentiment grading, tier SLA matrix |
| `conciergeagent/core/observability.py` | JSON logging, metrics registry |
| `conciergeagent/agents/` | The three specialist agents |
| `conciergeagent/orchestration/` | Routing and response assembly |
| `conciergeagent/server.py` | FastAPI gateway |
| `conciergeagent/static/` | Bilingual dashboard (no build step) |

## Commit messages

Conventional Commits, e.g. `fix(core): make ticket ids reproducible across processes`.
