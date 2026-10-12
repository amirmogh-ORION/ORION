"""Interactive Brokers paper-trading connector.

Requires IB Gateway (or TWS) running and logged into a Paper account.
Default port 4002 = IB Gateway paper.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from orion.domain import (
    Fill,
    Order,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    PortfolioSnapshot,
    Position,
)

logger = logging.getLogger(__name__)


class IBKRPaperBroker:
    """Thin wrapper around ib_insync for paper trading only."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4002,
        client_id: int = 1,
        account: str | None = None,
    ):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.account = account
        self._ib = None

    def connect(self) -> None:
        from ib_insync import IB

        if self._ib and self._ib.isConnected():
            return
        self._ib = IB()
        self._ib.connect(self.host, self.port, clientId=self.client_id)
        if not self.account:
            accounts = self._ib.managedAccounts()
            if accounts:
                self.account = accounts[0]
        logger.info("Connected to IBKR paper on %s:%s account=%s", self.host, self.port, self.account)

    def disconnect(self) -> None:
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
            logger.info("Disconnected from IBKR")

    def is_connected(self) -> bool:
        return bool(self._ib and self._ib.isConnected())

    def snapshot(self) -> PortfolioSnapshot:
        self._ensure_connected()
        assert self._ib is not None

        # Account values
        values = {av.tag: av.value for av in self._ib.accountValues() if av.currency in ("CAD", "BASE", "")}
        cash = float(values.get("TotalCashValue") or values.get("$LEDGER-CashBalance") or 0)
        equity = float(values.get("NetLiquidation") or cash)
        buying_power = float(values.get("BuyingPower") or cash)

        # Positions
        positions: list[Position] = []
        for p in self._ib.positions():
            if abs(p.position) < 1e-8:
                continue
            avg_cost = float(p.avgCost)
            qty = float(p.position)
            mkt_price = None
            mkt_value = None
            upnl = None
            try:
                # Best-effort market price from portfolio items
                for item in self._ib.portfolio():
                    if item.contract.symbol == p.contract.symbol:
                        mkt_price = float(item.marketPrice) if item.marketPrice else None
                        mkt_value = float(item.marketValue) if item.marketValue else None
                        upnl = float(item.unrealizedPNL) if item.unrealizedPNL else None
                        break
            except Exception:
                pass
            positions.append(
                Position(
                    symbol=p.contract.symbol,
                    quantity=qty,
                    avg_cost=avg_cost,
                    market_price=mkt_price,
                    market_value=mkt_value,
                    unrealized_pnl=upnl,
                    currency="CAD",
                )
            )

        return PortfolioSnapshot(
            account_id=self.account or "unknown",
            cash=cash,
            equity=equity,
            buying_power=buying_power,
            positions=positions,
            currency="CAD",
            source="ibkr_paper",
        )

    def place_order(self, req: OrderRequest) -> Order:
        """Place a paper order. Returns the local Order record."""
        self._ensure_connected()
        assert self._ib is not None
        from ib_insync import MarketOrder, LimitOrder, Stock

        contract = Stock(req.symbol, "SMART", "USD")  # US stocks via SMART
        self._ib.qualifyContracts(contract)

        if req.order_type == OrderType.MARKET:
            ib_order = MarketOrder(req.side.value, req.quantity)
        elif req.order_type == OrderType.LIMIT:
            if req.limit_price is None:
                raise ValueError("limit_price required for LIMIT orders")
            ib_order = LimitOrder(req.side.value, req.quantity, req.limit_price)
        else:
            raise NotImplementedError(f"Order type {req.order_type} not yet supported")

        trade = self._ib.placeOrder(contract, ib_order)
        order_id = str(uuid4())

        order = Order(
            id=order_id,
            symbol=req.symbol,
            side=req.side,
            quantity=req.quantity,
            order_type=req.order_type,
            limit_price=req.limit_price,
            status=OrderStatus.SUBMITTED,
            decision_id=req.decision_id,
            thesis=req.thesis,
            broker_order_id=str(trade.order.orderId) if trade.order else None,
        )
        logger.info("Submitted paper order %s %s %s qty=%s", order.id, order.side, order.symbol, order.quantity)
        return order

    def _ensure_connected(self) -> None:
        if not self.is_connected():
            self.connect()
