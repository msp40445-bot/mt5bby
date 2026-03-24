"""Signal aggregation engine - combines all indicators into actionable signals."""
from app.price_feed import PriceFeed
from app.indicators import (
    sma, ema, hull_ma, vwma, ichimoku_base,
    rsi, stochastic_k, cci, adx, awesome_oscillator,
    momentum, macd, stoch_rsi, williams_r, bull_bear_power,
    ultimate_oscillator, calculate_pivots,
    classify_ma_action, classify_rsi, classify_stochastic, classify_cci,
    classify_adx, classify_ao, classify_momentum, classify_macd,
    classify_williams, classify_bbp, classify_uo, classify_stoch_rsi,
)


def compute_oscillators(feed: PriceFeed, timeframe: str = "1m") -> list[dict]:
    """Compute all oscillator indicators for a given timeframe."""
    closes = feed.get_closes(timeframe)
    highs = feed.get_highs(timeframe)
    lows = feed.get_lows(timeframe)

    results = []

    # RSI(14)
    rsi_val = rsi(closes, 14)
    results.append({"name": "Relative Strength Index (14)", "value": round(rsi_val, 2) if rsi_val else None, "action": classify_rsi(rsi_val)})

    # Stochastic %K (14, 3, 3)
    stoch_k, stoch_d = stochastic_k(highs, lows, closes, 14, 3)
    results.append({"name": "Stochastic %K (14, 3, 3)", "value": round(stoch_k, 2) if stoch_k else None, "action": classify_stochastic(stoch_k, stoch_d)})

    # CCI(20)
    cci_val = cci(highs, lows, closes, 20)
    results.append({"name": "Commodity Channel Index (20)", "value": round(cci_val, 2) if cci_val else None, "action": classify_cci(cci_val)})

    # ADX(14)
    adx_val = adx(highs, lows, closes, 14)
    results.append({"name": "Average Directional Index (14)", "value": round(adx_val, 2) if adx_val else None, "action": classify_adx(adx_val)})

    # Awesome Oscillator
    ao_val = awesome_oscillator(highs, lows)
    results.append({"name": "Awesome Oscillator", "value": round(ao_val, 2) if ao_val else None, "action": classify_ao(ao_val)})

    # Momentum(10)
    mom_val = momentum(closes, 10)
    results.append({"name": "Momentum (10)", "value": round(mom_val, 2) if mom_val else None, "action": classify_momentum(mom_val)})

    # MACD(12, 26)
    macd_line, signal_line, hist = macd(closes, 12, 26, 9)
    results.append({"name": "MACD Level (12, 26)", "value": round(macd_line, 2) if macd_line else None, "action": classify_macd(hist)})

    # Stochastic RSI Fast (3, 3, 14, 14)
    srsi_k, srsi_d = stoch_rsi(closes, 14, 14, 3, 3)
    results.append({"name": "Stochastic RSI Fast (3, 3, 14, 14)", "value": round(srsi_k, 2) if srsi_k else None, "action": classify_stoch_rsi(srsi_k)})

    # Williams %R(14)
    wr_val = williams_r(highs, lows, closes, 14)
    results.append({"name": "Williams Percent Range (14)", "value": round(wr_val, 2) if wr_val else None, "action": classify_williams(wr_val)})

    # Bull Bear Power
    bbp_val = bull_bear_power(highs, lows, closes, 13)
    results.append({"name": "Bull Bear Power", "value": round(bbp_val, 2) if bbp_val else None, "action": classify_bbp(bbp_val)})

    # Ultimate Oscillator (7, 14, 28)
    uo_val = ultimate_oscillator(highs, lows, closes, 7, 14, 28)
    results.append({"name": "Ultimate Oscillator (7, 14, 28)", "value": round(uo_val, 2) if uo_val else None, "action": classify_uo(uo_val)})

    return results


def compute_moving_averages(feed: PriceFeed, timeframe: str = "1m") -> list[dict]:
    """Compute all moving average indicators for a given timeframe."""
    closes = feed.get_closes(timeframe)
    highs = feed.get_highs(timeframe)
    lows = feed.get_lows(timeframe)
    volumes = feed.get_volumes(timeframe)
    price = float(closes[-1]) if len(closes) > 0 else feed.current_price

    results = []

    # EMA periods
    for period in [10, 20, 30, 50, 100, 200]:
        val = ema(closes, period)
        results.append({
            "name": f"Exponential Moving Average ({period})",
            "value": round(val, 2) if val else None,
            "action": classify_ma_action(price, val),
        })

    # SMA periods
    for period in [10, 20, 30, 50, 100, 200]:
        val = sma(closes, period)
        results.append({
            "name": f"Simple Moving Average ({period})",
            "value": round(val, 2) if val else None,
            "action": classify_ma_action(price, val),
        })

    # Ichimoku Base Line (9, 26, 52, 26)
    ich_val = ichimoku_base(highs, lows, 26)
    results.append({
        "name": "Ichimoku Base Line (9, 26, 52, 26)",
        "value": round(ich_val, 2) if ich_val else None,
        "action": classify_ma_action(price, ich_val),
    })

    # VWMA(20)
    vwma_val = vwma(closes, volumes, 20)
    results.append({
        "name": "Volume Weighted Moving Average (20)",
        "value": round(vwma_val, 2) if vwma_val else None,
        "action": classify_ma_action(price, vwma_val),
    })

    # Hull MA(9)
    hma_val = hull_ma(closes, 9)
    results.append({
        "name": "Hull Moving Average (9)",
        "value": round(hma_val, 2) if hma_val else None,
        "action": classify_ma_action(price, hma_val),
    })

    return results


def compute_summary(indicators: list[dict]) -> dict:
    """Compute gauge summary from a list of indicators."""
    buy = sum(1 for i in indicators if i["action"] == "Buy")
    sell = sum(1 for i in indicators if i["action"] == "Sell")
    neutral = sum(1 for i in indicators if i["action"] == "Neutral")

    total = buy + sell + neutral
    if total == 0:
        return {"sell": 0, "neutral": 0, "buy": 0, "signal": "Neutral"}

    ratio = (buy - sell) / total

    if ratio > 0.5:
        signal = "Strong Buy"
    elif ratio > 0.1:
        signal = "Buy"
    elif ratio < -0.5:
        signal = "Strong Sell"
    elif ratio < -0.1:
        signal = "Sell"
    else:
        signal = "Neutral"

    return {"sell": sell, "neutral": neutral, "buy": buy, "signal": signal}


def compute_timeframe_signal(feed: PriceFeed, timeframe: str) -> dict:
    """Compute signal for a specific timeframe."""
    oscillators = compute_oscillators(feed, timeframe)
    mas = compute_moving_averages(feed, timeframe)

    osc_summary = compute_summary(oscillators)
    ma_summary = compute_summary(mas)

    # Combined summary
    all_indicators = oscillators + mas
    overall = compute_summary(all_indicators)

    # Strength: -1.0 (strong sell) to 1.0 (strong buy)
    total = overall["buy"] + overall["sell"] + overall["neutral"]
    strength = (overall["buy"] - overall["sell"]) / max(total, 1)

    if strength > 0.5:
        label = "STRONG BUY"
    elif strength > 0.15:
        label = "BUY"
    elif strength < -0.5:
        label = "STRONG SELL"
    elif strength < -0.15:
        label = "SELL"
    else:
        label = "NEUTRAL"

    return {
        "timeframe": timeframe,
        "oscillators": osc_summary,
        "moving_averages": ma_summary,
        "summary": overall,
        "strength": round(strength, 4),
        "label": label,
    }


def compute_master_signal(timeframe_signals: list[dict]) -> dict:
    """Compute a weighted master signal from all timeframe signals."""
    # Weight shorter timeframes more for scalping sensitivity
    weights = {
        "1s": 3.0,
        "5s": 2.5,
        "10s": 2.0,
        "30s": 1.5,
        "1m": 1.0,
        "5m": 0.8,
        "15m": 0.6,
        "1h": 0.4,
    }

    total_weight = 0.0
    weighted_strength = 0.0
    buy_count = 0
    sell_count = 0
    neutral_count = 0

    for sig in timeframe_signals:
        tf = sig["timeframe"]
        w = weights.get(tf, 1.0)
        total_weight += w
        weighted_strength += sig["strength"] * w

        buy_count += sig["summary"]["buy"]
        sell_count += sig["summary"]["sell"]
        neutral_count += sig["summary"]["neutral"]

    if total_weight == 0:
        final_strength = 0.0
    else:
        final_strength = weighted_strength / total_weight

    # Confidence based on agreement across timeframes
    agree_count = sum(1 for s in timeframe_signals if abs(s["strength"]) > 0.15)
    confidence = agree_count / max(len(timeframe_signals), 1) * 100

    if final_strength > 0.5:
        action = "STRONG BUY"
        color = "#00c853"
    elif final_strength > 0.15:
        action = "BUY"
        color = "#4caf50"
    elif final_strength < -0.5:
        action = "STRONG SELL"
        color = "#ff1744"
    elif final_strength < -0.15:
        action = "SELL"
        color = "#f44336"
    else:
        action = "NEUTRAL"
        color = "#9e9e9e"

    return {
        "action": action,
        "strength": round(final_strength, 4),
        "confidence": round(confidence, 1),
        "color": color,
        "total_buy": buy_count,
        "total_sell": sell_count,
        "total_neutral": neutral_count,
    }


def compute_full_analysis(feed: PriceFeed) -> dict:
    """Compute complete technical analysis across all timeframes."""
    import time

    # Get current price data
    tick = feed.tick()

    # Compute for primary timeframe (1m)
    oscillators = compute_oscillators(feed, "1m")
    mas = compute_moving_averages(feed, "1m")

    osc_summary = compute_summary(oscillators)
    ma_summary = compute_summary(mas)
    overall = compute_summary(oscillators + mas)

    # Compute pivots
    candles = feed.get_candles("1h")
    if len(candles) >= 2:
        prev = candles[-2]
        pivots = calculate_pivots(prev["high"], prev["low"], prev["close"], prev.get("open"))
    else:
        pivots = calculate_pivots(tick["high"], tick["low"], tick["price"], tick.get("open"))

    # Multi-timeframe signals
    timeframes = ["1s", "5s", "10s", "30s", "1m", "5m", "15m", "1h"]
    tf_signals = []
    for tf in timeframes:
        sig = compute_timeframe_signal(feed, tf)
        tf_signals.append(sig)

    # Master signal
    master = compute_master_signal(tf_signals)

    return {
        "symbol": feed.symbol,
        "price": tick,
        "oscillators": oscillators,
        "moving_averages": mas,
        "pivots": pivots,
        "oscillator_summary": osc_summary,
        "ma_summary": ma_summary,
        "overall_summary": overall,
        "timeframe_signals": tf_signals,
        "master_signal": master,
        "timestamp": time.time(),
    }
