# MT5BBY Trading Analysis Platform

A full-stack real-time trading analysis platform with live price data, technical indicators, and multi-timeframe signal generation.

## Features

- **Live Price Feed** - WebSocket-powered real-time price streaming with bid/ask, high/low
- **11 Oscillators** - RSI, Stochastic, CCI, ADX, Awesome Oscillator, Momentum, MACD, Stochastic RSI, Williams %R, Bull Bear Power, Ultimate Oscillator
- **15 Moving Averages** - EMA/SMA (10-200), Ichimoku, VWMA, Hull MA
- **5 Pivot Systems** - Classic, Fibonacci, Camarilla, Woodie, DM
- **8 Timeframes** - 1s, 5s, 10s, 30s, 1m, 5m, 15m, 1h
- **Master Signal** - Weighted aggregation across all timeframes with confidence score
- **TradingView-style UI** - Gauge meters, indicator tables, signal strength bars

## Quick Start

```bash
./start.sh
```

This single command:
1. Installs all dependencies (backend + frontend)
2. Starts the FastAPI backend server (port 8000)
3. Starts the Vite dev server (port 5173)
4. Opens the dashboard at http://localhost:5173

## Architecture

```
mt5bby/
├── backend/           # FastAPI + WebSocket server
│   └── app/
│       ├── main.py           # API endpoints & WebSocket
│       ├── price_feed.py     # Price data engine
│       ├── indicators.py     # Technical indicators (26 total)
│       └── signals.py        # Signal aggregation engine
├── frontend/          # React + TypeScript + Tailwind
│   └── src/
│       ├── App.tsx           # Main dashboard layout
│       ├── components/       # UI components
│       │   ├── Gauge.tsx          # Semicircle gauge meters
│       │   ├── IndicatorTable.tsx # Oscillators/MA tables
│       │   ├── PivotTable.tsx     # Pivot points table
│       │   ├── SignalPanel.tsx    # Multi-TF signal panel
│       │   ├── PriceTicker.tsx    # Live price display
│       │   └── Watchlist.tsx      # Market watchlist
│       └── hooks/
│           └── useWebSocket.ts   # WebSocket connection hook
├── start.sh           # Single command launcher
└── .github/workflows/ # CI/CD pipeline
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Health check |
| `/api/price` | GET | Current price data |
| `/api/analysis` | GET | Full technical analysis |
| `/api/analysis/{tf}` | GET | Timeframe-specific analysis |
| `/api/candles/{tf}` | GET | OHLCV candle data |
| `/api/symbols` | GET | Available symbols |
| `/ws` | WS | Live data WebSocket stream |

## Tech Stack

- **Backend**: Python 3.12, FastAPI, WebSocket, NumPy
- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **CI/CD**: GitHub Actions
