# ORION Architecture

## 1. System layers

### Orchestration
The Commander receives scheduled jobs and user requests, creates a task graph, assigns work to specialist agents, collects evidence, and produces a decision package.

### Research
Specialist agents independently investigate the same opportunity from different perspectives.

### Evidence
Every material claim should carry:
- source;
- retrieval timestamp;
- source type;
- confidence;
- relevant time period;
- transformation/calculation where applicable.

### Decision
The Portfolio Manager combines research with explicit risk constraints. The system records a decision state rather than pretending certainty.

### Learning
The Learning Agent compares forecasts against realized outcomes and identifies:
- false positives;
- false negatives;
- calibration errors;
- recurring research weaknesses;
- signal decay;
- regime dependence.

## 2. Agent topology

```
                    COMMANDER
                        |
        +---------------+---------------+
        |               |               |
   OPPORTUNITY       MACRO          NEWS/CATALYST
      SCOUT          REGIME             |
        |               |               |
        +-------+-------+-------+-------+
                |               |
          FUNDAMENTAL        QUANT
                |               |
                +-------+-------+
                        |
                     RISK
                        |
                   PORTFOLIO
                        |
              +---------+---------+
              |                   |
          DECISION             DASHBOARD
           AUDITOR             REPORTER
              |
           LEARNING
              |
         PROCESS/WEIGHTS
         IMPROVEMENT
              |
          COMMANDER
```

## 3. Decision states

- **WATCH** — interesting, insufficient evidence for action.
- **BUY** — evidence supports a defined entry thesis.
- **REINVEST** — existing thesis remains valid and capital can be reconsidered.
- **REDUCE** — risk/reward or exposure has deteriorated.
- **EXIT** — thesis invalidated or risk constraints breached.
- **NO ACTION** — insufficient edge.

These are system states, not guarantees of future performance.

## 4. Required decision record

Each decision should contain:

- asset/instrument;
- timestamp;
- decision state;
- thesis;
- catalysts;
- invalidation conditions;
- valuation/signal data;
- risk metrics;
- position/exposure;
- confidence;
- evidence references;
- agents consulted;
- model/prompt/version identifiers;
- expected horizon;
- expected return range;
- downside scenario;
- review date.

## 5. Learning contract

ORION must preserve a distinction between:

**Prediction**
What the system believed would happen.

**Outcome**
What actually happened.

**Evaluation**
How accurate/useful the prediction was.

**Improvement**
What process change should be tested next.

Historical records are append-only. Improvements create new versions rather than modifying old decisions.

## 6. Persistence

The production architecture should include:

- relational database for durable state;
- object storage for research artifacts;
- job scheduler/queue for recurring work;
- API layer;
- dashboard;
- alerting;
- observability;
- secrets management;
- version-controlled agent definitions.

A chat interface is an operator console, not the perpetual runtime.

## 7. Renaissance-inspired principles

ORION can learn from publicly documented systematic-investing principles such as:
- diversified independent signals;
- statistical testing;
- disciplined risk management;
- automation;
- continuous measurement;
- minimizing discretionary bias.

ORION does **not** assume access to or reproduce any proprietary Renaissance Technologies strategy.
