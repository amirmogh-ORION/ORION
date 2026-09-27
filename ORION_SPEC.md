# ORION Operating Specification

## Objective

Maximize the quality of repeatable, evidence-based opportunity identification and capital-allocation research while minimizing uncontrolled risk and decision bias.

## Priority order

1. Data integrity
2. Risk constraints
3. Evidence quality
4. Statistical validity
5. Independent research
6. Decision clarity
7. Performance
8. Process improvement

## Continuous cycle

### Daily
- ingest new data;
- scan universe;
- detect catalysts;
- update active theses;
- monitor risk;
- evaluate due predictions;
- produce operator report.

### Weekly
- review decisions;
- attribute performance;
- inspect false positives/negatives;
- review signal stability;
- identify experiments;
- update research priorities.

### Monthly
- strategy/process review;
- regime analysis;
- model drift check;
- agent reliability review;
- cost/performance review;
- archive research artifacts.

## Decision quality metrics

Track at minimum:
- hit rate;
- expected vs realized return;
- downside forecast error;
- calibration by confidence bucket;
- maximum drawdown;
- Sharpe-like risk-adjusted measures where appropriate;
- turnover;
- exposure;
- concentration;
- false discovery rate;
- signal decay;
- research latency;
- data-source reliability.

No single metric should be treated as sufficient evidence of a strategy's quality.

## Capital lifecycle

For every active position or thesis:

**DISCOVER → VALIDATE → ENTER/WAIT → MONITOR → REASSESS → REINVEST/REDUCE/EXIT → REVIEW → LEARN**

Every transition requires a reason and timestamp.

## Human control

The default system is decision-support. Live trading or financial transfers require explicit authorization and a separately configured execution layer.

## Definition of done for ORION

ORION is not complete when an agent can generate text.

ORION is complete when it can reliably:
1. discover;
2. investigate independently;
3. preserve evidence;
4. quantify uncertainty;
5. make a traceable decision state;
6. monitor the thesis;
7. evaluate the outcome;
8. learn from the outcome;
9. improve through versioned experiments;
10. operate repeatedly without a human keeping the chat open.
