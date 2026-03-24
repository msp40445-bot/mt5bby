#!/usr/bin/env bash
set -e

# ============================================================
# MT5BBY Trading Analysis Platform - Single Command Launcher
# ============================================================
# Usage: ./start.sh
# This starts both the backend API server and the frontend dev server.
# Backend: http://localhost:8000 (FastAPI + WebSocket)
# Frontend: http://localhost:5173 (Vite + React)
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   MT5BBY Trading Analysis Platform       ║"
echo "  ║   Live Price Data & Technical Signals     ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
    wait $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ── Install dependencies ──────────────────────────────────────
echo -e "${YELLOW}[1/4]${NC} Installing backend dependencies..."
cd "$BACKEND_DIR"
if command -v poetry &> /dev/null; then
    poetry install --no-interaction --quiet 2>/dev/null || poetry install --no-interaction
else
    echo -e "${RED}Error: Poetry not found. Install it: curl -sSL https://install.python-poetry.org | python3 -${NC}"
    exit 1
fi

echo -e "${YELLOW}[2/4]${NC} Installing frontend dependencies..."
cd "$FRONTEND_DIR"
npm install --silent 2>/dev/null || npm install

# ── Start backend ─────────────────────────────────────────────
echo -e "${YELLOW}[3/4]${NC} Starting backend server..."
cd "$BACKEND_DIR"
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
echo -ne "  Waiting for backend"
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        echo -e " ${GREEN}ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# ── Start frontend ────────────────────────────────────────────
echo -e "${YELLOW}[4/4]${NC} Starting frontend dev server..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

sleep 2

echo ""
echo -e "${GREEN}${BOLD}All systems online!${NC}"
echo -e "  ${CYAN}Frontend:${NC}  http://localhost:5173"
echo -e "  ${CYAN}Backend:${NC}   http://localhost:8000"
echo -e "  ${CYAN}WebSocket:${NC} ws://localhost:8000/ws"
echo -e "  ${CYAN}API Docs:${NC}  http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running
wait
