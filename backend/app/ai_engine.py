"""AI Trading Decision Engine - uses local LLM for analysis and trade signals."""
import asyncio
import json
import logging
import os
import subprocess
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Path where the AI model is stored
MODEL_DIR = os.path.expanduser("~/.mt5bby/models")
MODEL_NAME = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)
MODEL_URL = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# llama.cpp server
LLAMA_SERVER_PORT = 8899
LLAMA_SERVER_URL = f"http://127.0.0.1:{LLAMA_SERVER_PORT}/completion"


class AIEngine:
    """Manages the local AI model for trading decisions."""

    def __init__(self):
        self._server_process: Optional[subprocess.Popen] = None
        self._ready = False
        self._last_decision: Optional[dict] = None
        self._last_decision_time: float = 0
        self._decision_cache_ttl: float = 5.0  # Cache decisions for 5 seconds

    @property
    def is_ready(self) -> bool:
        return self._ready

    async def check_and_start(self):
        """Check if AI model is available and start the server."""
        # Check if llama-server or llama.cpp is available
        llama_bin = self._find_llama_binary()
        if not llama_bin:
            logger.info("llama.cpp not found - AI features will use rule-based fallback")
            return False

        if not os.path.exists(MODEL_PATH):
            logger.info(f"AI model not found at {MODEL_PATH} - using rule-based fallback")
            return False

        # Start the server
        try:
            self._server_process = subprocess.Popen(
                [
                    llama_bin,
                    "-m", MODEL_PATH,
                    "--port", str(LLAMA_SERVER_PORT),
                    "-c", "2048",
                    "-ngl", "0",  # CPU only for compatibility
                    "--threads", "4",
                    "-b", "512",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait for server to start
            for _ in range(30):
                await asyncio.sleep(1)
                if await self._health_check():
                    self._ready = True
                    logger.info("AI model server started successfully")
                    return True
        except Exception as e:
            logger.warning(f"Failed to start AI server: {e}")

        return False

    def _find_llama_binary(self) -> Optional[str]:
        """Find llama.cpp server binary."""
        possible_paths = [
            os.path.expanduser("~/.mt5bby/llama-server"),
            "/usr/local/bin/llama-server",
            "/usr/bin/llama-server",
            os.path.expanduser("~/.mt5bby/llama.cpp/build/bin/llama-server"),
        ]
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        return None

    async def _health_check(self) -> bool:
        """Check if the llama server is responding."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://127.0.0.1:{LLAMA_SERVER_PORT}/health",
                    timeout=aiohttp.ClientTimeout(total=2),
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def _query_llm(self, prompt: str) -> Optional[str]:
        """Query the local LLM."""
        if not self._ready:
            return None
        try:
            import aiohttp
            payload = {
                "prompt": prompt,
                "n_predict": 512,
                "temperature": 0.3,
                "top_p": 0.9,
                "stop": ["</s>", "\n\n\n"],
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    LLAMA_SERVER_URL,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("content", "").strip()
        except Exception as e:
            logger.warning(f"LLM query failed: {e}")
        return None

    def generate_trade_decision(
        self,
        price: float,
        symbol: str,
        master_signal: dict,
        oscillator_summary: dict,
        ma_summary: dict,
        rsi_value: Optional[float] = None,
        macd_hist: Optional[float] = None,
        atr_value: Optional[float] = None,
        bb_data: Optional[dict] = None,
        market_structure: Optional[dict] = None,
        patterns: Optional[list] = None,
    ) -> dict:
        """Generate a comprehensive trading decision using rule-based analysis.

        This always works - no AI model needed. When AI is available,
        it enhances with commentary.
        """
        if price <= 0:
            return self._empty_decision(symbol)

        # Determine signal direction from master signal
        strength = master_signal.get("strength", 0)
        confidence = master_signal.get("confidence", 0)
        action = master_signal.get("action", "NEUTRAL")

        # Calculate ATR-based stops if ATR available
        if atr_value and atr_value > 0:
            sl_distance = atr_value * 1.5
            tp_distance = atr_value * 2.5
        else:
            # Fallback: percentage-based
            sl_distance = price * 0.005  # 0.5%
            tp_distance = price * 0.01   # 1.0%

        # Adjust based on Bollinger Bands position
        if bb_data:
            bb_upper = bb_data.get("upper", price)
            bb_lower = bb_data.get("lower", price)
            bb_mid = bb_data.get("middle", price)

            if price > bb_upper:
                # Overbought - favor sell
                strength = min(strength - 0.2, strength)
            elif price < bb_lower:
                # Oversold - favor buy
                strength = max(strength + 0.2, strength)

        # Determine direction
        if strength > 0.15:
            direction = "BUY"
            entry = price
            sl = round(entry - sl_distance, 2)
            tp = round(entry + tp_distance, 2)
        elif strength < -0.15:
            direction = "SELL"
            entry = price
            sl = round(entry + sl_distance, 2)
            tp = round(entry - tp_distance, 2)
        else:
            direction = "HOLD"
            entry = price
            sl = round(entry - sl_distance, 2)
            tp = round(entry + tp_distance, 2)

        # Calculate risk/reward ratio
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr_ratio = round(reward / risk, 2) if risk > 0 else 0

        # Simulated profit (1 lot)
        lot_size = 100  # 1 standard lot = 100 oz for gold
        sim_profit = round(reward * lot_size, 2)
        sim_loss = round(-risk * lot_size, 2)

        # Confidence adjustment based on indicator agreement
        osc_signal = oscillator_summary.get("signal", "Neutral")
        ma_signal = ma_summary.get("signal", "Neutral")

        signal_agreement = 0
        for sig in [osc_signal, ma_signal, action]:
            if "Buy" in sig or "BUY" in sig:
                signal_agreement += 1
            elif "Sell" in sig or "SELL" in sig:
                signal_agreement -= 1

        agreement_pct = abs(signal_agreement) / 3 * 100

        # Build reasoning
        reasons = []
        if rsi_value is not None:
            if rsi_value < 30:
                reasons.append(f"RSI oversold at {rsi_value:.1f}")
            elif rsi_value > 70:
                reasons.append(f"RSI overbought at {rsi_value:.1f}")
            else:
                reasons.append(f"RSI neutral at {rsi_value:.1f}")

        if macd_hist is not None:
            if macd_hist > 0:
                reasons.append("MACD histogram positive (bullish)")
            else:
                reasons.append("MACD histogram negative (bearish)")

        if bb_data:
            if price > bb_data.get("upper", price):
                reasons.append("Price above upper Bollinger Band")
            elif price < bb_data.get("lower", price):
                reasons.append("Price below lower Bollinger Band")

        if market_structure:
            trend = market_structure.get("trend", "unknown")
            reasons.append(f"Market structure: {trend}")

        if patterns:
            for p in patterns[:3]:
                reasons.append(f"Pattern: {p['name']} ({p['bias']})")

        reasons.append(f"Signal agreement: {agreement_pct:.0f}%")
        reasons.append(f"Master signal: {action} ({confidence:.0f}% confidence)")

        # Determine signal quality
        if abs(strength) > 0.5 and agreement_pct > 60:
            quality = "HIGH"
            quality_color = "#22c55e"
        elif abs(strength) > 0.15 and agreement_pct > 30:
            quality = "MEDIUM"
            quality_color = "#f59e0b"
        else:
            quality = "LOW"
            quality_color = "#ef4444"

        return {
            "direction": direction,
            "entry": round(entry, 2),
            "stop_loss": sl,
            "take_profit": tp,
            "risk_reward": rr_ratio,
            "sim_profit": sim_profit,
            "sim_loss": sim_loss,
            "confidence": round(min(100, confidence + agreement_pct) / 2, 1),
            "quality": quality,
            "quality_color": quality_color,
            "strength": round(strength, 4),
            "reasons": reasons,
            "timestamp": time.time(),
            "ai_powered": self._ready,
        }

    def _empty_decision(self, symbol: str) -> dict:
        """Return an empty decision when no data is available."""
        return {
            "direction": "WAIT",
            "entry": 0,
            "stop_loss": 0,
            "take_profit": 0,
            "risk_reward": 0,
            "sim_profit": 0,
            "sim_loss": 0,
            "confidence": 0,
            "quality": "NONE",
            "quality_color": "#6b7280",
            "strength": 0,
            "reasons": ["Waiting for market data..."],
            "timestamp": time.time(),
            "ai_powered": False,
        }

    async def get_ai_commentary(self, decision: dict, price_data: dict) -> str:
        """Get AI commentary on the trading decision."""
        if not self._ready:
            return self._generate_rule_commentary(decision, price_data)

        prompt = f"""<|system|>
You are a professional trading analyst. Give a brief 2-3 sentence analysis.</s>
<|user|>
{price_data.get('symbol', 'XAUUSD')} is at {price_data.get('price', 0)}.
Signal: {decision['direction']} | Confidence: {decision['confidence']}%
Entry: {decision['entry']} | TP: {decision['take_profit']} | SL: {decision['stop_loss']}
Key factors: {'; '.join(decision['reasons'][:4])}
Give a brief trading analysis.</s>
<|assistant|>
"""
        result = await self._query_llm(prompt)
        if result:
            return result
        return self._generate_rule_commentary(decision, price_data)

    def _generate_rule_commentary(self, decision: dict, price_data: dict) -> str:
        """Generate rule-based commentary when AI is not available."""
        direction = decision["direction"]
        symbol = price_data.get("symbol", "XAUUSD")
        price = price_data.get("price", 0)
        confidence = decision["confidence"]

        if direction == "BUY":
            return (
                f"{symbol} showing bullish momentum at {price}. "
                f"Technical indicators favor long entry with {confidence:.0f}% confidence. "
                f"Target {decision['take_profit']} with stop at {decision['stop_loss']}."
            )
        elif direction == "SELL":
            return (
                f"{symbol} showing bearish pressure at {price}. "
                f"Indicators suggest short opportunity with {confidence:.0f}% confidence. "
                f"Target {decision['take_profit']} with stop at {decision['stop_loss']}."
            )
        else:
            return (
                f"{symbol} consolidating around {price}. "
                f"Mixed signals - waiting for clearer directional bias. "
                f"Monitor for breakout above/below key levels."
            )

    def shutdown(self):
        """Stop the AI server."""
        if self._server_process:
            self._server_process.terminate()
            self._server_process = None
            self._ready = False
