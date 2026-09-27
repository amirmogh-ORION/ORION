from orion.domain import Decision, DecisionState, AssetClass

def test_decision_validation():
    d = Decision(
        asset="TEST",
        asset_class=AssetClass.EQUITY,
        state=DecisionState.WATCH,
        thesis="test",
        confidence=0.7,
    )
    assert d.state is DecisionState.WATCH
    assert d.confidence == 0.7
