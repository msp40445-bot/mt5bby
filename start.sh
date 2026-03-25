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
MODEL_DIR="$HOME/.mt5bby/models"
LLAMA_DIR="$HOME/.mt5bby"

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
echo "  ║   Live TradingView Data + AI Analysis    ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    # Stop llama server if running
    if [ -n "$LLAMA_PID" ]; then
        kill $LLAMA_PID 2>/dev/null || true
    fi
    wait $BACKEND_PID 2>/dev/null || true
    wait $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ── Setup AI Model (lightweight, works on 7GB RAM macOS) ─────
setup_ai() {
    echo -e "${YELLOW}[0/4]${NC} Setting up AI model (TinyLlama 1.1B - lightweight)..."
    mkdir -p "$MODEL_DIR"

    # Check if model already downloaded
    MODEL_FILE="$MODEL_DIR/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    if [ -f "$MODEL_FILE" ]; then
        echo -e "  ${GREEN}AI model already downloaded${NC}"
    else
        echo -e "  ${YELLOW}Downloading TinyLlama 1.1B (Q4_K_M ~670MB - fits 7GB RAM)...${NC}"
        echo -e "  ${CYAN}This is a one-time download. The model runs fully offline after this.${NC}"
        if command -v curl &> /dev/null; then
            curl -L --progress-bar \
                "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
                -o "$MODEL_FILE" || {
                echo -e "  ${RED}Download failed - AI will use rule-based analysis (still works!)${NC}"
            }
        else
            echo -e "  ${RED}curl not found - AI will use rule-based analysis${NC}"
        fi
    fi

    # Check for llama.cpp server
    LLAMA_BIN=""
    if [ -f "$LLAMA_DIR/llama-server" ]; then
        LLAMA_BIN="$LLAMA_DIR/llama-server"
    elif command -v llama-server &> /dev/null; then
        LLAMA_BIN="$(command -v llama-server)"
    fi

    if [ -z "$LLAMA_BIN" ] && [ -f "$MODEL_FILE" ]; then
        echo -e "  ${YELLOW}llama.cpp server not found. Installing...${NC}"
        # Try to build llama.cpp from source
        if command -v cmake &> /dev/null && command -v make &> /dev/null; then
            LLAMA_BUILD_DIR="$LLAMA_DIR/llama.cpp"
            if [ ! -d "$LLAMA_BUILD_DIR" ]; then
                git clone --depth 1 https://github.com/ggerganov/llama.cpp.git "$LLAMA_BUILD_DIR" 2>/dev/null || true
            fi
            if [ -d "$LLAMA_BUILD_DIR" ]; then
                cd "$LLAMA_BUILD_DIR"
                mkdir -p build && cd build
                cmake .. -DLLAMA_BUILD_SERVER=ON 2>/dev/null && make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2) llama-server 2>/dev/null || true
                if [ -f "bin/llama-server" ]; then
                    cp bin/llama-server "$LLAMA_DIR/llama-server"
                    LLAMA_BIN="$LLAMA_DIR/llama-server"
                    echo -e "  ${GREEN}llama.cpp server built successfully${NC}"
                fi
                cd "$SCRIPT_DIR"
            fi
        fi
        if [ -z "$LLAMA_BIN" ]; then
            echo -e "  ${YELLOW}Could not install llama.cpp - AI will use rule-based analysis${NC}"
            echo -e "  ${CYAN}To enable full AI: brew install llama.cpp (macOS) or build from source${NC}"
        fi
    fi

    # Start llama server if available
    if [ -n "$LLAMA_BIN" ] && [ -f "$MODEL_FILE" ]; then
        echo -e "  ${YELLOW}Starting AI inference server...${NC}"
        "$LLAMA_BIN" \
            -m "$MODEL_FILE" \
            --port 8899 \
            -c 2048 \
            -ngl 0 \
            --threads 4 \
            -b 512 \
            > /dev/null 2>&1 &
        LLAMA_PID=$!
        # Quick check
        sleep 2
        if kill -0 $LLAMA_PID 2>/dev/null; then
            echo -e "  ${GREEN}AI server running (PID: $LLAMA_PID)${NC}"
        else
            echo -e "  ${YELLOW}AI server failed to start - using rule-based analysis${NC}"
            LLAMA_PID=""
        fi
    else
        echo -e "  ${CYAN}AI running in rule-based mode (no GPU/LLM required)${NC}"
        LLAMA_PID=""
    fi
}

# Run AI setup (non-blocking - continues even if AI setup fails)
setup_ai || true

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
echo -e "  ${CYAN}AI Status:${NC} http://localhost:8000/api/ai/status"
if [ -n "$LLAMA_PID" ]; then
    echo -e "  ${CYAN}AI Model:${NC}  TinyLlama 1.1B (local, offline)"
else
    echo -e "  ${CYAN}AI Mode:${NC}   Rule-based analysis (no LLM needed)"
fi
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running
wait
