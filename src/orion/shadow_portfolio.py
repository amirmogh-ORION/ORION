"""Fail-closed shadow portfolio allocation policy.

Pure decision logic only: no broker, network, or order-placement capability.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite

PAPER_CAPITAL_CAD = 1000.0

@dataclass(frozen=True)
class ShadowAllocation:
    approved: bool
    amount_cad: float
    reason: str
    risk_veto: bool = False

def evaluate_shadow_allocation(*, requested_cad: float, current_portfolio_cad: float,
                               evidence_fresh: bool, evidence_verified: bool,
                               specialist_votes: tuple[str, ...],
                               risk_veto: bool, instrument_type: str = "LONG_CASH") -> ShadowAllocation:
    """Evaluate a paper allocation without producing an executable order."""
    if instrument_type != "LONG_CASH":
        return ShadowAllocation(False, 0.0, "Only unlevered long cash positions are permitted.", True)
    if risk_veto:
        return ShadowAllocation(False, 0.0, "Risk veto is active.", True)
    if not evidence_fresh or not evidence_verified:
        return ShadowAllocation(False, 0.0, "Evidence is stale, missing, or unverified.", True)
    if not specialist_votes:
        return ShadowAllocation(False, 0.0, "No independent specialist conclusions.", True)
    normalized = {vote.strip().upper() for vote in specialist_votes}
    if len(normalized) != 1:
        return ShadowAllocation(False, 0.0, "Unresolved specialist disagreement.", True)
    if normalized != {"APPROVE"}:
        return ShadowAllocation(False, 0.0, "Specialists did not unanimously approve.", True)
    values = (requested_cad, current_portfolio_cad)
    if any(not isinstance(v, (int, float)) or not isfinite(v) or v < 0 for v in values):
        return ShadowAllocation(False, 0.0, "Invalid portfolio sizing input.", True)
    if requested_cad <= 0:
        return ShadowAllocation(False, 0.0, "Requested allocation must be positive.", True)
    if current_portfolio_cad + requested_cad > PAPER_CAPITAL_CAD:
        return ShadowAllocation(False, 0.0, "CAD 1,000 hard portfolio cap would be exceeded.", True)
    return ShadowAllocation(True, float(requested_cad), "Shadow allocation passed all gates.", False)
