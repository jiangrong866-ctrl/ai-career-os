# AI Career OS v5 Flowchart

```text
Windows Task Scheduler
  -> run_v5.cmd
  -> scripts/run_v5.py
  -> load state/state.json
  -> daily_report()
       -> scripts/daily_loop.py
       -> reports/daily_report_YYYY-MM-DD.md
  -> learning_module()
       -> data/learning/learning_YYYY-MM-DD_*.md
  -> portfolio_module()
       -> data/portfolio/portfolio_update_YYYY-MM-DD.md
  -> side_business_module()
       -> data/side_business/service_offer_merchant_support_kb.md
  -> dashboard/dashboard.html
  -> state/state.json
  -> git add .
  -> git commit -m "v5 auto update: daily cycle"
  -> git push origin main
       -> success: state.status = success
       -> failure: retry x3, write logs/v5_error.log, state.status = degraded
```
