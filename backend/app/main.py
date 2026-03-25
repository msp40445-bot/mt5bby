"""MT5BBY Trading Analysis Platform - Backend API with WebSocket live feeds."""
import asyncio
import json
import logging
import time
import collections
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import aiohttp

from app.price_feed import PriceFeed
from app.tradingview_feed import TradingViewFeed
from app.signals import compute_full_analysis
from app.ai_engine import AIEngine
from app.simulation_engine import SimulationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MT5BBY Trading Platform", version="3.0.0")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global feeds
tv_feed = TradingViewFeed(symbol="XAUUSD")
fallback_feed = PriceFeed(symbol="XAUUSD", base_price=4474.00)
ai_engine = AIEngine()
sim_engine = SimulationEngine()

_scraped_price_cache: dict = {"price": 0.0, "timestamp": 0.0}
_log_buffer: collections.deque = collections.deque(maxlen=200)
_chat_history: list[dict] = []
connected_clients: set[WebSocket] = set()


class LogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        entry = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": self.format(record),
        }
        _log_buffer.append(entry)


_log_handler = LogHandler()
_log_handler.setLevel(logging.DEBUG)
_log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.getLogger().addHandler(_log_handler)


def get_active_feed():
    if tv_feed.is_connected:
        return tv_feed
    return fallback_feed


async def _fetch_real_gold_price() -> float:
    urls = [
        ("https://api.metals.live/v1/spot/gold", "gold_api"),
        ("https://data-asg.goldprice.org/dbXRates/USD", "goldprice_org"),
    ]
    for url, source in urls:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if source == "gold_api" and isinstance(data, list) and data:
                            price = float(data[0].get("price", 0))
                            if price > 0:
                                logger.info(f"Real gold from metals.live: ${price:.2f}")
                                return price
                        elif source == "goldprice_org" and isinstance(data, dict):
                            items = data.get("items", [])
                            if items:
                                price = float(items[0].get("xauPrice", 0))
                                if price > 0:
                                    logger.info(f"Real gold from goldprice.org: ${price:.2f}")
                                    return price
        except Exception as e:
            logger.debug(f"Price fetch from {source} failed: {e}")
    return 0.0


_watchlist_cache: dict = {"data": [], "timestamp": 0.0}


async def _fetch_watchlist_prices() -> list[dict]:
    now = time.time()
    if now - _watchlist_cache["timestamp"] < 30 and _watchlist_cache["data"]:
        return _watchlist_cache["data"]
    watchlist: list[dict] = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.metals.live/v1/spot", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data:
                        if item.get("metal") == "gold":
                            watchlist.append({"symbol": "GOLD", "price": float(item["price"]), "change": 0, "changePct": 0, "category": "COMMODITY"})
                        elif item.get("metal") == "silver":
                            watchlist.append({"symbol": "SILVER", "price": float(item["price"]), "change": 0, "changePct": 0, "category": "COMMODITY"})
    except Exception:
        pass
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    rates = data.get("rates", {})
                    if "EUR" in rates:
                        watchlist.append({"symbol": "EURUSD", "price": round(1 / rates["EUR"], 5), "change": 0, "changePct": 0, "category": "FOREX"})
                    if "GBP" in rates:
                        watchlist.append({"symbol": "GBPUSD", "price": round(1 / rates["GBP"], 5), "change": 0, "changePct": 0, "category": "FOREX"})
                    if "JPY" in rates:
                        watchlist.append({"symbol": "USDJPY", "price": round(rates["JPY"], 2), "change": 0, "changePct": 0, "category": "FOREX"})
    except Exception:
        pass
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    btc = data.get("bitcoin", {})
                    eth = data.get("ethereum", {})
                    if btc.get("usd"):
                        watchlist.append({"symbol": "BTCUSD", "price": btc["usd"], "change": 0, "changePct": round(btc.get("usd_24h_change", 0), 2), "category": "CRYPTO"})
                    if eth.get("usd"):
                        watchlist.append({"symbol": "ETHUSD", "price": eth["usd"], "change": 0, "changePct": round(eth.get("usd_24h_change", 0), 2), "category": "CRYPTO"})
    except Exception:
        pass
    if watchlist:
        _watchlist_cache["data"] = watchlist
        _watchlist_cache["timestamp"] = now
    return watchlist


@app.on_event("startup")
async def startup():
    real_price = await _fetch_real_gold_price()
    if real_price > 0:
        fallback_feed.recalibrate(real_price)
        _scraped_price_cache["price"] = real_price
        _scraped_price_cache["timestamp"] = time.time()
        logger.info(f"Calibrated to real gold: ${real_price:.2f}")
    logger.info("Starting TradingView live feed...")
    await tv_feed.connect()
    logger.info("Starting AI engine...")
    await ai_engine.check_and_start()


@app.on_event("shutdown")
async def shutdown():
    ai_engine.shutdown()


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/api/symbols")
async def get_symbols():
    return {"symbols": [
        {"name": "XAUUSD", "description": "Gold Spot / U.S. Dollar", "category": "COMMODITIES"},
        {"name": "SPX", "description": "S&P 500 Index", "category": "INDICES"},
        {"name": "NDQ", "description": "NASDAQ 100", "category": "INDICES"},
        {"name": "DJI", "description": "Dow Jones Industrial", "category": "INDICES"},
        {"name": "EURUSD", "description": "Euro / U.S. Dollar", "category": "FOREX"},
        {"name": "GBPUSD", "description": "British Pound / U.S. Dollar", "category": "FOREX"},
        {"name": "USDJPY", "description": "U.S. Dollar / Japanese Yen", "category": "FOREX"},
        {"name": "BTCUSD", "description": "Bitcoin / U.S. Dollar", "category": "CRYPTO"},
        {"name": "ETHUSD", "description": "Ethereum / U.S. Dollar", "category": "CRYPTO"},
    ]}


@app.get("/api/analysis")
async def get_analysis():
    feed = get_active_feed()
    return compute_full_analysis(feed)


@app.get("/api/analysis/{timeframe}")
async def get_timeframe_analysis(timeframe: str):
    from app.signals import compute_timeframe_signal
    feed = get_active_feed()
    return compute_timeframe_signal(feed, timeframe)


@app.get("/api/scraper/gold-price")
async def scraper_gold_price():
    now = time.time()
    feed = get_active_feed()
    tick = feed.tick()
    if not tv_feed.is_connected and (now - _scraped_price_cache["timestamp"]) > 60:
        real_price = await _fetch_real_gold_price()
        if real_price > 0:
            _scraped_price_cache["price"] = real_price
            _scraped_price_cache["timestamp"] = now
            drift = (real_price - fallback_feed.current_price) * 0.1
            fallback_feed.current_price += drift
            fallback_feed.base_price = fallback_feed.current_price
    return {"price": tick["price"], "bid": tick["bid"], "ask": tick["ask"], "high": tick["high"], "low": tick["low"], "change": tick["change"], "change_pct": tick["change_pct"], "source": "tradingview" if tv_feed.is_connected else "api_calibrated", "timestamp": tick["timestamp"]}


@app.get("/api/price")
async def get_price():
    feed = get_active_feed()
    return feed.tick()


@app.get("/api/candles/{timeframe}")
async def get_candles(timeframe: str, limit: int = 100):
    feed = get_active_feed()
    candles = feed.get_candles(timeframe)
    return {"timeframe": timeframe, "candles": candles[-limit:]}


@app.get("/api/ai/status")
async def ai_status():
    return {"ready": ai_engine.is_ready, "model": "TinyLlama-1.1B" if ai_engine.is_ready else "Rule-based (offline)"}


@app.get("/api/ai/decision")
async def get_ai_decision():
    feed = get_active_feed()
    analysis = compute_full_analysis(feed)
    decision = _build_ai_decision(analysis)
    commentary = await ai_engine.get_ai_commentary(decision, analysis["price"])
    decision["commentary"] = commentary
    return decision


@app.get("/api/feed/status")
async def feed_status():
    return {"source": "tradingview" if tv_feed.is_connected else "simulation", "connected": tv_feed.is_connected, "symbol": tv_feed.symbol, "tv_symbol": tv_feed.tv_symbol}


@app.get("/api/simulation/state")
async def simulation_state():
    feed = get_active_feed()
    return sim_engine.get_state(feed.tick()["price"])


@app.post("/api/simulation/close")
async def simulation_close():
    feed = get_active_feed()
    return sim_engine.force_close(feed.tick()["price"])


@app.get("/api/logs")
async def get_logs(limit: int = 50):
    return {"logs": list(_log_buffer)[-limit:]}


@app.get("/api/watchlist")
async def get_watchlist():
    return {"watchlist": await _fetch_watchlist_prices()}


@app.post("/api/ai/chat")
async def ai_chat(body: dict):
    user_message = body.get("message", "")
    if not user_message:
        return {"response": "Please provide a message."}
    feed = get_active_feed()
    analysis = compute_full_analysis(feed)
    tick = analysis["price"]
    master = analysis["master_signal"]
    sim_state = sim_engine.get_state(tick["price"])
    if ai_engine.is_ready:
        context = f"Price: {tick['price']:.2f}, Signal: {master['action']} ({master['confidence']:.0f}%)"
        trade_ctx = ""
        if sim_state["current_trade"]:
            t = sim_state["current_trade"]
            trade_ctx = f" Trade: {t['direction']} at {t['entry_price']}, PnL: ${t['pnl']:.2f}"
        prompt = f"<|system|>\nMT5BBY AI gold analyst. {context}{trade_ctx}</s>\n<|user|>\n{user_message}</s>\n<|assistant|>\n"
        result = await ai_engine._query_llm(prompt)
        response = result if result else _rule_chat(user_message, tick, master, analysis, sim_state)
    else:
        response = _rule_chat(user_message, tick, master, analysis, sim_state)
    _chat_history.append({"role": "user", "message": user_message, "timestamp": time.time()})
    _chat_history.append({"role": "assistant", "message": response, "timestamp": time.time()})
    return {"response": response, "context": {"price": tick["price"], "signal": master["action"]}}


def _rule_chat(message: str, tick: dict, master: dict, analysis: dict, sim_state: dict) -> str:
    ml = message.lower()
    p, s = tick["price"], tick["symbol"]
    if any(w in ml for w in ["price", "how much", "current", "what is"]):
        return f"{s} at ${p:.2f}. Range: ${tick['low']:.2f}-${tick['high']:.2f}. Change: {tick['change']:+.2f} ({tick['change_pct']:+.2f}%)."
    if any(w in ml for w in ["signal", "buy", "sell", "trade", "should i", "recommendation"]):
        osc, ma = analysis["oscillator_summary"], analysis["ma_summary"]
        return f"Signal: {master['action']} ({master['confidence']:.0f}%). Osc: Buy:{osc['buy']}/Sell:{osc['sell']}/N:{osc['neutral']}. MA: Buy:{ma['buy']}/Sell:{ma['sell']}."
    if any(w in ml for w in ["position", "pnl", "profit", "loss"]):
        if sim_state["current_trade"]:
            t = sim_state["current_trade"]
            return f"Open {t['direction']} at {t['entry_price']:.2f}. PnL: ${t['pnl']:.2f}. TP:{t['take_profit']:.2f} SL:{t['stop_loss']:.2f}."
        st = sim_state["stats"]
        return f"No position. {st['total_trades']} trades, WR:{st['win_rate']:.0f}%, PnL:${st['total_pnl']:.2f}."
    if any(w in ml for w in ["analysis", "technical", "indicator", "rsi", "macd"]):
        oscs = analysis.get("oscillators", [])
        txt = ", ".join([f"{o['name'].split('(')[0].strip()}:{o['value']:.1f}({o['action']})" for o in oscs[:5] if o.get('value') is not None])
        return f"{s} ${p:.2f}: {txt}. Signal: {master['action']}."
    if any(w in ml for w in ["help", "what can", "how do"]):
        return "Ask about: price, signals, positions, indicators, analysis."
    return f"{s} ${p:.2f}. Signal: {master['action']} ({master['confidence']:.0f}%)."


@app.get("/api/orderbook")
async def get_orderbook():
    feed = get_active_feed()
    tick = feed.tick()
    price, spread = tick["price"], tick["ask"] - tick["bid"]
    bids, asks, cb, ca = [], [], 0.0, 0.0
    for i in range(15):
        bp = round(price - spread / 2 - i * 0.1 - random.uniform(0, 0.05), 2)
        ap = round(price + spread / 2 + i * 0.1 + random.uniform(0, 0.05), 2)
        bv = round(random.uniform(1, 50) * (1 + random.expovariate(0.5)), 1)
        av = round(random.uniform(1, 50) * (1 + random.expovariate(0.5)), 1)
        cb += bv
        ca += av
        bids.append({"price": bp, "volume": bv, "total": round(cb, 1)})
        asks.append({"price": ap, "volume": av, "total": round(ca, 1)})
    return {"bids": bids, "asks": asks, "spread": round(spread, 2), "mid_price": round(price, 2)}


def _build_ai_decision(analysis: dict):
    rsi_value, macd_hist = None, None
    for osc in analysis.get("oscillators", []):
        if "RSI" in osc["name"]:
            rsi_value = osc["value"]
        if "MACD" in osc["name"]:
            macd_hist = osc["value"]
    return ai_engine.generate_trade_decision(
        price=analysis["price"]["price"], symbol=analysis["price"]["symbol"],
        master_signal=analysis["master_signal"], oscillator_summary=analysis["oscillator_summary"],
        ma_summary=analysis["ma_summary"], rsi_value=rsi_value, macd_hist=macd_hist,
        atr_value=analysis.get("advanced", {}).get("atr", {}).get("value"),
        bb_data=analysis.get("advanced", {}).get("bollinger_bands"),
        market_structure=analysis.get("advanced", {}).get("market_structure"),
        patterns=analysis.get("advanced", {}).get("patterns"),
    )


def _get_feed_source() -> str:
    if tv_feed.is_connected:
        return "tradingview"
    if _scraped_price_cache["price"] > 0:
        return "api_calibrated"
    return "simulation"


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        feed = get_active_feed()
        analysis = compute_full_analysis(feed)
        decision = _build_ai_decision(analysis)
        commentary = await ai_engine.get_ai_commentary(decision, analysis["price"])
        decision["commentary"] = commentary
        sim_state = sim_engine.process_signal(decision, analysis["price"]["price"])
        analysis["ai_decision"] = decision
        analysis["simulation"] = sim_state
        analysis["feed_source"] = _get_feed_source()
        analysis["backend_logs"] = list(_log_buffer)[-30:]
        await websocket.send_json({"type": "full_analysis", "data": analysis})

        tick_interval = 0.5
        decision_counter = 0
        log_counter = 0

        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=tick_interval)
                try:
                    client_msg = json.loads(msg)
                    if client_msg.get("type") == "set_interval":
                        tick_interval = max(0.1, min(5.0, client_msg.get("interval", 0.5)))
                    elif client_msg.get("type") == "chat":
                        chat_msg = client_msg.get("message", "")
                        if chat_msg:
                            feed = get_active_feed()
                            a = compute_full_analysis(feed)
                            ss = sim_engine.get_state(a["price"]["price"])
                            if ai_engine.is_ready:
                                prompt = f"<|system|>\nMT5BBY AI. Price:{a['price']['price']:.2f} Signal:{a['master_signal']['action']}</s>\n<|user|>\n{chat_msg}</s>\n<|assistant|>\n"
                                resp = await ai_engine._query_llm(prompt)
                                if not resp:
                                    resp = _rule_chat(chat_msg, a["price"], a["master_signal"], a, ss)
                            else:
                                resp = _rule_chat(chat_msg, a["price"], a["master_signal"], a, ss)
                            await websocket.send_json({"type": "chat_response", "data": {"response": resp}})
                    elif client_msg.get("type") == "force_close":
                        feed = get_active_feed()
                        result = sim_engine.force_close(feed.tick()["price"])
                        await websocket.send_json({"type": "simulation_update", "data": result})
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                pass

            feed = get_active_feed()
            analysis = compute_full_analysis(feed)
            decision_counter += 1
            if decision_counter >= 5:
                decision_counter = 0
                decision = _build_ai_decision(analysis)
                commentary = await ai_engine.get_ai_commentary(decision, analysis["price"])
                decision["commentary"] = commentary

            sim_state = sim_engine.process_signal(decision, analysis["price"]["price"])
            analysis["ai_decision"] = decision
            analysis["simulation"] = sim_state
            analysis["feed_source"] = _get_feed_source()
            log_counter += 1
            if log_counter >= 10:
                log_counter = 0
                analysis["backend_logs"] = list(_log_buffer)[-30:]

            await websocket.send_json({"type": "update", "data": {
                "price": analysis["price"], "oscillators": analysis["oscillators"],
                "moving_averages": analysis["moving_averages"], "pivots": analysis["pivots"],
                "oscillator_summary": analysis["oscillator_summary"], "ma_summary": analysis["ma_summary"],
                "overall_summary": analysis["overall_summary"], "timeframe_signals": analysis["timeframe_signals"],
                "master_signal": analysis["master_signal"], "advanced": analysis.get("advanced", {}),
                "ai_decision": analysis.get("ai_decision", {}), "simulation": analysis.get("simulation", {}),
                "feed_source": analysis.get("feed_source", "simulation"),
                "backend_logs": analysis.get("backend_logs", []), "timestamp": analysis["timestamp"],
            }})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)
