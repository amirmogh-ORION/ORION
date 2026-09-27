from orion.agents import Commander, StubAgent, AgentContext

def test_commander_runs_all_agents():
    commander = Commander([
        StubAgent("a", "A"),
        StubAgent("b", "B"),
    ])
    reports = commander.run_cycle(AgentContext(cycle_id="c1", subjects=["X", "Y"]))
    assert len(reports) == 4
    assert {r.agent for r in reports} == {"a", "b"}
