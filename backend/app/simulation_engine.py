"""Simulation/Backtest Trade Engine - manages one position at a time with full lifecycle."""
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Trade:
    """Represents a single simulated trade."""

    def __init__(self, direction: str, entry_price: float, stop_loss: float,
                 take_profit: float, signal_quality: str, confidence: float):
        self.id = int(time.time() * 1000)
        self.direction = direction  # BUY or SELL
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.signal_quality = signal_quality
        self.confidence = confidence
        self.open_time = time.time()
        self.close_time: Optional[float] = None
        self.close_price: Optional[float] = None
        self.close_reason: Optional[str] = None
        self.pnl: float = 0.0
        self.pnl_pct: float = 0.0
        self.max_favorable: float = 0.0
        self.max_adverse: float = 0.0
        self.break_even_hit = False
        self.trailing_stop: Optional[float] = None
        self.status = "OPEN"  # OPEN, CLOSED

    def update(self, current_price: float) -> Optional[str]:
        """Update trade with current price. Returns close reason if trade should close."""
        if self.status != "OPEN":
            return None

        if self.direction == "BUY":
            unrealized = current_price - self.entry_price
            self.max_favorable = max(self.max_favorable, unrealized)
            self.max_adverse = min(self.max_adverse, unrealized)

            # Check stop loss
            if current_price <= self.stop_loss:
                return self._close(current_price, "STOP_LOSS")

            # Check take profit
            if current_price >= self.take_profit:
                return self._close(current_price, "TAKE_PROFIT")

            # Break-even: if price moved 50% toward TP, move SL to entry
            tp_distance = self.take_profit - self.entry_price
            if unrealized >= tp_distance * 0.5 and not self.break_even_hit:
                self.break_even_hit = True
                self.stop_loss = self.entry_price + 0.5  # small buffer above entry
                self.trailing_stop = current_price - tp_distance * 0.3

            # Trailing stop
            if self.trailing_stop is not None:
                new_trail = current_price - (self.take_profit - self.entry_price) * 0.3
                self.trailing_stop = max(self.trailing_stop, new_trail)
                if current_price <= self.trailing_stop:
                    return self._close(current_price, "TRAILING_STOP")

        else:  # SELL
            unrealized = self.entry_price - current_price
            self.max_favorable = max(self.max_favorable, unrealized)
            self.max_adverse = min(self.max_adverse, unrealized)

            # Check stop loss
            if current_price >= self.stop_loss:
                return self._close(current_price, "STOP_LOSS")

            # Check take profit
            if current_price <= self.take_profit:
                return self._close(current_price, "TAKE_PROFIT")

            # Break-even
            tp_distance = self.entry_price - self.take_profit
            if unrealized >= tp_distance * 0.5 and not self.break_even_hit:
                self.break_even_hit = True
                self.stop_loss = self.entry_price - 0.5
                self.trailing_stop = current_price + tp_distance * 0.3

            # Trailing stop
            if self.trailing_stop is not None:
                new_trail = current_price + (self.entry_price - self.take_profit) * 0.3
                self.trailing_stop = min(self.trailing_stop, new_trail)
                if current_price >= self.trailing_stop:
                    return self._close(current_price, "TRAILING_STOP")

        return None

    def _close(self, price: float, reason: str) -> str:
        self.close_price = price
        self.close_time = time.time()
        self.close_reason = reason
        self.status = "CLOSED"
        if self.direction == "BUY":
            self.pnl = (price - self.entry_price) * 100  # 1 lot = 100 oz
        else:
            self.pnl = (self.entry_price - price) * 100
        self.pnl_pct = ((price - self.entry_price) / self.entry_price) * 100
        if self.direction == "SELL":
            self.pnl_pct = -self.pnl_pct
        return reason

    def to_dict(self, current_price: float = 0) -> dict:
        if self.status == "OPEN" and current_price > 0:
            if self.direction == "BUY":
                unrealized_pnl = (current_price - self.entry_price) * 100
            else:
                unrealized_pnl = (self.entry_price - current_price) * 100
            unrealized_pct = ((current_price - self.entry_price) / self.entry_price) * 100
            if self.direction == "SELL":
                unrealized_pct = -unrealized_pct
        else:
            unrealized_pnl = self.pnl
            unrealized_pct = self.pnl_pct

        duration = (self.close_time or time.time()) - self.open_time

        return {
            "id": self.id,
            "direction": self.direction,
            "entry_price": round(self.entry_price, 2),
            "stop_loss": round(self.stop_loss, 2),
            "take_profit": round(self.take_profit, 2),
            "close_price": round(self.close_price, 2) if self.close_price else None,
            "close_reason": self.close_reason,
            "status": self.status,
            "pnl": round(unrealized_pnl, 2),
            "pnl_pct": round(unrealized_pct, 4),
            "max_favorable": round(self.max_favorable, 2),
            "max_adverse": round(self.max_adverse, 2),
            "break_even_hit": self.break_even_hit,
            "trailing_stop": round(self.trailing_stop, 2) if self.trailing_stop else None,
            "signal_quality": self.signal_quality,
            "confidence": round(self.confidence, 1),
            "duration_seconds": round(duration, 0),
            "open_time": self.open_time,
            "close_time": self.close_time,
        }


class SimulationEngine:
    """Manages the simulation backtest system - one position at a time."""

    def __init__(self):
        self.current_trade: Optional[Trade] = None
        self.trade_history: list[Trade] = []
        self.total_pnl: float = 0.0
        self.win_count: int = 0
        self.loss_count: int = 0
        self.max_drawdown: float = 0.0
        self.peak_pnl: float = 0.0
        self._last_signal_time: float = 0
        self._signal_cooldown: float = 30.0  # minimum 30s between trades

    def process_signal(self, ai_decision: dict, current_price: float) -> Optional[dict]:
        """Process an AI decision signal and manage positions."""
        now = time.time()

        # Update current trade if exists
        if self.current_trade and self.current_trade.status == "OPEN":
            close_reason = self.current_trade.update(current_price)
            if close_reason:
                self._record_closed_trade()
                logger.info(f"Trade closed: {close_reason} at {current_price:.2f}, PnL: ${self.current_trade.pnl:.2f}")

        # Check if we should open a new trade
        direction = ai_decision.get("direction", "HOLD")
        quality = ai_decision.get("quality", "WAIT")
        confidence = ai_decision.get("confidence", 0)

        # Only open trades on strong signals with cooldown
        can_trade = (
            self.current_trade is None or self.current_trade.status == "CLOSED"
        ) and (now - self._last_signal_time > self._signal_cooldown)

        if can_trade and direction in ("BUY", "STRONG BUY", "SELL", "STRONG SELL") and quality in ("HIGH", "GOOD", "MEDIUM"):
            trade_dir = "BUY" if "BUY" in direction else "SELL"
            entry = current_price
            sl = ai_decision.get("stop_loss", 0)
            tp = ai_decision.get("take_profit", 0)

            if sl > 0 and tp > 0:
                self.current_trade = Trade(
                    direction=trade_dir,
                    entry_price=entry,
                    stop_loss=sl,
                    take_profit=tp,
                    signal_quality=quality,
                    confidence=confidence,
                )
                self._last_signal_time = now
                logger.info(f"New trade opened: {trade_dir} at {entry:.2f}, SL: {sl:.2f}, TP: {tp:.2f}")

        # Handle EXIT signal on open position
        if direction == "EXIT" and self.current_trade and self.current_trade.status == "OPEN":
            self.current_trade._close(current_price, "SIGNAL_EXIT")
            self._record_closed_trade()

        return self.get_state(current_price)

    def force_close(self, current_price: float) -> Optional[dict]:
        """Force close current position."""
        if self.current_trade and self.current_trade.status == "OPEN":
            self.current_trade._close(current_price, "MANUAL_CLOSE")
            self._record_closed_trade()
        return self.get_state(current_price)

    def _record_closed_trade(self):
        if self.current_trade and self.current_trade.status == "CLOSED":
            self.trade_history.append(self.current_trade)
            self.total_pnl += self.current_trade.pnl
            if self.current_trade.pnl >= 0:
                self.win_count += 1
            else:
                self.loss_count += 1
            self.peak_pnl = max(self.peak_pnl, self.total_pnl)
            drawdown = self.peak_pnl - self.total_pnl
            self.max_drawdown = max(self.max_drawdown, drawdown)

    def get_state(self, current_price: float = 0) -> dict:
        total_trades = self.win_count + self.loss_count
        win_rate = (self.win_count / total_trades * 100) if total_trades > 0 else 0
        avg_win = 0.0
        avg_loss = 0.0
        if self.win_count > 0:
            avg_win = sum(t.pnl for t in self.trade_history if t.pnl >= 0) / self.win_count
        if self.loss_count > 0:
            avg_loss = sum(t.pnl for t in self.trade_history if t.pnl < 0) / self.loss_count

        return {
            "current_trade": self.current_trade.to_dict(current_price) if self.current_trade else None,
            "history": [t.to_dict() for t in reversed(self.trade_history[-20:])],
            "stats": {
                "total_pnl": round(self.total_pnl, 2),
                "total_trades": total_trades,
                "win_count": self.win_count,
                "loss_count": self.loss_count,
                "win_rate": round(win_rate, 1),
                "max_drawdown": round(self.max_drawdown, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
            },
        }
