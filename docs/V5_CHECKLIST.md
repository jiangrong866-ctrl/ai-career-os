# AI Career OS v5 Verification Checklist

- [ ] `scripts/run_v5.py` exists.
- [ ] `scripts/scheduler.py` exists.
- [ ] `scripts/auto_git.py` exists.
- [ ] `scripts/recovery.py` exists.
- [ ] `run_v5.cmd` exists.
- [ ] `state/state.json` is updated after a run.
- [ ] `logs/v5_runtime.log` records `START`, module status, and `END`.
- [ ] `logs/v5_error.log` records git retry failures when push fails.
- [ ] `dashboard/dashboard.html` is regenerated after a run.
- [ ] Git remote remains `https://github.com/jiangrong866-ctrl/ai-career-os.git`.
- [ ] Branch remains `main`.
- [ ] Windows Task Scheduler has a daily 20:30 trigger.
- [ ] Windows Task Scheduler has a logon trigger.
- [ ] Windows Task Scheduler runs with highest privileges.
