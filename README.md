# ORION

**ORION — Autonomous Intelligence & Investment Research System**

ORION is a continuously improving multi-agent system for market research, opportunity discovery, portfolio intelligence, risk management, decision tracking, and performance learning.

## Mission

Build a persistent research team that:
- continuously scans for opportunities;
- separates research, analysis, risk, and decision-making;
- records every thesis, forecast, confidence level, and outcome;
- evaluates what worked and what failed;
- improves its research process over time;
- produces clear **BUY / WATCH / REINVEST / REDUCE / EXIT** signals with evidence and uncertainty;
- never silently rewrites history.

ORION is initially a research and decision-support system. Actual financial transactions remain explicitly authorized by the human operator.

## Core agents

1. **Commander** — orchestration, task allocation, conflict resolution.
2. **Opportunity Scout** — discovers investable opportunities across asset classes.
3. **Fundamental Analyst** — financial statements, valuation, business quality.
4. **Quant Analyst** — systematic signals, statistics, backtests.
5. **Macro & Regime Analyst** — rates, inflation, liquidity, economic regime.
6. **News & Catalyst Analyst** — filings, earnings, events, catalysts.
7. **Alternative Data Analyst** — sentiment and non-traditional signals.
8. **Risk Manager** — exposure, correlation, drawdown, liquidity, sizing.
9. **Portfolio Manager** — portfolio construction and capital allocation scenarios.
10. **Decision Auditor** — immutable thesis/rationale/confidence/outcome records.
11. **Learning Agent** — forecast-vs-outcome analysis and process improvement.
12. **Dashboard Reporter** — daily/weekly status and actionable reports.
13. **Engineering Agent** — tests, reliability, integrations, deployments.

## Operating loop

**SCAN → RESEARCH → CROSS-CHECK → SCORE EVIDENCE → RISK CHECK → DECISION → LOG → OBSERVE → MEASURE → LEARN → IMPROVE**

ORION is designed to run on scheduled/event-driven infrastructure rather than relying on a chat session remaining open.

## Design principles

- Independent agents before consensus.
- Evidence before conclusions.
- Out-of-sample validation before trusting a strategy.
- Risk controls before position sizing.
- Every decision gets a timestamp and version.
- Predictions are scored after the outcome is known.
- Failed ideas become training data rather than being deleted.
- No agent may alter historical decisions.
- Human approval is required for live execution unless explicitly enabled later.

## Initial build status

The repository was initially empty. This commit establishes the ORION architecture and operating contract. The next build stages add the runtime, data connectors, persistent storage, agent implementations, scheduler, dashboard, evaluation engine, and tests.
