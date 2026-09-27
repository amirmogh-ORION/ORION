# ORION Agent Registry

## Commander
**Role:** Orchestration and final synthesis.
**Inputs:** schedules, user requests, agent reports.
**Outputs:** task graph, research brief, decision package.
**Guardrail:** cannot override risk controls silently.

## Opportunity Scout
**Role:** broad discovery.
**Inputs:** market universe, screening rules, news/events.
**Outputs:** candidate opportunities with reasons and source evidence.

## Fundamental Analyst
**Role:** business and valuation analysis.
**Outputs:** quality assessment, financial trends, valuation scenarios, thesis/invalidation.

## Quant Analyst
**Role:** systematic analysis.
**Outputs:** signals, factor exposures, backtests, statistical confidence, robustness checks.

## Macro & Regime Analyst
**Role:** identify market/economic conditions relevant to strategies.
**Outputs:** regime classification, macro risks, scenario impacts.

## News & Catalyst Analyst
**Role:** identify material events.
**Outputs:** catalyst timeline, event risk, source-backed interpretation.

## Alternative Data Analyst
**Role:** non-traditional signals.
**Outputs:** sentiment/trend indicators with methodology and limitations.

## Risk Manager
**Role:** protect the system from uncontrolled exposure.
**Outputs:** risk budget, concentration, correlation, drawdown, liquidity and sizing constraints.
**Veto:** may block a proposed action when defined risk limits are breached.

## Portfolio Manager
**Role:** translate evidence into portfolio-level actions.
**Outputs:** allocation scenarios and BUY/WATCH/REINVEST/REDUCE/EXIT state.

## Decision Auditor
**Role:** preserve decision history and auditability.
**Outputs:** immutable decision records and provenance.

## Learning Agent
**Role:** measure prediction quality and improve process.
**Outputs:** calibration, error analysis, signal performance, experiments.

## Dashboard Reporter
**Role:** make system activity visible.
**Outputs:** daily brief, weekly review, agent health, open decisions.

## Engineering Agent
**Role:** reliability and software delivery.
**Outputs:** tests, fixes, integrations, deployment health.

## Agent independence rule

Specialists should produce their own analysis before seeing another specialist's conclusion whenever practical. This reduces correlated reasoning and makes disagreement measurable.
