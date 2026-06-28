# Consistency Enforcement

Every daily run must satisfy all gates:

1. Executable: at least one concrete next action is generated for job, learning, side-business, and portfolio.
2. Deliverable: at least one file is written under `reports/`, `data/learning/`, or `data/portfolio/`.
3. Persistence: every run appends to local CSV/JSONL ledgers and queues GitHub sync when remote commit is unavailable.
4. Privacy: no job application, email send, public publish, or third-party website write happens without explicit confirmation.
5. Ranking: jobs and side-business tasks must be sorted by weighted score before output.

If any gate fails, the run is incomplete and must write a blocked reason to `state/memory.json` or `queue/`.
