# Automation & Orchestration

- Scheduler: cron/n8n to run **data ingest** (07:00 SAST) and **daily prompt** (09:30).
- Pipeline: ingest → validate → features → (optional train) → backtest → deploy → trade.
- Tracking: CSV or MLflow; version configs in Git; secrets in `.env`.
- Hot‑swap: reload models/configs without downtime where possible.
