# AI Autonomous Trading System — Modular Documentation
*Build date: 2025-10-02*

This repository splits the unified blueprint into focused modules:

- `docs/architecture.md` — Final system architecture & project structure
- `docs/data_research.md` — Data schema, ingest pipeline, Perplexity workflow
- `docs/strategy_execution.md` — Strategy edge, daily execution rules, gold timings
- `docs/modeling_backtesting.md` — Features, labeling, walk‑forward, stress tests
- `docs/risk_portfolio.md` — Risk caps, sizing, portfolio rules, kill switches
- `docs/execution_gateway.md` — MT5↔Python FastAPI gateway & order flow
- `docs/dashboard_user_guide.md` — Tradecraft UI features & how‑to
- `docs/automation_orchestration.md` — Schedulers, pipelines, tracking
- `docs/compliance_cost_resilience.md` — Audit, free stack, resilience playbook
- `docs/daily_sop.md` — Morning→Trade→Evening checklist
- `appendices/prompts.md` — Reusable Perplexity prompts
- `appendices/json_schema.md` — Daily data JSON schema
- `appendices/python_validator.md` — Validator + CSV writer (ready to run)
- `appendices/gold_trading_cheatsheet.md` — Hours, lot sizing, quick rules
- `appendices/trade_logging_template.md` — Table template for reviews

> Notes:
> - This repo is designed to be copied into your project root.
> - You can merge or extend sections as you iterate.
