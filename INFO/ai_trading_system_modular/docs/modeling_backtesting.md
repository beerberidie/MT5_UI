# Modeling, Backtesting & Simulation

## Features & Labels
- Targets: forward returns (T+N), meta-labels (trade/no-trade).
- Features: ATR/volatility, moving averages, spreads, calendar effects, simple price action patterns.
- Leakage Control: time-series CV with embargo/purging.

## Walk-Forward Backtesting
- Rolling windows; re-fit periodically.
- Model families: GBMs, LSTMs/Transformers for sequence modeling (optional).
- Cost Modeling: spreads, swaps, slippage; broker rules (FIFO, min step).

## Stress Tests
- Flash-crash gaps; spread widening; data outages; latency spikes.
- Report: Sharpe, Sortino, profit factor, drawdowns, turnover.
