"""
Database models and configuration for PostgreSQL.

This module defines SQLAlchemy models matching the AI Trading Platform Blueprint schema.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Boolean, Column, Integer, String, Numeric, Text, TIMESTAMP,
    ForeignKey, CheckConstraint, Index, ARRAY, JSON, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

Base = declarative_base()


# Enums
class TradeIdeaStatus(str, enum.Enum):
    """Trade idea status enum."""
    WAITING = "waiting"
    NEEDS_APPROVAL = "needs_approval"
    AUTO_EXECUTED = "auto_executed"
    REJECTED = "rejected"
    HALTED_BY_RISK = "halted_by_risk"


class DecisionAction(str, enum.Enum):
    """Decision action enum."""
    AI_PROPOSED = "ai_proposed"
    AI_AUTO_EXECUTED = "ai_auto_executed"
    HUMAN_APPROVED = "human_approved"
    HUMAN_REJECTED = "human_rejected"
    RISK_REJECTED = "risk_rejected"
    AI_HALTED = "ai_halted"
    AI_RESUMED = "ai_resumed"


# Models
class Strategy(Base):
    """Strategy definition table."""
    __tablename__ = "strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    allowed_symbols = Column(ARRAY(Text), nullable=False)
    session_windows = Column(JSON, nullable=False)
    entry_conditions = Column(JSON, nullable=False)
    exit_rules = Column(JSON, nullable=False)
    forbidden_conditions = Column(JSON, nullable=False)
    risk_caps = Column(JSON, nullable=False)
    rr_expectation = Column(Numeric(5, 2), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trade_ideas = relationship("TradeIdea", back_populates="strategy")
    decision_history = relationship("DecisionHistory", back_populates="strategy")


class RiskConfig(Base):
    """Global AI Control Panel + Risk Management configuration."""
    __tablename__ = "risk_config"

    id = Column(Boolean, primary_key=True, default=True)  # Single row table
    ai_trading_enabled = Column(Boolean, nullable=False, default=False)
    min_confidence_threshold = Column(Numeric(5, 2), nullable=False, default=90.0)
    max_lot_size = Column(Numeric(10, 2), nullable=False)
    max_concurrent_trades = Column(Integer, nullable=False)
    daily_profit_target = Column(Numeric(12, 2), nullable=False)
    stop_after_target = Column(Boolean, nullable=False, default=True)
    max_drawdown_amount = Column(Numeric(12, 2), nullable=False)
    halt_on_drawdown = Column(Boolean, nullable=False, default=True)
    allow_off_watchlist_autotrade = Column(Boolean, nullable=False, default=False)
    last_halt_reason = Column(Text, nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('id = true', name='single_row_check'),
    )


class SnapshotMarket(Base):
    """Raw candle data snapshots."""
    __tablename__ = "snapshot_market"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(Text, nullable=False)
    timeframe = Column(Text, nullable=False)
    open = Column(Numeric(18, 6), nullable=False)
    high = Column(Numeric(18, 6), nullable=False)
    low = Column(Numeric(18, 6), nullable=False)
    close = Column(Numeric(18, 6), nullable=False)
    volume = Column(Integer, nullable=False)
    captured_at = Column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        Index('idx_snapshot_market_symbol_timeframe_captured', 'symbol', 'timeframe', 'captured_at'),
    )


class SnapshotIndicators(Base):
    """Computed indicators snapshots."""
    __tablename__ = "snapshot_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(Text, nullable=False)
    timeframe = Column(Text, nullable=False)
    rsi_14 = Column(Numeric(6, 2), nullable=True)
    sma_50 = Column(Numeric(18, 6), nullable=True)
    sma_200 = Column(Numeric(18, 6), nullable=True)
    macd = Column(JSON, nullable=True)
    atr = Column(Numeric(18, 6), nullable=True)
    captured_at = Column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        Index('idx_snapshot_indicators_symbol_timeframe_captured', 'symbol', 'timeframe', 'captured_at'),
    )


class SnapshotCalendar(Base):
    """Economic calendar events snapshots."""
    __tablename__ = "snapshot_calendar"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_time = Column(TIMESTAMP(timezone=True), nullable=False)
    currency = Column(Text, nullable=False)
    impact_level = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    previous_value = Column(Text, nullable=True)
    forecast_value = Column(Text, nullable=True)
    actual_value = Column(Text, nullable=True)
    captured_at = Column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        Index('idx_snapshot_calendar_currency_event_time', 'currency', 'event_time'),
        Index('idx_snapshot_calendar_captured', 'captured_at'),
    )


class SnapshotNews(Base):
    """News + RSS feed snapshots."""
    __tablename__ = "snapshot_news"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    headline = Column(Text, nullable=False)
    source = Column(Text, nullable=False)
    symbols = Column(ARRAY(Text), default=[])
    published_at = Column(TIMESTAMP(timezone=True), nullable=False)
    captured_at = Column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        Index('idx_snapshot_news_published', 'published_at'),
    )


class SnapshotAccount(Base):
    """Account state snapshots from MT5."""
    __tablename__ = "snapshot_account"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    balance = Column(Numeric(18, 2), nullable=False)
    equity = Column(Numeric(18, 2), nullable=False)
    margin_used = Column(Numeric(18, 2), nullable=False)
    margin_free = Column(Numeric(18, 2), nullable=False)
    open_pl = Column(Numeric(18, 2), nullable=False)
    open_positions = Column(Integer, nullable=False)
    captured_at = Column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        Index('idx_snapshot_account_captured', 'captured_at'),
    )


class TradeIdea(Base):
    """Current + historical AI trade proposals."""
    __tablename__ = "trade_ideas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(Text, nullable=False)
    direction = Column(Text, nullable=False)
    entry_price = Column(Numeric(18, 6), nullable=True)
    entry_range = Column(ARRAY(Numeric), nullable=True)
    stop_loss = Column(Numeric(18, 6), nullable=False)
    take_profit = Column(ARRAY(Numeric), nullable=False)
    expected_hold = Column(Text, nullable=True)
    rationale = Column(Text, nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=False)
    status = Column(SQLEnum(TradeIdeaStatus), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey('strategies.id'), nullable=True)
    snapshot_ref = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    strategy = relationship("Strategy", back_populates="trade_ideas")
    decision_history = relationship("DecisionHistory", back_populates="trade_idea")

    __table_args__ = (
        CheckConstraint("direction IN ('buy', 'sell')", name='check_direction'),
        Index('idx_trade_ideas_status', 'status'),
        Index('idx_trade_ideas_symbol_created', 'symbol', 'created_at'),
    )


class DecisionHistory(Base):
    """Full audit trail of all AI and human decisions."""
    __tablename__ = "decision_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    occurred_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    symbol = Column(Text, nullable=True)
    action = Column(SQLEnum(DecisionAction), nullable=False)
    rationale = Column(Text, nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=True)
    risk_check_result = Column(Text, nullable=True)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey('strategies.id'), nullable=True)
    trade_idea_id = Column(UUID(as_uuid=True), ForeignKey('trade_ideas.id'), nullable=True)
    snapshot_ref = Column(UUID(as_uuid=True), nullable=True)
    human_override = Column(Boolean, nullable=False, default=False)

    # Relationships
    strategy = relationship("Strategy", back_populates="decision_history")
    trade_idea = relationship("TradeIdea", back_populates="decision_history")

    __table_args__ = (
        Index('idx_decision_history_occurred', 'occurred_at'),
        Index('idx_decision_history_symbol_occurred', 'symbol', 'occurred_at'),
        Index('idx_decision_history_action_occurred', 'action', 'occurred_at'),
    )


class User(Base):
    """User accounts for JWT authentication."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_users_email', 'email'),
    )

