

## Autonomy Loop (NEW)

Run every N minutes during allowed sessions for each profiled symbol:

1) **Fetch** latest bars/news/calendar → compute indicators
2) **Evaluate EMNR** rules → {entry, exit, strong, weak}
3) **Score** with confidence model → 0–100
4) **Consult scheduler** (risk %, min RR, open/modify/close/skip)
5) **Act** via gateway (place/modify/close) or **skip**
6) **Log** cycle outputs: Trade idea, RR plan, Confidence, Execution plan, Monitoring plan
