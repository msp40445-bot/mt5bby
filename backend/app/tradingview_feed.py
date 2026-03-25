"""TradingView real-time price feed via their WebSocket protocol."""
import asyncio
import json
import random
import string
import time
import logging
from typing import Optional

import aiohttp
import numpy as np

logger = logging.getLogger(__name__)


def _generate_session() -> str:
    """Generate a TradingView-style session ID."""
    chars = string.ascii_lowercase + string.digits
    return "qs_" + "".join(random.choices(chars, k=12))


def _prepend_header(msg: str) -> str:
    """Prepend TradingView message header."""
    return f"~m~{len(msg)}~m~{msg}"


def _create_message(func: str, params: list) -> str:
    """Create a TradingView protocol message."""
    payload = json.dumps({"m": func, "p": params})
    return _prepend_header(payload)


def _parse_messages(raw: str) -> list[dict]:
    """Parse TradingView WebSocket messages."""
    results = []
    i = 0
    while i < len(raw):
        if raw[i:].startswith("~m~"):
            i += 3
            end = raw.index("~m~", i)
            length = int(raw[i:end])
            i = end + 3
            payload = raw[i : i + length]
            i += length
            if payload.startswith("{") or payload.startswith("["):
                try:
                    results.append(json.loads(payload))
                except json.JSONDecodeError:
                    pass
            elif payload.startswith("~h~"):
                results.append({"heartbeat": payload})
        else:
            i += 1
    return results


class TradingViewFeed:
    """Connects to TradingView's WebSocket for real-time price data."""

    TV_WS_URL = "wss://data.tradingview.com/socket.io/websocket"
    TV_WS_URLS = [
        "wss://data.tradingview.com/socket.io/websocket",
        "wss://widgetdata.tradingview.com/socket.io/websocket",
        "wss://prodata.tradingview.com/socket.io/websocket",
    ]
    TV_HEADERS = {
        "Origin": "https://www.tradingview.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    # Map our symbols to TradingView symbols
    SYMBOL_MAP = {
        "XAUUSD": "PEPPERSTONE:XAUUSD",
        "EURUSD": "FX:EURUSD",
        "GBPUSD": "FX:GBPUSD",
        "USDJPY": "FX:USDJPY",
        "BTCUSD": "BITSTAMP:BTCUSD",
        "ETHUSD": "BITSTAMP:ETHUSD",
        "SPX": "SP:SPX",
        "NDQ": "NASDAQ:NDX",
        "DJI": "DJ:DJI",
    }

    def __init__(self, symbol: str = "XAUUSD"):
        self.symbol = symbol
        self.tv_symbol = self.SYMBOL_MAP.get(symbol, f"PEPPERSTONE:{symbol}")
        self.session_id = _generate_session()
        self.chart_session = "cs_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=12))

        # Current price data
        self.current_price: float = 0.0
        self.bid: float = 0.0
        self.ask: float = 0.0
        self.high: float = 0.0
        self.low: float = 0.0
        self.open_price: float = 0.0
        self.volume: float = 0.0
        self.change: float = 0.0
        self.change_pct: float = 0.0
        self.last_update: float = time.time()
        self._connected = False
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._task: Optional[asyncio.Task] = None

        # Candle storage for indicators
        from collections import deque

        self.candles_1m: deque = deque(maxlen=500)
        self.candles_5m: deque = deque(maxlen=300)
        self.candles_15m: deque = deque(maxlen=200)
        self.candles_1h: deque = deque(maxlen=200)
        self.candles_1s: deque = deque(maxlen=3600)
        self.candles_5s: deque = deque(maxlen=2000)
        self.candles_10s: deque = deque(maxlen=1000)
        self.candles_30s: deque = deque(maxlen=500)

        self.tick_history: deque = deque(maxlen=10000)
        self._current_candles: dict = {}
        self._candle_start_times: dict = {}
        self._tick_count = 0

    @property
    def is_connected(self) -> bool:
        return self._connected and self.current_price > 0

    async def connect(self):
        """Start the TradingView WebSocket connection."""
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run())

    async def _run(self):
        """Main WebSocket loop with auto-reconnect, tries multiple endpoints."""
        url_index = 0
        retry_delay = 3
        while True:
            try:
                ws_url = self.TV_WS_URLS[url_index % len(self.TV_WS_URLS)]
                logger.info(f"Trying TradingView WebSocket: {ws_url}")
                await self._connect_and_listen(ws_url)
                retry_delay = 3  # Reset on successful connection
            except Exception as e:
                logger.warning(f"TradingView feed error on {ws_url}: {e}")
                self._connected = False
                url_index += 1  # Try next URL on failure
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 30)  # Backoff up to 30s

    async def _connect_and_listen(self, ws_url: str = ""):
        """Connect to TradingView and listen for price updates."""
        if not ws_url:
            ws_url = self.TV_WS_URL
        self._session = aiohttp.ClientSession()
        try:
            self._ws = await self._session.ws_connect(
                ws_url,
                headers=self.TV_HEADERS,
                timeout=aiohttp.ClientWSTimeout(ws_close=10, ws_receive=30),
            )

            # Send auth and subscribe messages
            auth_msg = _create_message("set_auth_token", ["unauthorized_user_token"])
            await self._ws.send_str(auth_msg)

            # Create quote session
            qs_msg = _create_message("quote_create_session", [self.session_id])
            await self._ws.send_str(qs_msg)

            # Set fields we want
            fields = [
                "ch", "chp", "current_session", "description", "local_description",
                "language", "exchange", "fractional", "is_tradable", "lp", "lp_time",
                "minmov", "minmove2", "original_name", "pricescale", "pro_name",
                "short_name", "type", "update_mode", "volume", "ask", "bid",
                "fundamentals", "high_price", "low_price", "open_price",
                "prev_close_price", "rch", "rchp", "rtc", "rtc_time", "status",
                "basic_eps_net_income", "beta_1_year", "earnings_per_share_basic_ttm",
                "industry", "market_cap_basic", "sector", "volume",
            ]
            set_fields_msg = _create_message(
                "quote_set_fields", [self.session_id] + fields
            )
            await self._ws.send_str(set_fields_msg)

            # Add symbol
            add_symbol_msg = _create_message(
                "quote_add_symbols", [self.session_id, self.tv_symbol]
            )
            await self._ws.send_str(add_symbol_msg)

            # Also set up chart session for candle data
            cs_msg = _create_message("chart_create_session", [self.chart_session, ""])
            await self._ws.send_str(cs_msg)

            resolve_msg = _create_message(
                "resolve_symbol",
                [self.chart_session, "sds_sym_1", f'={{"symbol":"{self.tv_symbol}","adjustment":"splits"}}'],
            )
            await self._ws.send_str(resolve_msg)

            series_msg = _create_message(
                "create_series",
                [self.chart_session, "sds_1", "s1", "sds_sym_1", "1", 300, ""],
            )
            await self._ws.send_str(series_msg)

            self._connected = True
            logger.info(f"Connected to TradingView for {self.tv_symbol}")

            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    self._process_messages(msg.data)
                elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSED):
                    break

        except Exception as e:
            logger.warning(f"TradingView connection error: {e}")
        finally:
            self._connected = False
            if self._ws and not self._ws.closed:
                await self._ws.close()
            if self._session and not self._session.closed:
                await self._session.close()

    def _process_messages(self, raw: str):
        """Process raw TradingView WebSocket messages."""
        messages = _parse_messages(raw)
        for msg in messages:
            if isinstance(msg, dict):
                if "heartbeat" in msg:
                    # Respond to heartbeat
                    if self._ws and not self._ws.closed:
                        asyncio.ensure_future(
                            self._ws.send_str(_prepend_header(msg["heartbeat"]))
                        )
                    continue

                m = msg.get("m")
                if m == "qsd":
                    self._handle_quote_data(msg.get("p", []))
                elif m == "timescale_update":
                    self._handle_candle_data(msg.get("p", []))
                elif m == "du":
                    self._handle_candle_update(msg.get("p", []))

    def _handle_quote_data(self, params: list):
        """Handle real-time quote data from TradingView."""
        if len(params) < 2:
            return
        data = params[1]
        if not isinstance(data, dict):
            return
        values = data.get("v", {})
        if not values:
            return

        now = time.time()

        if "lp" in values and values["lp"] is not None:
            self.current_price = float(values["lp"])
        if "bid" in values and values["bid"] is not None:
            self.bid = float(values["bid"])
        else:
            self.bid = self.current_price - 0.15
        if "ask" in values and values["ask"] is not None:
            self.ask = float(values["ask"])
        else:
            self.ask = self.current_price + 0.15
        if "high_price" in values and values["high_price"] is not None:
            self.high = float(values["high_price"])
        if "low_price" in values and values["low_price"] is not None:
            self.low = float(values["low_price"])
        if "open_price" in values and values["open_price"] is not None:
            self.open_price = float(values["open_price"])
        if "volume" in values and values["volume"] is not None:
            self.volume = float(values["volume"])
        if "ch" in values and values["ch"] is not None:
            self.change = float(values["ch"])
        if "chp" in values and values["chp"] is not None:
            self.change_pct = float(values["chp"])

        self.last_update = now
        self._tick_count += 1

        if self.current_price > 0:
            tick_data = self._make_tick()
            self.tick_history.append(tick_data)
            self._update_candles(tick_data)

    def _handle_candle_data(self, params: list):
        """Handle historical candle data from TradingView."""
        if len(params) < 2:
            return
        data = params[1]
        if not isinstance(data, dict):
            return

        sds = data.get("sds_1", {})
        series = sds.get("s", [])

        for bar in series:
            vals = bar.get("v", [])
            if len(vals) >= 6:
                candle = {
                    "timestamp": vals[0],
                    "open": vals[1],
                    "high": vals[2],
                    "low": vals[3],
                    "close": vals[4],
                    "volume": vals[5] if len(vals) > 5 else 0,
                }
                self.candles_1m.append(candle)

    def _handle_candle_update(self, params: list):
        """Handle real-time candle updates."""
        if len(params) < 2:
            return
        data = params[1]
        if not isinstance(data, dict):
            return

        sds = data.get("sds_1", {})
        series = sds.get("s", [])

        for bar in series:
            vals = bar.get("v", [])
            if len(vals) >= 6:
                candle = {
                    "timestamp": vals[0],
                    "open": vals[1],
                    "high": vals[2],
                    "low": vals[3],
                    "close": vals[4],
                    "volume": vals[5] if len(vals) > 5 else 0,
                }
                # Update or append the latest candle
                if self.candles_1m and abs(self.candles_1m[-1]["timestamp"] - candle["timestamp"]) < 60:
                    self.candles_1m[-1] = candle
                else:
                    self.candles_1m.append(candle)

    def _make_tick(self) -> dict:
        """Create a tick data dict from current state."""
        return {
            "symbol": self.symbol,
            "price": round(self.current_price, 2),
            "bid": round(self.bid, 2),
            "ask": round(self.ask, 2),
            "high": round(self.high, 2),
            "low": round(self.low, 2),
            "open": round(self.open_price, 2),
            "change": round(self.change, 2),
            "change_pct": round(self.change_pct, 4),
            "volume": round(self.volume, 0),
            "timestamp": self.last_update,
            "source": "tradingview",
        }

    def tick(self) -> dict:
        """Get current price tick (compatible with PriceFeed interface)."""
        if self.current_price > 0:
            return self._make_tick()
        # Fallback if not connected
        return {
            "symbol": self.symbol,
            "price": 0,
            "bid": 0,
            "ask": 0,
            "high": 0,
            "low": 0,
            "open": 0,
            "change": 0,
            "change_pct": 0,
            "volume": 0,
            "timestamp": time.time(),
            "source": "offline",
        }

    def _update_candles(self, tick: dict):
        """Update all timeframe candles with the latest tick."""
        now = tick["timestamp"]
        price = tick["price"]
        volume = tick.get("volume", 0)

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
        candles = self.get_candles(timeframe)
        if not candles:
            return np.array([self.current_price]) if self.current_price > 0 else np.array([1.0])
        return np.array([c["close"] for c in candles])

    def get_highs(self, timeframe: str) -> np.ndarray:
        candles = self.get_candles(timeframe)
        if not candles:
            return np.array([self.current_price]) if self.current_price > 0 else np.array([1.0])
        return np.array([c["high"] for c in candles])

    def get_lows(self, timeframe: str) -> np.ndarray:
        candles = self.get_candles(timeframe)
        if not candles:
            return np.array([self.current_price]) if self.current_price > 0 else np.array([1.0])
        return np.array([c["low"] for c in candles])

    def get_volumes(self, timeframe: str) -> np.ndarray:
        candles = self.get_candles(timeframe)
        if not candles:
            return np.array([1000.0])
        return np.array([c["volume"] for c in candles])
