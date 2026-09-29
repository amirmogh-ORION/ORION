from orion.agents import Commander, StubAgent, AgentContext

def test_commander_runs_all_agents():
    commander = Commander([
        StubAgent("a", "A"),
        StubAgent("b", "B"),
    ])
    reports = commander.run_cycle(
        AgentContext(
            cycle_id="c1",
            subjects=["X", "Y"],
            active_rules=("Use verified evidence only",),
        )
    )
    assert len(reports) == 4
    assert {r.agent for r in reports} == {"a", "b"}
    assert all("1 active learned rules were loaded" in r.evidence[0].claim for r in reports)
