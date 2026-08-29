# Security Policy

## Scope and intent

ConciergeAgent is a **demonstration platform**. It models banking, insurance,
and wealth-management workflows, but it holds no real customer data, performs no
real financial transactions, and has no authentication layer. Do not deploy it
against production customer records without adding authentication, authorization,
audit logging, and data-retention controls appropriate to your jurisdiction.

## Reporting a vulnerability

Open a
[security advisory](https://github.com/asadullah48/conciergeagent/security/advisories/new)
rather than a public issue. Please include reproduction steps and the affected
version.

## Controls currently in place

| Control | Where |
| :--- | :--- |
| Explicit CORS allowlist, no wildcard with credentials | `conciergeagent/core/config.py`, `conciergeagent/server.py` |
| Input validation at the API boundary (ranges, lengths, enums) | `conciergeagent/core/models.py` |
| Unhandled exceptions return a structured error, never a traceback | `conciergeagent/server.py` |
| Container runs unprivileged (uid 10001), read-only root filesystem | `Dockerfile`, `helm/values.yaml`, `docker-compose.yml` |
| No secrets in source; configuration is environment-driven | `.env.example` |
| Dependency updates monitored | `.github/dependabot.yml` |

## Known limitations

- **No authentication or rate limiting** on `/api/v1/concierge/interact`. Put it
  behind a gateway that provides both before exposing it publicly.
- **Sentiment classification is lexical**, not a trained model. It can be evaded
  and should not be relied on as a safety control.
- **`/metrics` is unauthenticated.** Set `METRICS_ENABLED=false`, or restrict the
  route at the ingress, if the endpoint is reachable from outside the cluster.
