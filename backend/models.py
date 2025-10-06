from pydantic import BaseModel, Field
from typing import Literal, Optional, Union


class OrderRequest(BaseModel):
    canonical: str = Field(..., description="Canonical symbol, e.g., EURUSD")
    side: Literal["buy", "sell"]
    volume: float = Field(..., gt=0)
    sl: Optional[float] = None
    tp: Optional[float] = None
    deviation: int = 10
    comment: str = ""
    magic: int = 0


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Union[dict, None] = None


class ApiError(BaseModel):
    error: ErrorBody


# === PHASE 1 MODELS: PENDING ORDERS ===

class PendingOrderRequest(BaseModel):
    canonical: str = Field(..., description="Canonical symbol, e.g., EURUSD")
    order_type: Literal["buy_stop", "sell_stop", "buy_limit", "sell_limit"]
    volume: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    sl: Optional[float] = None
    tp: Optional[float] = None
    deviation: int = 10
    comment: str = ""
    magic: int = 0


class PendingOrderModifyRequest(BaseModel):
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    expiration: Optional[int] = None



# === PHASE 1 MODELS: HISTORICAL DATA ===

class HistoricalBarsRequest(BaseModel):
    symbol: str = Field(..., description="Symbol name")
    timeframe: Literal["M1", "M5", "M15", "M30", "H1", "H4", "D1"] = "M1"
    date_from: str = Field(..., description="Start date in ISO format")
    date_to: str = Field(..., description="End date in ISO format")


class HistoricalTicksRequest(BaseModel):
    symbol: str = Field(..., description="Symbol name")
    date_from: str = Field(..., description="Start date in ISO format")
    date_to: str = Field(..., description="End date in ISO format")
    flags: Optional[str] = "ALL"  # ALL, INFO, BID, ASK, LAST, VOLUME


# === PHASE 1 MODELS: TRADING HISTORY ===

class TradingHistoryRequest(BaseModel):
    date_from: str = Field(..., description="Start date in ISO format")
    date_to: str = Field(..., description="End date in ISO format")
    symbol: Optional[str] = None


# === AI TRADING MODELS ===

class EMNRFlags(BaseModel):
    """EMNR condition evaluation flags."""
    entry: bool = False
    exit: bool = False
    strong: bool = False
    weak: bool = False


class IndicatorValues(BaseModel):
    """Technical indicator values."""
    ema_fast: Optional[float] = None
    ema_slow: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    atr: Optional[float] = None
    atr_median: Optional[float] = None


class ExecutionPlan(BaseModel):
    """Trade execution plan from scheduler."""
    action: Literal["observe", "pending_only", "wait_rr", "open_or_scale"]
    riskPct: str = "0"


class TradeIdea(BaseModel):
    """AI-generated trade idea."""
    id: str
    timestamp: str
    symbol: str
    timeframe: str
    confidence: int
    action: str
    direction: Literal["long", "short"]
    entry_price: float
    stop_loss: float
    take_profit: float
    volume: float
    rr_ratio: float
    emnr_flags: EMNRFlags
    indicators: IndicatorValues
    execution_plan: ExecutionPlan
    status: Literal["pending_approval", "approved", "rejected", "executed", "cancelled"]
    notes: Optional[str] = None


class EvaluateRequest(BaseModel):
    """Request to evaluate a symbol."""
    timeframe: Literal["M1", "M5", "M15", "M30", "H1", "H4", "D1"] = "H1"
    force: bool = False


class EvaluateResponse(BaseModel):
    """Response from symbol evaluation."""
    trade_idea: Optional[TradeIdea] = None
    confidence: int
    action: str
    message: str


class AIStatusResponse(BaseModel):
    """AI engine status."""
    enabled: bool
    mode: Literal["semi-auto", "full-auto"]
    enabled_symbols: list[str]
    active_trade_ideas: int
    autonomy_loop_running: bool


class EnableAIRequest(BaseModel):
    """Request to enable AI for a symbol."""
    timeframe: Literal["M1", "M5", "M15", "M30", "H1", "H4", "D1"] = "H1"
    auto_execute: bool = False


class KillSwitchRequest(BaseModel):
    """Request to trigger kill switch."""
    reason: str = "Manual kill switch activation"

