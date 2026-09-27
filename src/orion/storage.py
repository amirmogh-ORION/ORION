from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

class Base(DeclarativeBase):
    pass

class DecisionRow(Base):
    __tablename__ = "decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset: Mapped[str] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(30), index=True)
    thesis: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class PredictionRow(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    decision_id: Mapped[str] = mapped_column(String(100), index=True)
    metric: Mapped[str] = mapped_column(String(100))
    horizon_days: Mapped[int] = mapped_column(Integer)
    predicted_value: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class OutcomeRow(Base):
    __tablename__ = "outcomes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[str] = mapped_column(String(100), index=True)
    actual_value: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class LearningRow(Base):
    __tablename__ = "learning_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[str] = mapped_column(String(100), index=True)
    error: Mapped[float] = mapped_column(Float)
    lesson: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

def create_session_factory(url: str = "sqlite:///orion.db"):
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
