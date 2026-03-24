"""MT5BBY Trading Analysis Platform - Backend API with WebSocket live feeds."""
import asyncio
import json
import logging
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.price_feed import PriceFeed
from app.tradingview_feed import TradingViewFeed
from app.signals import compute_full_analysis
from app.ai_engine import AIEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MT5BBY Trading Platform", version="2.0.0")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global feeds - TradingView for real data, PriceFeed as fallback
tv_feed = TradingViewFeed(symbol="XAUUSD")
fallback_feed = PriceFeed(symbol="XAUUSD", base_price=3025.50)
ai_engine = AIEngine()

# Track connected WebSocket clients
connected_clients: set[WebSocket] = set()


def get_active_feed():
    """Get the currently active price feed (TradingView if connected, else fallback)."""
    if tv_feed.is_connected:
        return tv_feed
    return fallback_feed


@app.on_event("startup")
async def startup():
    """Start TradingView feed and AI engine on startup."""
    logger.info("Starting TradingView live feed...")
    await tv_feed.connect()
    logger.info("Starting AI engine...")
    await ai_engine.check_and_start()


@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown."""
    ai_engine.shutdown()


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/api/symbols")
async def get_symbols():
    """Get available trading symbols."""
    return {
        "symbols": [
            {"name": "XAUUSD", "description": "Gold Spot / U.S. Dollar", "category": "COMMODITIES"},
            {"name": "SPX", "description": "S&P 500 Index", "category": "INDICES"},
            {"name": "NDQ", "description": "NASDAQ 100", "category": "INDICES"},
            {"name": "DJI", "description": "Dow Jones Industrial", "category": "INDICES"},
            {"name": "EURUSD", "description": "Euro / U.S. Dollar", "category": "FOREX"},
            {"name": "GBPUSD", "description": "British Pound / U.S. Dollar", "category": "FOREX"},
            {"name": "USDJPY", "description": "U.S. Dollar / Japanese Yen", "category": "FOREX"},
            {"name": "BTCUSD", "description": "Bitcoin / U.S. Dollar", "category": "CRYPTO"},
            {"name": "ETHUSD", "description": "Ethereum / U.S. Dollar", "category": "CRYPTO"},
        ]
    }


@app.get("/api/analysis")
async def get_analysis():
    """Get full technical analysis snapshot."""
    feed = get_active_feed()
    return compute_full_analysis(feed)


@app.get("/api/analysis/{timeframe}")
async def get_timeframe_analysis(timeframe: str):
    """Get analysis for a specific timeframe."""
    from app.signals import compute_timeframe_signal
    feed = get_active_feed()
    return compute_timeframe_signal(feed, timeframe)


@app.get("/api/price")
async def get_price():
    """Get current price data."""
    feed = get_active_feed()
    tick = feed.tick()
    return tick


@app.get("/api/candles/{timeframe}")
async def get_candles(timeframe: str, limit: int = 100):
    """Get candle data for a timeframe."""
    feed = get_active_feed()
    candles = feed.get_candles(timeframe)
    return {"timeframe": timeframe, "candles": candles[-limit:]}


@app.get("/api/ai/status")
async def ai_status():
    """Get AI engine status."""
    return {
        "ready": ai_engine.is_ready,
        "model": "TinyLlama-1.1B" if ai_engine.is_ready else "Rule-based (offline)",
    }


@app.get("/api/ai/decision")
async def get_ai_decision():
    """Get AI trading decision."""
    feed = get_active_feed()
    analysis = compute_full_analysis(feed)

    rsi_value = None
    macd_hist = None
    for osc in analysis.get("oscillators", []):
        if "RSI" in osc["name"]:
            rsi_value = osc["value"]
        if "MACD" in osc["name"]:
            macd_hist = osc["value"]

    decision = ai_engine.generate_trade_decision(
        price=analysis["price"]["price"],
        symbol=analysis["price"]["symbol"],
        master_signal=analysis["master_signal"],
        oscillator_summary=analysis["oscillator_summary"],
        ma_summary=analysis["ma_summary"],
        rsi_value=rsi_value,
        macd_hist=macd_hist,
        atr_value=analysis.get("advanced", {}).get("atr", {}).get("value"),
        bb_data=analysis.get("advanced", {}).get("bollinger_bands"),
        market_structure=analysis.get("advanced", {}).get("market_structure"),
        patterns=analysis.get("advanced", {}).get("patterns"),
    )

    commentary = await ai_engine.get_ai_commentary(decision, analysis["price"])
    decision["commentary"] = commentary

    return decision


@app.get("/api/feed/status")
async def feed_status():
    """Get current feed status."""
    return {
        "source": "tradingview" if tv_feed.is_connected else "simulation",
        "connected": tv_feed.is_connected,
        "symbol": tv_feed.symbol,
        "tv_symbol": tv_feed.tv_symbol,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live data streaming."""
    await websocket.accept()
    connected_clients.add(websocket)

    try:
        feed = get_active_feed()

        # Send initial full analysis
        analysis = compute_full_analysis(feed)

        # Generate AI decision
        rsi_value = None
        macd_hist = None
        for osc in analysis.get("oscillators", []):
            if "RSI" in osc["name"]:
                rsi_value = osc["value"]
            if "MACD" in osc["name"]:
                macd_hist = osc["value"]

        decision = ai_engine.generate_trade_decision(
            price=analysis["price"]["price"],
            symbol=analysis["price"]["symbol"],
            master_signal=analysis["master_signal"],
            oscillator_summary=analysis["oscillator_summary"],
            ma_summary=analysis["ma_summary"],
            rsi_value=rsi_value,
            macd_hist=macd_hist,
            atr_value=analysis.get("advanced", {}).get("atr", {}).get("value"),
            bb_data=analysis.get("advanced", {}).get("bollinger_bands"),
            market_structure=analysis.get("advanced", {}).get("market_structure"),
            patterns=analysis.get("advanced", {}).get("patterns"),
        )
        commentary = await ai_engine.get_ai_commentary(decision, analysis["price"])
        decision["commentary"] = commentary

        analysis["ai_decision"] = decision
        analysis["feed_source"] = "tradingview" if tv_feed.is_connected else "simulation"

        await websocket.send_json({"type": "full_analysis", "data": analysis})

        # Start streaming
        tick_interval = 0.5
        decision_counter = 0

        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=tick_interval)
                try:
                    client_msg = json.loads(msg)
                    if client_msg.get("type") == "set_interval":
                        tick_interval = max(0.1, min(5.0, client_msg.get("interval", 0.5)))
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                pass

            feed = get_active_feed()
            analysis = compute_full_analysis(feed)

            # Update AI decision every 5 ticks
            decision_counter += 1
            if decision_counter >= 5:
                decision_counter = 0
                rsi_value = None
                macd_hist = None
                for osc in analysis.get("oscillators", []):
                    if "RSI" in osc["name"]:
                        rsi_value = osc["value"]
                    if "MACD" in osc["name"]:
                        macd_hist = osc["value"]

                decision = ai_engine.generate_trade_decision(
                    price=analysis["price"]["price"],
                    symbol=analysis["price"]["symbol"],
                    master_signal=analysis["master_signal"],
                    oscillator_summary=analysis["oscillator_summary"],
                    ma_summary=analysis["ma_summary"],
                    rsi_value=rsi_value,
                    macd_hist=macd_hist,
                    atr_value=analysis.get("advanced", {}).get("atr", {}).get("value"),
                    bb_data=analysis.get("advanced", {}).get("bollinger_bands"),
                    market_structure=analysis.get("advanced", {}).get("market_structure"),
                    patterns=analysis.get("advanced", {}).get("patterns"),
                )
                commentary = await ai_engine.get_ai_commentary(decision, analysis["price"])
                decision["commentary"] = commentary

            analysis["ai_decision"] = decision
            analysis["feed_source"] = "tradingview" if tv_feed.is_connected else "simulation"

            await websocket.send_json({
                "type": "update",
                "data": {
                    "price": analysis["price"],
                    "oscillators": analysis["oscillators"],
                    "moving_averages": analysis["moving_averages"],
                    "pivots": analysis["pivots"],
                    "oscillator_summary": analysis["oscillator_summary"],
                    "ma_summary": analysis["ma_summary"],
                    "overall_summary": analysis["overall_summary"],
                    "timeframe_signals": analysis["timeframe_signals"],
                    "master_signal": analysis["master_signal"],
                    "advanced": analysis.get("advanced", {}),
                    "ai_decision": analysis.get("ai_decision", {}),
                    "feed_source": analysis.get("feed_source", "simulation"),
                    "timestamp": analysis["timestamp"],
                },
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)
