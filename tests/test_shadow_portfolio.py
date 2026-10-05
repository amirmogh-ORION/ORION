from orion.shadow_portfolio import PAPER_CAPITAL_CAD, evaluate_shadow_allocation

def good(**overrides):
    args = dict(requested_cad=100, current_portfolio_cad=0, evidence_fresh=True,
                evidence_verified=True, specialist_votes=("APPROVE", "APPROVE"),
                risk_veto=False, instrument_type="LONG_CASH")
    args.update(overrides)
    return evaluate_shadow_allocation(**args)

def test_cap_is_exactly_cad_1000_and_cumulative():
    assert PAPER_CAPITAL_CAD == 1000
    assert good(requested_cad=250, current_portfolio_cad=750).approved
    assert not good(requested_cad=250.01, current_portfolio_cad=750).approved

def test_fails_closed_on_stale_or_unverified_evidence():
    assert not good(evidence_fresh=False).approved
    assert not good(evidence_verified=False).approved

def test_unresolved_disagreement_blocks_allocation():
    result = good(specialist_votes=("APPROVE", "REJECT"))
    assert not result.approved
    assert result.risk_veto

def test_risk_veto_cannot_be_overridden():
    assert not good(risk_veto=True).approved

def test_leverage_options_and_shorting_are_not_permitted():
    for kind in ("LEVERAGED_LONG", "OPTION", "SHORT"):
        assert not good(instrument_type=kind).approved

def test_invalid_sizing_fails_closed():
    for value in (-1, float("nan"), float("inf")):
        assert not good(requested_cad=value).approved
