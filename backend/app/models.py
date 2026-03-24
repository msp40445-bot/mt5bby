"""Pydantic models for the trading platform."""
from pydantic import BaseModel
from typing import Optional


class PriceData(BaseModel):
    symbol: str
    price: float
    bid: float
    ask: float
    high: float
    low: float
    open: float
    change: float
    change_pct: float
    volume: float
    timestamp: float


class IndicatorValue(BaseModel):
    name: str
    value: Optional[float] = None
    action: str  # "Buy", "Sell", "Neutral"


class PivotLevel(BaseModel):
    name: str
    classic: Optional[float] = None
    fibonacci: Optional[float] = None
    camarilla: Optional[float] = None
    woodie: Optional[float] = None
    dm: Optional[float] = None


class GaugeSummary(BaseModel):
    sell: int = 0
    neutral: int = 0
    buy: int = 0
    signal: str = "Neutral"  # "Strong Sell", "Sell", "Neutral", "Buy", "Strong Buy"


class TimeframeSignal(BaseModel):
    timeframe: str  # "1s", "5s", "10s", "30s", "1m", "5m", "15m", "1h"
    oscillators: GaugeSummary
    moving_averages: GaugeSummary
    summary: GaugeSummary
    strength: float  # -1.0 to 1.0
    label: str  # "STRONG SELL" to "STRONG BUY"


class TechnicalAnalysis(BaseModel):
    symbol: str
    price: PriceData
    oscillators: list[IndicatorValue]
    moving_averages: list[IndicatorValue]
    pivots: list[PivotLevel]
    oscillator_summary: GaugeSummary
    ma_summary: GaugeSummary
    overall_summary: GaugeSummary
    timeframe_signals: list[TimeframeSignal]
    master_signal: dict  # Combined weighted signal
    timestamp: float
