# Mission recovery: evidence before percentage

The previous 30% maturity figure was an informal judgment. No measured baseline
or acceptance rubric supports a numeric change from that figure.

This implementation addresses three operational priorities:

1. A scheduled Commander cycle with distinct deterministic workers, task IDs,
   per-task output, explicit failed-source states and persisted cycle history.
2. Discovery across 168 stocks, ETFs, commodity proxies and crypto instruments,
   plus the official CanadaBuys open-tender CSV. Universe attempted and universe
   actually observed are separate counts. At most 12 market and 12 procurement
   leads are passed downstream per cycle.
3. Mandatory decision triage for each selected lead and the live Airtable backlog,
   with missing inputs, owner, review deadline, rejection reason and no capital
   action. Existing deadlines are not reset to disguise overdue work.

SEC company facts provide dated annual financial facts for selected equities.
The parser checks annual reporting duration, filing date and period age. It is
not a complete fundamental analyst, a valuation model or independent consensus.

## Persistence and operation

GitHub Actions runs the deterministic cycle every four hours, including weekends.
It pulls the current Airtable backlog, restores the previous state, archives full
cycle reports and updates the dedicated `orion-state` branch. Airtable receives
research sources, decisions, run records and worker summaries.

The existing ChatGPT ORION research task was separately changed from daily to
hourly, to investigate unresolved leads using primary and independent evidence.
Scheduling a task is not proof that its future runs will succeed.

The web console reads the persisted report; placeholder on-demand cycles are
retired. Evidence older than eight hours is labeled stale.

## What remains outside this implementation

- Independent specialist reasoning and full company/tender diligence.
- Economic qualification with verified expected return, downside and execution.
- 31 autonomous analysts: implemented workers cover only part of the registry.
- Validated backtests, model promotion and empirical learning improvements.
- Smart-money feeds and provider redundancy.
- Verified portfolio cash/positions, allocation, paper execution, exits and
  reinvestment accounting.

NEEDS DATA is unresolved. A transparent screening rejection is a research-screen
decision, not a fully investigated rejection. Task completion is engineering
throughput, not a measure of investment profitability.

Do not label overall mission maturity 60% until a defined mission rubric and
actual acceptance evidence justify that claim.
