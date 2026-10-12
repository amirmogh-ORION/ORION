from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class DecisionState(str, Enum):
    WATCH = "WATCH"
    BUY = "BUY"
    REINVEST = "REINVEST"
    REDUCE = "REDUCE"
    EXIT = "EXIT"
    NO_ACTION = "NO_ACTION"


class AssetClass(str, Enum):
    EQUITY = "equity"
    ETF = "etf"
    COMMODITY = "commodity"
    PRECIOUS_METAL = "precious_metal"
    CRYPTO = "crypto"
    OTHER = "other"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Evidence(BaseModel):
    source: str
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    claim: str
    reliability: float = Field(ge=0, le=1)


class AgentReport(BaseModel):
    agent: str
    subject: str
    conclusion: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[Evidence] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Decision(BaseModel):
    asset: str
    asset_class: AssetClass = AssetClass.OTHER
    state: DecisionState
    thesis: str
    confidence: float = Field(ge=0, le=1)
    expected_return: float | None = None
    downside: float | None = None
    invalidation: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    agents_consulted: list[str] = Field(default_factory=list)
    review_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Prediction(BaseModel):
    decision_id: str
    metric: str
    horizon_days: int = Field(gt=0)
    predicted_value: float
    confidence: float = Field(ge=0, le=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Outcome(BaseModel):
    prediction_id: str
    actual_value: float
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LearningRecord(BaseModel):
    prediction_id: str
    error: float
    lesson: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------- Paper trading models ----------

class OrderRequest(BaseModel):
    """Intent to place a paper (or later live) order."""
    symbol: str
    side: OrderSide
    quantity: float = Field(gt=0)
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = None
    stop_price: float | None = None
    decision_id: str | None = None
    thesis: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Fill(BaseModel):
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float = 0.0
    filled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    broker_exec_id: str | None = None


class Order(BaseModel):
    id: str
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType
    limit_price: float | None = None
    stop_price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float | None = None
    decision_id: str | None = None
    thesis: str | None = None
    broker_order_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fills: list[Fill] = Field(default_factory=list)


class Position(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    market_price: float | None = None
    market_value: float | None = None
    unrealized_pnl: float | None = None
    currency: str = "CAD"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PortfolioSnapshot(BaseModel):
    account_id: str
    cash: float
    equity: float
    buying_power: float
    positions: list[Position] = Field(default_factory=list)
    open_orders: list[Order] = Field(default_factory=list)
    currency: str = "CAD"
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "ibkr_paper"
