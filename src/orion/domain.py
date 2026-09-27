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
    evidence: list[Evidence] = []
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Decision(BaseModel):
    asset: str
    asset_class: AssetClass = AssetClass.OTHER
    state: DecisionState
    thesis: str
    confidence: float = Field(ge=0, le=1)
    expected_return: float | None = None
    downside: float | None = None
    invalidation: list[str] = []
    evidence: list[Evidence] = []
    agents_consulted: list[str] = []
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
