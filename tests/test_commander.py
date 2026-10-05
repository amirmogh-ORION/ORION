from orion.agents import Commander, StubAgent, AgentContext
from orion.domain import AgentReport, Evidence

def test_commander_runs_all_agents():
    commander = Commander([StubAgent("a", "A"), StubAgent("b", "B")])
    reports = commander.run_cycle(AgentContext(cycle_id="c1", subjects=["X", "Y"],
        active_rules=("Use verified evidence only",)))
    assert len(reports) == 4
    assert {r.agent for r in reports} == {"a", "b"}
    assert all("1 active learned rules were loaded" in r.evidence[0].claim for r in reports)

def report(agent, conclusion, reliability=1.0, confidence=.8):
    return AgentReport(agent=agent, subject="X", conclusion=conclusion, confidence=confidence,
                       evidence=[Evidence(source="test", claim="verified", reliability=reliability)])

def test_commander_records_and_blocks_specialist_disagreement():
    decision = Commander([StubAgent("x","x")]).synthesize([
        report("Quant Agent", "APPROVE: positive case"),
        report("Research Agent", "REJECT: evidence conflict"),
    ])[0]
    assert decision.state == "NO_ACTION"
    assert decision.disagreements
    assert set(decision.agents_consulted) == {"Quant Agent", "Research Agent"}

def test_risk_veto_is_non_overridable():
    decision = Commander([StubAgent("x","x")]).synthesize([
        report("Quant Agent", "APPROVE: positive case"),
        report("Research Agent", "APPROVE: supported"),
        report("Risk Agent", "VETO: downside exceeds limit"),
    ])[0]
    assert decision.state == "NO_ACTION"
    assert decision.risk_veto

def test_unanimous_verified_approval_is_shadow_only():
    decision = Commander([StubAgent("x","x")]).synthesize([
        report("Quant Agent", "APPROVE: positive case"),
        report("Research Agent", "APPROVE: supported"),
        report("Risk Agent", "APPROVE: within limits"),
    ])[0]
    assert decision.state == "SHADOW_APPROVED"

def test_weak_evidence_fails_closed():
    decision = Commander([StubAgent("x","x")]).synthesize([
        report("Quant Agent", "APPROVE: positive case", reliability=.5),
        report("Risk Agent", "APPROVE: within limits"),
    ])[0]
    assert decision.state == "NO_ACTION"
