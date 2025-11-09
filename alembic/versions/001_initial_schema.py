"""Initial schema - AI Trading Platform Blueprint

Revision ID: 001
Revises: 
Create Date: 2025-10-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    trade_idea_status = postgresql.ENUM(
        'waiting', 'needs_approval', 'auto_executed', 'rejected', 'halted_by_risk',
        name='tradeideastatus',
        create_type=False
    )
    trade_idea_status.create(op.get_bind(), checkfirst=True)
    
    decision_action = postgresql.ENUM(
        'ai_proposed', 'ai_auto_executed', 'human_approved', 'human_rejected',
        'risk_rejected', 'ai_halted', 'ai_resumed',
        name='decisionaction',
        create_type=False
    )
    decision_action.create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Create strategies table
    op.create_table(
        'strategies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allowed_symbols', postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column('session_windows', postgresql.JSON(), nullable=False),
        sa.Column('entry_conditions', postgresql.JSON(), nullable=False),
        sa.Column('exit_rules', postgresql.JSON(), nullable=False),
        sa.Column('forbidden_conditions', postgresql.JSON(), nullable=False),
        sa.Column('risk_caps', postgresql.JSON(), nullable=False),
        sa.Column('rr_expectation', sa.Numeric(5, 2), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create risk_config table
    op.create_table(
        'risk_config',
        sa.Column('id', sa.Boolean(), primary_key=True),
        sa.Column('ai_trading_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('min_confidence_threshold', sa.Numeric(5, 2), nullable=False, server_default='90.0'),
        sa.Column('max_lot_size', sa.Numeric(10, 2), nullable=False),
        sa.Column('max_concurrent_trades', sa.Integer(), nullable=False),
        sa.Column('daily_profit_target', sa.Numeric(12, 2), nullable=False),
        sa.Column('stop_after_target', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_drawdown_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('halt_on_drawdown', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_off_watchlist_autotrade', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_halt_reason', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('id = true', name='single_row_check'),
    )
    
    # Create snapshot tables
    op.create_table(
        'snapshot_market',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('symbol', sa.Text(), nullable=False),
        sa.Column('timeframe', sa.Text(), nullable=False),
        sa.Column('open', sa.Numeric(18, 6), nullable=False),
        sa.Column('high', sa.Numeric(18, 6), nullable=False),
        sa.Column('low', sa.Numeric(18, 6), nullable=False),
        sa.Column('close', sa.Numeric(18, 6), nullable=False),
        sa.Column('volume', sa.Integer(), nullable=False),
        sa.Column('captured_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index('idx_snapshot_market_symbol_timeframe_captured', 'snapshot_market', 
                    ['symbol', 'timeframe', 'captured_at'])
    
    op.create_table(
        'snapshot_indicators',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('symbol', sa.Text(), nullable=False),
        sa.Column('timeframe', sa.Text(), nullable=False),
        sa.Column('rsi_14', sa.Numeric(6, 2), nullable=True),
        sa.Column('sma_50', sa.Numeric(18, 6), nullable=True),
        sa.Column('sma_200', sa.Numeric(18, 6), nullable=True),
        sa.Column('macd', postgresql.JSON(), nullable=True),
        sa.Column('atr', sa.Numeric(18, 6), nullable=True),
        sa.Column('captured_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index('idx_snapshot_indicators_symbol_timeframe_captured', 'snapshot_indicators',
                    ['symbol', 'timeframe', 'captured_at'])
    
    op.create_table(
        'snapshot_calendar',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('currency', sa.Text(), nullable=False),
        sa.Column('impact_level', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('previous_value', sa.Text(), nullable=True),
        sa.Column('forecast_value', sa.Text(), nullable=True),
        sa.Column('actual_value', sa.Text(), nullable=True),
        sa.Column('captured_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index('idx_snapshot_calendar_currency_event_time', 'snapshot_calendar',
                    ['currency', 'event_time'])
    op.create_index('idx_snapshot_calendar_captured', 'snapshot_calendar', ['captured_at'])
    
    op.create_table(
        'snapshot_news',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('headline', sa.Text(), nullable=False),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('symbols', postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('published_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('captured_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index('idx_snapshot_news_published', 'snapshot_news', ['published_at'])
    
    op.create_table(
        'snapshot_account',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('balance', sa.Numeric(18, 2), nullable=False),
        sa.Column('equity', sa.Numeric(18, 2), nullable=False),
        sa.Column('margin_used', sa.Numeric(18, 2), nullable=False),
        sa.Column('margin_free', sa.Numeric(18, 2), nullable=False),
        sa.Column('open_pl', sa.Numeric(18, 2), nullable=False),
        sa.Column('open_positions', sa.Integer(), nullable=False),
        sa.Column('captured_at', sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index('idx_snapshot_account_captured', 'snapshot_account', ['captured_at'])
    
    # Create trade_ideas table
    op.create_table(
        'trade_ideas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('symbol', sa.Text(), nullable=False),
        sa.Column('direction', sa.Text(), nullable=False),
        sa.Column('entry_price', sa.Numeric(18, 6), nullable=True),
        sa.Column('entry_range', postgresql.ARRAY(sa.Numeric()), nullable=True),
        sa.Column('stop_loss', sa.Numeric(18, 6), nullable=False),
        sa.Column('take_profit', postgresql.ARRAY(sa.Numeric()), nullable=False),
        sa.Column('expected_hold', sa.Text(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('status', trade_idea_status, nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('strategies.id'), nullable=True),
        sa.Column('snapshot_ref', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint("direction IN ('buy', 'sell')", name='check_direction'),
    )
    op.create_index('idx_trade_ideas_status', 'trade_ideas', ['status'])
    op.create_index('idx_trade_ideas_symbol_created', 'trade_ideas', ['symbol', 'created_at'])
    
    # Create decision_history table
    op.create_table(
        'decision_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('occurred_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('symbol', sa.Text(), nullable=True),
        sa.Column('action', decision_action, nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('risk_check_result', sa.Text(), nullable=True),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('strategies.id'), nullable=True),
        sa.Column('trade_idea_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('trade_ideas.id'), nullable=True),
        sa.Column('snapshot_ref', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('human_override', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.create_index('idx_decision_history_occurred', 'decision_history', ['occurred_at'])
    op.create_index('idx_decision_history_symbol_occurred', 'decision_history', ['symbol', 'occurred_at'])
    op.create_index('idx_decision_history_action_occurred', 'decision_history', ['action', 'occurred_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('decision_history')
    op.drop_table('trade_ideas')
    op.drop_table('snapshot_account')
    op.drop_table('snapshot_news')
    op.drop_table('snapshot_calendar')
    op.drop_table('snapshot_indicators')
    op.drop_table('snapshot_market')
    op.drop_table('risk_config')
    op.drop_table('strategies')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS decisionaction')
    op.execute('DROP TYPE IF EXISTS tradeideastatus')

