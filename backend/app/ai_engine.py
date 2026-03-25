"""AI Trading Decision Engine - uses local LLM for analysis and trade signals."""
import asyncio
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
            trailing_stop = atr_value * 1.0
        else:
            # Fallback: percentage-based
            sl_distance = price * 0.005  # 0.5%
            tp_distance = price * 0.01   # 1.0%
            trailing_stop = price * 0.003

        # Bollinger Band position analysis
        bb_position = "middle"
        bb_squeeze = False
        if bb_data:
            bb_upper = bb_data.get("upper", price)
            bb_lower = bb_data.get("lower", price)
            bb_mid = bb_data.get("middle", price)
            bb_width = bb_data.get("width", 0)
            pct_b = bb_data.get("percent_b", 50)

            if price > bb_upper:
                bb_position = "above_upper"
                strength = min(strength - 0.2, strength)
            elif price < bb_lower:
                bb_position = "below_lower"
                strength = max(strength + 0.2, strength)
            elif pct_b > 80:
                bb_position = "near_upper"
            elif pct_b < 20:
                bb_position = "near_lower"

            if bb_width < 1.0:
                bb_squeeze = True

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

        # Detect momentum divergence
        momentum_diverging = False
        if rsi_value is not None and macd_hist is not None:
            if (rsi_value > 70 and macd_hist < 0) or (rsi_value < 30 and macd_hist > 0):
                momentum_diverging = True

        # Determine direction with more granular actions
        if strength > 0.5 and agreement_pct > 60:
            direction = "STRONG BUY"
            entry = price
            sl = round(entry - sl_distance, 2)
            tp = round(entry + tp_distance, 2)
        elif strength > 0.15:
            direction = "BUY"
            entry = price
            sl = round(entry - sl_distance, 2)
            tp = round(entry + tp_distance, 2)
        elif strength < -0.5 and agreement_pct > 60:
            direction = "STRONG SELL"
            entry = price
            sl = round(entry + sl_distance, 2)
            tp = round(entry - tp_distance, 2)
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

        # Override to EXIT if momentum is diverging against the position
        if momentum_diverging and abs(strength) < 0.3:
            direction = "EXIT"

        # Break-even zone detection
        break_even_zone = False
        if abs(strength) < 0.05 and agreement_pct < 40:
            break_even_zone = True
            if direction == "HOLD":
                direction = "BREAK EVEN"

        # Calculate risk/reward ratio
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr_ratio = round(reward / risk, 2) if risk > 0 else 0

        # Simulated profit (1 lot)
        lot_size = 100  # 1 standard lot = 100 oz for gold
        sim_profit = round(reward * lot_size, 2)
        sim_loss = round(-risk * lot_size, 2)

        # Build reasoning
        reasons = []

        # RSI analysis
        if rsi_value is not None:
            if rsi_value < 20:
                reasons.append(f"RSI deeply oversold at {rsi_value:.1f} - strong bounce expected")
            elif rsi_value < 30:
                reasons.append(f"RSI oversold at {rsi_value:.1f} - watch for reversal")
            elif rsi_value > 80:
                reasons.append(f"RSI deeply overbought at {rsi_value:.1f} - pullback likely")
            elif rsi_value > 70:
                reasons.append(f"RSI overbought at {rsi_value:.1f} - caution on longs")
            elif 45 <= rsi_value <= 55:
                reasons.append(f"RSI neutral at {rsi_value:.1f} - no momentum edge")
            elif rsi_value > 55:
                reasons.append(f"RSI bullish at {rsi_value:.1f} - momentum favors buyers")
            else:
                reasons.append(f"RSI bearish at {rsi_value:.1f} - momentum favors sellers")

        # MACD analysis
        if macd_hist is not None:
            if macd_hist > 0 and macd_hist > 0.5:
                reasons.append("MACD strongly bullish - upward momentum accelerating")
            elif macd_hist > 0:
                reasons.append("MACD histogram positive - mild bullish momentum")
            elif macd_hist < -0.5:
                reasons.append("MACD strongly bearish - downward momentum accelerating")
            else:
                reasons.append("MACD histogram negative - mild bearish pressure")

        # Divergence warning
        if momentum_diverging:
            reasons.append("WARNING: RSI/MACD divergence detected - trend weakening")

        # Bollinger Band analysis
        if bb_data:
            if bb_position == "above_upper":
                reasons.append("Price above upper BB - overbought, expect mean reversion")
            elif bb_position == "below_lower":
                reasons.append("Price below lower BB - oversold, expect bounce")
            elif bb_position == "near_upper":
                reasons.append("Price near upper BB - approaching resistance")
            elif bb_position == "near_lower":
                reasons.append("Price near lower BB - approaching support")
            if bb_squeeze:
                reasons.append("BB Squeeze detected - breakout imminent, wait for direction")

        # Market structure
        if market_structure:
            trend = market_structure.get("trend", "unknown")
            ms_strength = market_structure.get("strength", 0)
            hh = market_structure.get("higher_highs", 0)
            ll = market_structure.get("lower_lows", 0)
            if trend == "Uptrend":
                reasons.append(f"Market structure bullish ({hh} HH) - buy dips")
            elif trend == "Downtrend":
                reasons.append(f"Market structure bearish ({ll} LL) - sell rallies")
            else:
                reasons.append(f"Market ranging - trade boundaries, strength {ms_strength}%")

        # Pattern analysis
        if patterns:
            for p in patterns[:3]:
                p_strength = p.get('strength', 50)
                if p_strength >= 80:
                    reasons.append(f"STRONG pattern: {p['name']} ({p['bias']}) - high reliability")
                else:
                    reasons.append(f"Pattern: {p['name']} ({p['bias']})")

        reasons.append(f"Signal agreement: {agreement_pct:.0f}% across oscillators, MAs, master")
        reasons.append(f"Master signal: {action} ({confidence:.0f}% confidence)")

        # Determine signal quality
        if abs(strength) > 0.5 and agreement_pct > 60:
            quality = "HIGH"
            quality_color = "#22c55e"
        elif abs(strength) > 0.3 and agreement_pct > 40:
            quality = "GOOD"
            quality_color = "#84cc16"
        elif abs(strength) > 0.15 and agreement_pct > 30:
            quality = "MEDIUM"
            quality_color = "#f59e0b"
        elif abs(strength) > 0.05:
            quality = "LOW"
            quality_color = "#f97316"
        else:
            quality = "WAIT"
            quality_color = "#ef4444"

        # Build action advice
        if direction in ("BUY", "STRONG BUY"):
            action_advice = f"Enter LONG at {entry:.2f}. Set SL at {sl:.2f}, TP at {tp:.2f}. Trail stop by {trailing_stop:.2f} as price moves in your favor."
        elif direction in ("SELL", "STRONG SELL"):
            action_advice = f"Enter SHORT at {entry:.2f}. Set SL at {sl:.2f}, TP at {tp:.2f}. Trail stop by {trailing_stop:.2f} as price moves in your favor."
        elif direction == "EXIT":
            action_advice = "Close open positions. Momentum divergence signals trend exhaustion. Re-evaluate after consolidation."
        elif direction == "BREAK EVEN":
            action_advice = "Move stops to break-even. Mixed signals - protect capital. No new entries until direction clears."
        else:
            action_advice = "No clear edge. Stay flat or tighten stops on existing positions. Wait for stronger signal alignment."

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
            "action_advice": action_advice,
            "trailing_stop": round(trailing_stop, 2),
            "break_even_zone": break_even_zone,
            "momentum_divergence": momentum_diverging,
            "bb_position": bb_position,
            "bb_squeeze": bb_squeeze if bb_data else False,
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
            "action_advice": "Waiting for market data to initialize...",
            "trailing_stop": 0,
            "break_even_zone": False,
            "momentum_divergence": False,
            "bb_position": "unknown",
            "bb_squeeze": False,
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
        quality = decision.get("quality", "LOW")
        rr = decision.get("risk_reward", 0)
        trailing = decision.get("trailing_stop", 0)

        if direction in ("BUY", "STRONG BUY"):
            urgency = "STRONG " if direction == "STRONG BUY" else ""
            return (
                f"{urgency}BUY SIGNAL on {symbol} at {price:.2f}. "
                f"Entry: {decision['entry']:.2f} | TP: {decision['take_profit']:.2f} | SL: {decision['stop_loss']:.2f}. "
                f"Risk/Reward {rr}:1 with {confidence:.0f}% confidence ({quality} quality). "
                f"Trail your stop by {trailing:.2f} as price moves up. "
                f"Look to take partial profits at 50% of TP distance."
            )
        elif direction in ("SELL", "STRONG SELL"):
            urgency = "STRONG " if direction == "STRONG SELL" else ""
            return (
                f"{urgency}SELL SIGNAL on {symbol} at {price:.2f}. "
                f"Entry: {decision['entry']:.2f} | TP: {decision['take_profit']:.2f} | SL: {decision['stop_loss']:.2f}. "
                f"Risk/Reward {rr}:1 with {confidence:.0f}% confidence ({quality} quality). "
                f"Trail your stop by {trailing:.2f} as price drops. "
                f"Scale out at key support levels."
            )
        elif direction == "EXIT":
            return (
                f"EXIT SIGNAL on {symbol} at {price:.2f}. "
                f"Momentum divergence detected - the current trend is losing steam. "
                f"Close open positions and move to sidelines. "
                f"Wait for a fresh setup with better signal alignment before re-entering."
            )
        elif direction == "BREAK EVEN":
            return (
                f"BREAK-EVEN ZONE on {symbol} at {price:.2f}. "
                f"Signals are mixed and conflicting. If you have an open position, "
                f"move your stop loss to break-even to protect capital. "
                f"No new entries recommended until directional bias strengthens."
            )
        else:
            return (
                f"HOLD/WAIT on {symbol} at {price:.2f}. "
                f"No clear directional edge right now ({confidence:.0f}% confidence). "
                f"Stay flat or tighten stops on existing positions. "
                f"Key levels to watch: above {decision['take_profit']:.2f} for bullish, below {decision['stop_loss']:.2f} for bearish."
            )

    def shutdown(self):
        """Stop the AI server."""
        if self._server_process:
            self._server_process.terminate()
            self._server_process = None
            self._ready = False
