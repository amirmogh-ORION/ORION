"""ORION paper portfolio engine.

Translates research decisions into paper orders under strict risk limits.
All capital actions remain explicit and logged.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from orion.broker.ibkr import IBKRPaperBroker
from orion.domain import (
    Decision,
    DecisionState,
    Order,
    OrderRequest,
    OrderSide,
    OrderStatus,
    PortfolioSnapshot,
)

logger = logging.getLogger(__name__)


class RiskLimits:
    """Conservative limits sized for a ~$1,000 paper account."""

    def __init__(
        self,
        max_position_pct: float = 0.20,       # max 20% of equity in one name
        max_order_notional: float = 200.0,    # hard $ cap per order
        min_cash_buffer: float = 50.0,       # keep some cash
        max_open_positions: int = 5,
        allow_fractional: bool = False,
    ):
        self.max_position_pct = max_position_pct
        self.max_order_notional = max_order_notional
        self.min_cash_buffer = min_cash_buffer
        self.max_open_positions = max_open_positions
        self.allow_fractional = allow_fractional


class PortfolioEngine:
    """Decision → paper order bridge with risk gates."""

    def __init__(
        self,
        broker: IBKRPaperBroker,
        limits: RiskLimits | None = None,
        price_lookup: Callable[[str], float | None] | None = None,
    ):
        self.broker = broker
        self.limits = limits or RiskLimits()
        self.price_lookup = price_lookup
        self.order_log: list[Order] = []

    def current_snapshot(self) -> PortfolioSnapshot:
        return self.broker.snapshot()

    def size_order(self, decision: Decision, snapshot: PortfolioSnapshot) -> float | None:
        """Return quantity to trade, or None if risk rejects."""
        if decision.state not in (DecisionState.BUY, DecisionState.REINVEST):
            return None

        price = None
        if self.price_lookup:
            price = self.price_lookup(decision.asset)
        if price is None or price <= 0:
            logger.warning("No usable price for %s — cannot size", decision.asset)
            return None

        equity = max(snapshot.equity, 1.0)
        cash = snapshot.cash

        # Position count gate
        if len(snapshot.positions) >= self.limits.max_open_positions:
            if not any(p.symbol == decision.asset for p in snapshot.positions):
                logger.info("Max open positions reached (%s)", self.limits.max_open_positions)
                return None

        # Notional limits
        max_by_pct = equity * self.limits.max_position_pct
        max_by_cash = max(0.0, cash - self.limits.min_cash_buffer)
        notional = min(max_by_pct, max_by_cash, self.limits.max_order_notional)

        if notional < price * 0.5:  # too small to bother
            logger.info("Sized notional too small for %s (%.2f)", decision.asset, notional)
            return None

        qty = notional / price
        if not self.limits.allow_fractional:
            qty = int(qty)
        if qty < 1:
            return None
        return float(qty)

    def execute_decision(self, decision: Decision) -> Order | None:
        """Convert a BUY/REINVEST decision into a paper order if risk allows."""
        snapshot = self.current_snapshot()
        qty = self.size_order(decision, snapshot)
        if qty is None:
            return None

        req = OrderRequest(
            symbol=decision.asset,
            side=OrderSide.BUY,
            quantity=qty,
            decision_id=None,  # can wire later when Decision has stable id
            thesis=decision.thesis,
        )
        order = self.broker.place_order(req)
        self.order_log.append(order)
        logger.info(
            "Paper order submitted: %s %s x%s | thesis=%s",
            order.side.value,
            order.symbol,
            order.quantity,
            (decision.thesis or "")[:80],
        )
        return order

    def execute_exit(self, symbol: str, reason: str = "EXIT") -> Order | None:
        """Close an existing paper position."""
        snapshot = self.current_snapshot()
        pos = next((p for p in snapshot.positions if p.symbol == symbol), None)
        if not pos or pos.quantity <= 0:
            logger.info("No long position in %s to exit", symbol)
            return None

        req = OrderRequest(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=abs(pos.quantity),
            thesis=reason,
        )
        order = self.broker.place_order(req)
        self.order_log.append(order)
        return order
