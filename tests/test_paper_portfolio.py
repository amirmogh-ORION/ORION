"""Smoke tests for paper portfolio layer.

These tests do not require a live IBKR connection.
Integration tests that hit Gateway are marked and skipped by default.
"""
from __future__ import annotations

import pytest

from orion.domain import (
    Decision,
    DecisionState,
    OrderRequest,
    OrderSide,
    OrderType,
    PortfolioSnapshot,
    Position,
)
from orion.portfolio import PortfolioEngine, RiskLimits


def test_risk_limits_size_buy():
    limits = RiskLimits(
        max_position_pct=0.20,
        max_order_notional=200.0,
        min_cash_buffer=50.0,
        max_open_positions=5,
        allow_fractional=False,
    )

    class FakeBroker:
        def snapshot(self):
            return PortfolioSnapshot(
                account_id="TEST",
                cash=1000.0,
                equity=1000.0,
                buying_power=1000.0,
                positions=[],
                currency="CAD",
            )

        def place_order(self, req: OrderRequest):
            from orion.domain import Order, OrderStatus
            from uuid import uuid4

            return Order(
                id=str(uuid4()),
                symbol=req.symbol,
                side=req.side,
                quantity=req.quantity,
                order_type=req.order_type,
                status=OrderStatus.SUBMITTED,
                thesis=req.thesis,
            )

    engine = PortfolioEngine(
        broker=FakeBroker(),  # type: ignore
        limits=limits,
        price_lookup=lambda s: 50.0,
    )

    decision = Decision(
        asset="AAPL",
        state=DecisionState.BUY,
        thesis="Test buy",
        confidence=0.6,
    )
    order = engine.execute_decision(decision)
    assert order is not None
    assert order.side == OrderSide.BUY
    assert order.quantity == 4  # min(200, 200, 950) / 50 = 4


def test_risk_rejects_when_too_many_positions():
    limits = RiskLimits(max_open_positions=1)

    class FakeBroker:
        def snapshot(self):
            return PortfolioSnapshot(
                account_id="TEST",
                cash=1000.0,
                equity=1000.0,
                buying_power=1000.0,
                positions=[Position(symbol="MSFT", quantity=1, avg_cost=100.0)],
                currency="CAD",
            )

        def place_order(self, req):
            raise AssertionError("should not place")

    engine = PortfolioEngine(
        broker=FakeBroker(),  # type: ignore
        limits=limits,
        price_lookup=lambda s: 50.0,
    )
    decision = Decision(asset="AAPL", state=DecisionState.BUY, thesis="x", confidence=0.5)
    assert engine.execute_decision(decision) is None


@pytest.mark.skip(reason="Requires running IB Gateway on port 4002")
def test_live_ibkr_connection():
    from orion.broker import IBKRPaperBroker

    broker = IBKRPaperBroker(port=4002)
    broker.connect()
    snap = broker.snapshot()
    assert snap.account_id
    assert snap.equity >= 0
    broker.disconnect()
