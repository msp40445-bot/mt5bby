"""MT5BBY Trading Analysis Platform - Backend API with WebSocket live feeds."""
import asyncio
import json
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.price_feed import PriceFeed
from app.signals import compute_full_analysis

app = FastAPI(title="MT5BBY Trading Platform", version="1.0.0")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global price feed instance
price_feed = PriceFeed(symbol="XAUUSD", base_price=4347.27)

# Track connected WebSocket clients
connected_clients: set[WebSocket] = set()


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
    return compute_full_analysis(price_feed)


@app.get("/api/analysis/{timeframe}")
async def get_timeframe_analysis(timeframe: str):
    """Get analysis for a specific timeframe."""
    from app.signals import compute_timeframe_signal
    return compute_timeframe_signal(price_feed, timeframe)


@app.get("/api/price")
async def get_price():
    """Get current price data."""
    tick = price_feed.tick()
    return tick


@app.get("/api/candles/{timeframe}")
async def get_candles(timeframe: str, limit: int = 100):
    """Get candle data for a timeframe."""
    candles = price_feed.get_candles(timeframe)
    return {"timeframe": timeframe, "candles": candles[-limit:]}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live data streaming."""
    await websocket.accept()
    connected_clients.add(websocket)

    try:
        # Send initial full analysis
        analysis = compute_full_analysis(price_feed)
        await websocket.send_json({"type": "full_analysis", "data": analysis})

        # Start streaming
        tick_interval = 0.2  # 200ms = 5 ticks/second for smooth updates

        while True:
            # Check for client messages (e.g., config changes)
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=tick_interval)
                try:
                    client_msg = json.loads(msg)
                    if client_msg.get("type") == "set_interval":
                        tick_interval = max(0.1, min(5.0, client_msg.get("interval", 0.2)))
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                pass

            # Generate new tick and compute analysis
            analysis = compute_full_analysis(price_feed)

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
                    "timestamp": analysis["timestamp"],
                },
            })

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        connected_clients.discard(websocket)
