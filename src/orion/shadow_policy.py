"""Fail-closed shadow decision policy for ORION research.

This module does not connect to a broker or place orders. It turns specialist
research votes into an auditable shadow allocation ceiling.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

MAX_SHADOW_PORTFOLIO_CAD = Decimal("1000.00")

@dataclass(frozen=True)
class SpecialistVote:
    agent: str
    decision: str
    evidence_fresh: bool
    risk_veto: bool = False

def shadow_allocation_cap(
    votes: list[SpecialistVote],
    current_shadow_exposure_cad: Decimal,
    requested_cad: Decimal,
) -> Decimal:
    """Return allowed shadow allocation, or zero when evidence/gates disagree."""
    if current_shadow_exposure_cad < 0 or requested_cad <= 0:
        return Decimal("0")
    if not votes or any(not v.evidence_fresh for v in votes):
        return Decimal("0")
    if any(v.risk_veto for v in votes):
        return Decimal("0")
    decisions = {v.decision.upper() for v in votes}
    if decisions != {"QUALIFIED"}:
        return Decimal("0")
    remaining = MAX_SHADOW_PORTFOLIO_CAD - current_shadow_exposure_cad
    if remaining <= 0:
        return Decimal("0")
    return min(requested_cad, remaining)
