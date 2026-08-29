# 🎩 ConciergeAgent: Hyperpersonalized Service AI Platform

> **A luxury, white-glove customer concierge multi-agent framework delivering personalized wealth advisory, instant claims and dispute resolution, and five-star hospitality governance.**

[![CI](https://github.com/asadullah48/conciergeagent/actions/workflows/ci.yml/badge.svg)](https://github.com/asadullah48/conciergeagent/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-382%20passing-brightgreen.svg)](https://github.com/asadullah48/conciergeagent/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen.svg)](https://github.com/asadullah48/conciergeagent/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Asadullah%20Shafique-purple.svg)](https://asadullahshafique-devunity.vercel.app)

---

## 🚀 Key Value Propositions

1. **Wealth-Tier Awareness**: Dynamically tailors responses, dispute credit limits, and asset allocations based on client tier (`Retail`, `Premier`, `Private Client`, `Ultra-HNW`).
2. **Proactive Financial Advisory**: Delivers tax-optimized, private equity and fixed income allocations via `AdvisorAgent`.
3. **Instant Claim & Dispute Triage**: Grants instant provisional dispute credits up to $50,000 and fast-tracks VIP insurance claims via `SupportAgent`.
4. **Five-Star Hospitality Governance**: Employs `ExperienceAgent` to monitor real-time sentiment, award luxury loyalty gifts, and trigger executive handovers.
5. **Interactive Luxury Studio**: Live glassmorphic dashboard with client tier toggles, sentiment speedometers, and bilingual (English/Arabic RTL) UI.

---

## 🏛️ Concierge Multi-Agent Architecture

```
                    ┌─────────────────────────┐
                    │     Customer Inquiry    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Personalization Engine │
                    │ • Wealth Tier Profiling │
                    │ • Sentiment Scoring     │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌──────────────────┐                           ┌──────────────────┐
│   AdvisorAgent   │                           │   SupportAgent   │
│ • Asset Alloc.   │                           │ • Dispute Credit │
│ • Tax Efficiency │                           │ • Claim Triage   │
│ • Private Market │                           │ • Zero-Liability │
└────────┬─────────┘                           └────────┬─────────┘
         │                                              │
         └───────────────────────┬──────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     ExperienceAgent     │
                    │ • 5-Star Hospitality    │
                    │ • Loyalty Perk Gifting  │
                    │ • Executive Escalation  │
                    └─────────────────────────┘
```

---

## 🛠️ Quick Start

```powershell
# 1. Clone repository
git clone https://github.com/asadullah48/conciergeagent.git
cd conciergeagent

# 2. Install dependencies
pip install -e .

# 3. Run automated test suite
python -m pytest tests -v

# 4. Start local gateway & frontend dashboard
uvicorn conciergeagent.server:app --host 127.0.0.1 --port 8005 --reload
```

- **Interactive Dashboard**: [http://127.0.0.1:8005/](http://127.0.0.1:8005/)
- **Swagger OpenAPI Docs**: [http://127.0.0.1:8005/docs](http://127.0.0.1:8005/docs)

---

## 🌐 Connected Ecosystem & Portfolio

- **DevUnity Portfolio**: [https://asadullahshafique-devunity.vercel.app](https://asadullahshafique-devunity.vercel.app)
- **ContextX**: [https://github.com/asadullah48/contextx](https://github.com/asadullah48/contextx)
- **GuardrailAI**: [https://github.com/asadullah48/guardrailai](https://github.com/asadullah48/guardrailai)
- **MarketAgentHub**: [https://github.com/asadullah48/marketagenthub](https://github.com/asadullah48/marketagenthub)
- **WorkforceAI**: [https://github.com/asadullah48/workforceai](https://github.com/asadullah48/workforceai)
- **DomainX**: [https://github.com/asadullah48/domainx](https://github.com/asadullah48/domainx)
