"""Advanced technical analysis - Bollinger Bands, ATR, OBV, VWAP, patterns, market structure."""
import numpy as np
from typing import Optional


# ============================================================
# BOLLINGER BANDS
# ============================================================

def bollinger_bands(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Optional[dict]:
    """Calculate Bollinger Bands."""
    if len(closes) < period:
        return None
    sma_val = float(np.mean(closes[-period:]))
    std = float(np.std(closes[-period:]))
    upper = sma_val + std_dev * std
    lower = sma_val - std_dev * std
    width = (upper - lower) / sma_val * 100 if sma_val > 0 else 0
    pct_b = (float(closes[-1]) - lower) / (upper - lower) * 100 if (upper - lower) > 0 else 50

    return {
        "upper": round(upper, 2),
        "middle": round(sma_val, 2),
        "lower": round(lower, 2),
        "width": round(width, 4),
        "percent_b": round(pct_b, 2),
    }


# ============================================================
# ATR - AVERAGE TRUE RANGE
# ============================================================

def atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Optional[float]:
    """Calculate Average True Range."""
    if len(closes) < period + 1:
        return None
    tr_values = []
    for i in range(1, len(closes)):
        h = float(highs[i])
        l = float(lows[i])
        pc = float(closes[i - 1])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_values.append(tr)
    if len(tr_values) < period:
        return None
    return float(np.mean(tr_values[-period:]))


# ============================================================
# OBV - ON BALANCE VOLUME
# ============================================================

def obv(closes: np.ndarray, volumes: np.ndarray) -> Optional[dict]:
    """Calculate On Balance Volume and its trend."""
    if len(closes) < 2 or len(volumes) < 2:
        return None
    n = min(len(closes), len(volumes))
    obv_val = 0.0
    obv_values = [0.0]
    for i in range(1, n):
        if closes[i] > closes[i - 1]:
            obv_val += volumes[i]
        elif closes[i] < closes[i - 1]:
            obv_val -= volumes[i]
        obv_values.append(obv_val)

    # OBV trend (last 10 periods)
    if len(obv_values) >= 10:
        recent = obv_values[-10:]
        if recent[-1] > recent[0]:
            trend = "Rising"
        elif recent[-1] < recent[0]:
            trend = "Falling"
        else:
            trend = "Flat"
    else:
        trend = "N/A"

    return {
        "value": round(obv_val, 0),
        "trend": trend,
    }


# ============================================================
# VWAP - VOLUME WEIGHTED AVERAGE PRICE
# ============================================================

def vwap(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray) -> Optional[dict]:
    """Calculate VWAP."""
    n = min(len(highs), len(lows), len(closes), len(volumes))
    if n < 1:
        return None
    tp = (highs[:n] + lows[:n] + closes[:n]) / 3.0
    cumulative_tp_vol = np.cumsum(tp * volumes[:n])
    cumulative_vol = np.cumsum(volumes[:n])

    if cumulative_vol[-1] == 0:
        return None

    vwap_val = float(cumulative_tp_vol[-1] / cumulative_vol[-1])
    price = float(closes[-1])
    deviation = price - vwap_val
    deviation_pct = (deviation / vwap_val * 100) if vwap_val > 0 else 0

    return {
        "value": round(vwap_val, 2),
        "deviation": round(deviation, 2),
        "deviation_pct": round(deviation_pct, 4),
        "signal": "Buy" if price > vwap_val else "Sell" if price < vwap_val else "Neutral",
    }


# ============================================================
# FIBONACCI RETRACEMENT
# ============================================================

def fibonacci_retracement(highs: np.ndarray, lows: np.ndarray, lookback: int = 100) -> Optional[dict]:
    """Calculate Fibonacci retracement levels from recent swing high/low."""
    if len(highs) < lookback or len(lows) < lookback:
        lookback = min(len(highs), len(lows))
    if lookback < 10:
        return None

    swing_high = float(np.max(highs[-lookback:]))
    swing_low = float(np.min(lows[-lookback:]))
    diff = swing_high - swing_low

    if diff <= 0:
        return None

    levels = {
        "0.0": round(swing_high, 2),
        "0.236": round(swing_high - 0.236 * diff, 2),
        "0.382": round(swing_high - 0.382 * diff, 2),
        "0.5": round(swing_high - 0.5 * diff, 2),
        "0.618": round(swing_high - 0.618 * diff, 2),
        "0.786": round(swing_high - 0.786 * diff, 2),
        "1.0": round(swing_low, 2),
    }

    return {
        "swing_high": round(swing_high, 2),
        "swing_low": round(swing_low, 2),
        "levels": levels,
    }


# ============================================================
# MARKET STRUCTURE
# ============================================================

def detect_market_structure(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, lookback: int = 50) -> dict:
    """Detect market structure - Higher Highs, Higher Lows, etc."""
    n = min(len(highs), len(lows), len(closes), lookback)
    if n < 10:
        return {"trend": "Unknown", "swings": [], "strength": 0}

    h = highs[-n:]
    l = lows[-n:]

    # Find swing points using a simple 5-bar pivot
    swing_highs = []
    swing_lows = []
    pivot_len = 3

    for i in range(pivot_len, n - pivot_len):
        if all(h[i] >= h[i - j] for j in range(1, pivot_len + 1)) and all(h[i] >= h[i + j] for j in range(1, pivot_len + 1)):
            swing_highs.append({"index": i, "price": float(h[i])})
        if all(l[i] <= l[i - j] for j in range(1, pivot_len + 1)) and all(l[i] <= l[i + j] for j in range(1, pivot_len + 1)):
            swing_lows.append({"index": i, "price": float(l[i])})

    # Determine trend from swing points
    hh_count = 0
    ll_count = 0
    hl_count = 0
    lh_count = 0

    for i in range(1, len(swing_highs)):
        if swing_highs[i]["price"] > swing_highs[i - 1]["price"]:
            hh_count += 1
        else:
            lh_count += 1

    for i in range(1, len(swing_lows)):
        if swing_lows[i]["price"] > swing_lows[i - 1]["price"]:
            hl_count += 1
        else:
            ll_count += 1

    # Classify trend
    if hh_count > lh_count and hl_count > ll_count:
        trend = "Uptrend"
        strength = min(100, (hh_count + hl_count) * 20)
    elif lh_count > hh_count and ll_count > hl_count:
        trend = "Downtrend"
        strength = min(100, (lh_count + ll_count) * 20)
    else:
        trend = "Ranging"
        strength = 30

    return {
        "trend": trend,
        "higher_highs": hh_count,
        "lower_highs": lh_count,
        "higher_lows": hl_count,
        "lower_lows": ll_count,
        "swing_highs": len(swing_highs),
        "swing_lows": len(swing_lows),
        "strength": strength,
    }


# ============================================================
# CANDLESTICK PATTERN RECOGNITION
# ============================================================

def detect_patterns(opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> list[dict]:
    """Detect candlestick patterns in the recent data."""
    patterns = []
    n = len(closes)
    if n < 3:
        return patterns

    # Helper
    def body(i: int) -> float:
        return abs(float(closes[i]) - float(opens[i]))

    def upper_shadow(i: int) -> float:
        return float(highs[i]) - max(float(opens[i]), float(closes[i]))

    def lower_shadow(i: int) -> float:
        return min(float(opens[i]), float(closes[i])) - float(lows[i])

    def is_bullish(i: int) -> bool:
        return float(closes[i]) > float(opens[i])

    def is_bearish(i: int) -> bool:
        return float(closes[i]) < float(opens[i])

    i = n - 1  # Latest candle

    b = body(i)
    us = upper_shadow(i)
    ls = lower_shadow(i)
    avg_body = float(np.mean([body(j) for j in range(max(0, i - 10), i)])) if i > 0 else b

    if avg_body == 0:
        avg_body = 0.01

    # Doji
    if b < avg_body * 0.1:
        patterns.append({"name": "Doji", "bias": "Neutral", "strength": 50})

    # Hammer (bullish)
    if ls > b * 2 and us < b * 0.3 and b > 0:
        patterns.append({"name": "Hammer", "bias": "Bullish", "strength": 70})

    # Shooting Star (bearish)
    if us > b * 2 and ls < b * 0.3 and b > 0:
        patterns.append({"name": "Shooting Star", "bias": "Bearish", "strength": 70})

    # Engulfing patterns (need 2 candles)
    if i >= 1:
        prev_b = body(i - 1)
        # Bullish Engulfing
        if is_bearish(i - 1) and is_bullish(i) and b > prev_b * 1.3:
            if float(closes[i]) > float(opens[i - 1]) and float(opens[i]) < float(closes[i - 1]):
                patterns.append({"name": "Bullish Engulfing", "bias": "Bullish", "strength": 80})

        # Bearish Engulfing
        if is_bullish(i - 1) and is_bearish(i) and b > prev_b * 1.3:
            if float(closes[i]) < float(opens[i - 1]) and float(opens[i]) > float(closes[i - 1]):
                patterns.append({"name": "Bearish Engulfing", "bias": "Bearish", "strength": 80})

    # Morning/Evening Star (need 3 candles)
    if i >= 2:
        # Morning Star
        if is_bearish(i - 2) and body(i - 1) < avg_body * 0.3 and is_bullish(i):
            if float(closes[i]) > (float(opens[i - 2]) + float(closes[i - 2])) / 2:
                patterns.append({"name": "Morning Star", "bias": "Bullish", "strength": 85})

        # Evening Star
        if is_bullish(i - 2) and body(i - 1) < avg_body * 0.3 and is_bearish(i):
            if float(closes[i]) < (float(opens[i - 2]) + float(closes[i - 2])) / 2:
                patterns.append({"name": "Evening Star", "bias": "Bearish", "strength": 85})

    # Three White Soldiers
    if i >= 2:
        if all(is_bullish(i - j) for j in range(3)):
            if float(closes[i]) > float(closes[i - 1]) > float(closes[i - 2]):
                if all(body(i - j) > avg_body * 0.5 for j in range(3)):
                    patterns.append({"name": "Three White Soldiers", "bias": "Bullish", "strength": 85})

    # Three Black Crows
    if i >= 2:
        if all(is_bearish(i - j) for j in range(3)):
            if float(closes[i]) < float(closes[i - 1]) < float(closes[i - 2]):
                if all(body(i - j) > avg_body * 0.5 for j in range(3)):
                    patterns.append({"name": "Three Black Crows", "bias": "Bearish", "strength": 85})

    # Marubozu
    if b > avg_body * 1.5 and us < b * 0.05 and ls < b * 0.05:
        if is_bullish(i):
            patterns.append({"name": "Bullish Marubozu", "bias": "Bullish", "strength": 75})
        else:
            patterns.append({"name": "Bearish Marubozu", "bias": "Bearish", "strength": 75})

    # Spinning Top
    if b < avg_body * 0.5 and (us + ls) > b * 2 and b > avg_body * 0.1:
        patterns.append({"name": "Spinning Top", "bias": "Neutral", "strength": 30})

    return patterns


# ============================================================
# VOLUME PROFILE (simplified)
# ============================================================

def volume_profile(closes: np.ndarray, volumes: np.ndarray, bins: int = 10) -> Optional[dict]:
    """Calculate a simplified volume profile."""
    n = min(len(closes), len(volumes))
    if n < 10:
        return None

    c = closes[-n:]
    v = volumes[-n:]

    price_min = float(np.min(c))
    price_max = float(np.max(c))

    if price_max == price_min:
        return None

    bin_edges = np.linspace(price_min, price_max, bins + 1)
    profile = []

    for j in range(bins):
        mask = (c >= bin_edges[j]) & (c < bin_edges[j + 1])
        vol = float(np.sum(v[mask]))
        profile.append({
            "price_low": round(float(bin_edges[j]), 2),
            "price_high": round(float(bin_edges[j + 1]), 2),
            "volume": round(vol, 0),
        })

    # Find POC (Point of Control) - highest volume level
    max_vol_idx = max(range(len(profile)), key=lambda x: profile[x]["volume"])
    poc = (profile[max_vol_idx]["price_low"] + profile[max_vol_idx]["price_high"]) / 2

    # Value Area (70% of volume)
    total_vol = sum(p["volume"] for p in profile)
    if total_vol == 0:
        return None

    sorted_by_vol = sorted(range(len(profile)), key=lambda x: profile[x]["volume"], reverse=True)
    va_vol = 0.0
    va_indices = []
    for idx in sorted_by_vol:
        va_vol += profile[idx]["volume"]
        va_indices.append(idx)
        if va_vol >= total_vol * 0.7:
            break

    va_high = max(profile[idx]["price_high"] for idx in va_indices)
    va_low = min(profile[idx]["price_low"] for idx in va_indices)

    return {
        "poc": round(poc, 2),
        "value_area_high": round(va_high, 2),
        "value_area_low": round(va_low, 2),
        "profile": profile,
    }


# ============================================================
# TREND STRENGTH (ADX-based + directional)
# ============================================================

def trend_strength_analysis(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> dict:
    """Comprehensive trend strength analysis."""
    n = min(len(highs), len(lows), len(closes))
    if n < 20:
        return {"strength": 0, "direction": "Unknown", "description": "Insufficient data"}

    # Simple linear regression slope
    x = np.arange(min(n, 50))
    c = closes[-len(x):]
    if len(c) < 2:
        return {"strength": 0, "direction": "Unknown", "description": "Insufficient data"}

    slope = float(np.polyfit(x, c, 1)[0])
    price_range = float(np.max(c) - np.min(c))
    normalized_slope = slope / price_range * 100 if price_range > 0 else 0

    # Moving average alignment
    ma_20 = float(np.mean(closes[-20:])) if n >= 20 else float(closes[-1])
    ma_50 = float(np.mean(closes[-50:])) if n >= 50 else ma_20

    if float(closes[-1]) > ma_20 > ma_50:
        alignment = "Bullish"
    elif float(closes[-1]) < ma_20 < ma_50:
        alignment = "Bearish"
    else:
        alignment = "Mixed"

    strength = min(100, abs(normalized_slope) * 10)

    if normalized_slope > 1:
        direction = "Strong Uptrend"
    elif normalized_slope > 0.2:
        direction = "Uptrend"
    elif normalized_slope < -1:
        direction = "Strong Downtrend"
    elif normalized_slope < -0.2:
        direction = "Downtrend"
    else:
        direction = "Sideways"

    return {
        "strength": round(strength, 1),
        "direction": direction,
        "slope": round(normalized_slope, 4),
        "ma_alignment": alignment,
        "description": f"{direction} with {alignment.lower()} MA alignment ({strength:.0f}% strength)",
    }


# ============================================================
# COMPUTE ALL ADVANCED ANALYSIS
# ============================================================

def compute_advanced_analysis(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray,
                               volumes: np.ndarray, opens: Optional[np.ndarray] = None) -> dict:
    """Compute all advanced analysis features."""
    result = {}

    # Bollinger Bands
    bb = bollinger_bands(closes, 20, 2.0)
    if bb:
        result["bollinger_bands"] = bb

    # ATR
    atr_val = atr(highs, lows, closes, 14)
    if atr_val is not None:
        result["atr"] = {"value": round(atr_val, 2), "period": 14}

    # OBV
    obv_data = obv(closes, volumes)
    if obv_data:
        result["obv"] = obv_data

    # VWAP
    vwap_data = vwap(highs, lows, closes, volumes)
    if vwap_data:
        result["vwap"] = vwap_data

    # Fibonacci
    fib = fibonacci_retracement(highs, lows)
    if fib:
        result["fibonacci"] = fib

    # Market Structure
    ms = detect_market_structure(highs, lows, closes)
    result["market_structure"] = ms

    # Candlestick Patterns
    if opens is not None and len(opens) > 0:
        patterns = detect_patterns(opens, highs, lows, closes)
    else:
        patterns = detect_patterns(closes, highs, lows, closes)  # Use closes as opens fallback
    result["patterns"] = patterns

    # Volume Profile
    vp = volume_profile(closes, volumes)
    if vp:
        result["volume_profile"] = vp

    # Trend Strength
    ts = trend_strength_analysis(highs, lows, closes)
    result["trend_strength"] = ts

    return result
