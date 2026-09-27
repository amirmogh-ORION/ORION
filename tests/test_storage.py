from orion.storage import create_session_factory, DecisionRow

def test_storage_creates_schema():
    Session = create_session_factory("sqlite:///:memory:")
    with Session() as session:
        session.add(DecisionRow(asset="X", state="WATCH", thesis="t", confidence=0.5))
        session.commit()
        assert session.query(DecisionRow).count() == 1
