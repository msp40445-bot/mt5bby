"""Live price feed manager with WebSocket support and realistic simulation."""
import asyncio
import time
import math
import random
from collections import deque
from typing import Optional

import numpy as np


class PriceFeed:
    """Manages live price data with configurable update intervals."""

    def __init__(self, symbol: str = "XAUUSD", base_price: float = 4347.27):
        self.symbol = symbol
        self.base_price = base_price
        self.current_price = base_price
        self.bid = base_price - 0.15
        self.ask = base_price + 0.15
        self.open_price = base_price
        self.high = base_price + 12.0
        self.low = base_price - 8.0
        self.volume = 125000.0
        self.last_update = time.time()
        self.start_time = time.time()

        # Store price history for indicator calculations
        # Multiple timeframe candle stores
        self.tick_history: deque = deque(maxlen=10000)
        self.candles_1s: deque = deque(maxlen=3600)
        self.candles_5s: deque = deque(maxlen=2000)
        self.candles_10s: deque = deque(maxlen=1000)
        self.candles_30s: deque = deque(maxlen=500)
        self.candles_1m: deque = deque(maxlen=500)
        self.candles_5m: deque = deque(maxlen=300)
        self.candles_15m: deque = deque(maxlen=200)
        self.candles_1h: deque = deque(maxlen=200)

        # Current candle builders
        self._current_candles: dict = {}
        self._candle_start_times: dict = {}

        # Volatility and trend parameters
        self._trend = 0.0
        self._volatility = 0.8
        self._momentum = 0.0
        self._tick_count = 0

        # Initialize with historical data
        self._generate_historical_data()

    def _generate_historical_data(self):
        """Generate realistic historical candle data for indicator warm-up."""
        now = time.time()
        price = self.base_price - 50.0  # Start lower
        rng = np.random.default_rng(42)

        # Generate 500 x 1-minute candles (about 8 hours of data)
        for i in range(500):
            drift = rng.normal(0.1, 2.0)
            price += drift
            o = price
            h = price + abs(rng.normal(0, 3.0))
            l = price - abs(rng.normal(0, 3.0))
            c = price + rng.normal(0, 1.5)
            v = max(1000, rng.normal(15000, 5000))
            ts = now - (500 - i) * 60

            candle = {"open": o, "high": h, "low": l, "close": c, "volume": v, "timestamp": ts}
            self.candles_1m.append(candle)

            # Also populate 5m, 15m, 1h at appropriate intervals
            if i % 5 == 0:
                self.candles_5m.append(candle)
            if i % 15 == 0:
                self.candles_15m.append(candle)
            if i % 60 == 0:
                self.candles_1h.append(candle)

        # Generate more granular data for sub-minute timeframes
        for i in range(3600):
            drift = rng.normal(0.01, 0.3)
            price += drift
            o = price
            h = price + abs(rng.normal(0, 0.5))
            l = price - abs(rng.normal(0, 0.5))
            c = price + rng.normal(0, 0.2)
            v = max(100, rng.normal(500, 200))
            ts = now - (3600 - i)

            candle = {"open": o, "high": h, "low": l, "close": c, "volume": v, "timestamp": ts}
            self.candles_1s.append(candle)

            if i % 5 == 0:
                self.candles_5s.append(candle)
            if i % 10 == 0:
                self.candles_10s.append(candle)
            if i % 30 == 0:
                self.candles_30s.append(candle)

        self.current_price = price
        self.base_price = price
        self.bid = price - 0.15
        self.ask = price + 0.15

    def tick(self) -> dict:
        """Generate a new price tick with realistic market microstructure."""
        self._tick_count += 1
        now = time.time()
        elapsed = now - self.start_time

        # Market microstructure simulation
        # Trend changes slowly
        if self._tick_count % 50 == 0:
            self._trend = max(-0.5, min(0.5, self._trend + random.gauss(0, 0.1)))
        if self._tick_count % 200 == 0:
            self._volatility = max(0.3, min(2.0, self._volatility + random.gauss(0, 0.1)))

        # Momentum with mean reversion
        self._momentum = 0.95 * self._momentum + random.gauss(self._trend * 0.01, self._volatility * 0.05)

        # Add some realistic patterns
        # Sine wave component for natural oscillation
        wave = 0.3 * math.sin(elapsed * 0.01) + 0.15 * math.sin(elapsed * 0.03)

        # Price change
        change = self._momentum + wave * 0.1 + random.gauss(0, self._volatility * 0.15)
        self.current_price += change
        self.current_price = max(self.current_price, self.base_price * 0.95)
        self.current_price = min(self.current_price, self.base_price * 1.05)

        # Spread varies with volatility
        spread = max(0.10, 0.15 + abs(change) * 0.3)
        self.bid = self.current_price - spread / 2
        self.ask = self.current_price + spread / 2

        # Update high/low
        self.high = max(self.high, self.current_price)
        self.low = min(self.low, self.current_price)

        # Volume simulation
        self.volume += random.uniform(50, 500)

        total_change = self.current_price - self.open_price
        change_pct = (total_change / self.open_price) * 100

        tick_data = {
            "symbol": self.symbol,
            "price": round(self.current_price, 2),
            "bid": round(self.bid, 2),
            "ask": round(self.ask, 2),
            "high": round(self.high, 2),
            "low": round(self.low, 2),
            "open": round(self.open_price, 2),
            "change": round(total_change, 2),
            "change_pct": round(change_pct, 4),
            "volume": round(self.volume, 0),
            "timestamp": now,
        }

        self.tick_history.append(tick_data)
        self._update_candles(tick_data)

        self.last_update = now
        return tick_data

    def _update_candles(self, tick: dict):
        """Update all timeframe candles with the latest tick."""
        now = tick["timestamp"]
        price = tick["price"]
        volume = random.uniform(10, 100)

        timeframes = {
            "1s": (self.candles_1s, 1),
            "5s": (self.candles_5s, 5),
            "10s": (self.candles_10s, 10),
            "30s": (self.candles_30s, 30),
            "1m": (self.candles_1m, 60),
            "5m": (self.candles_5m, 300),
            "15m": (self.candles_15m, 900),
            "1h": (self.candles_1h, 3600),
        }

        for tf_name, (candle_store, interval) in timeframes.items():
            period_start = int(now // interval) * interval

            if tf_name not in self._candle_start_times or self._candle_start_times[tf_name] != period_start:
                # New candle
                self._candle_start_times[tf_name] = period_start
                self._current_candles[tf_name] = {
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": volume,
                    "timestamp": period_start,
                }
                candle_store.append(self._current_candles[tf_name])
            else:
                # Update current candle
                candle = self._current_candles.get(tf_name)
                if candle:
                    candle["high"] = max(candle["high"], price)
                    candle["low"] = min(candle["low"], price)
                    candle["close"] = price
                    candle["volume"] += volume

    def get_candles(self, timeframe: str) -> list[dict]:
        """Get candle data for a specific timeframe."""
        tf_map = {
            "1s": self.candles_1s,
            "5s": self.candles_5s,
            "10s": self.candles_10s,
            "30s": self.candles_30s,
            "1m": self.candles_1m,
            "5m": self.candles_5m,
            "15m": self.candles_15m,
            "1h": self.candles_1h,
        }
        store = tf_map.get(timeframe, self.candles_1m)
        return list(store)

    def get_closes(self, timeframe: str) -> np.ndarray:
        """Get close prices as numpy array for a timeframe."""
        candles = self.get_candles(timeframe)
        if not candles:
            return np.array([self.current_price])
        return np.array([c["close"] for c in candles])

    def get_highs(self, timeframe: str) -> np.ndarray:
        candles = self.get_candles(timeframe)
        if not candles:
            return np.array([self.current_price])
        return np.array([c["high"] for c in candles])

    def get_lows(self, timeframe: str) -> np.ndarray:
        candles = self.get_candles(timeframe)
        if not candles:
            return np.array([self.current_price])
        return np.array([c["low"] for c in candles])

    def get_volumes(self, timeframe: str) -> np.ndarray:
        candles = self.get_candles(timeframe)
        if not candles:
            return np.array([1000.0])
        return np.array([c["volume"] for c in candles])
