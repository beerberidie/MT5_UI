

## Confidence Scoring Model (NEW)

Score = weighted sum of rules + news/econ modifiers → **0–100**.

- Base votes: Entry(+30), Strong(+25), Weak(−15), Exit(−40)
- Alignment bonus: Trend/timeframe/session alignment (+10)
- News/Econ penalty: High‑impact within embargo window (−20 to −40)

**Action thresholds**
- < 60 → Observe only
- 60–74 → Watch / allow pending orders only
- ≥ 75 → Place market/pending order if RR ≥ min_rr and risk rules allow
