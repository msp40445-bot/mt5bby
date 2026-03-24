"""Technical indicators engine - computes all oscillators, moving averages, and pivots."""
import numpy as np
from typing import Optional


def _safe_divide(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b


# ============================================================
# MOVING AVERAGES
# ============================================================

def sma(data: np.ndarray, period: int) -> Optional[float]:
    """Simple Moving Average."""
    if len(data) < period:
        return None
    return float(np.mean(data[-period:]))


def ema(data: np.ndarray, period: int) -> Optional[float]:
    """Exponential Moving Average."""
    if len(data) < period:
        return None
    multiplier = 2.0 / (period + 1)
    result = float(data[0])
    for val in data[1:]:
        result = (float(val) - result) * multiplier + result
    return result


def wma(data: np.ndarray, period: int) -> Optional[float]:
    """Weighted Moving Average."""
    if len(data) < period:
        return None
    weights = np.arange(1, period + 1, dtype=float)
    return float(np.dot(data[-period:], weights) / weights.sum())


def hull_ma(data: np.ndarray, period: int = 9) -> Optional[float]:
    """Hull Moving Average."""
    if len(data) < period:
        return None
    half_period = max(1, period // 2)
    sqrt_period = max(1, int(np.sqrt(period)))

    wma_half = wma(data, half_period)
    wma_full = wma(data, period)
    if wma_half is None or wma_full is None:
        return None

    diff = 2 * wma_half - wma_full
    # Simplified HMA
    return diff


def vwma(closes: np.ndarray, volumes: np.ndarray, period: int = 20) -> Optional[float]:
    """Volume Weighted Moving Average."""
    if len(closes) < period or len(volumes) < period:
        return None
    c = closes[-period:]
    v = volumes[-period:]
    total_vol = np.sum(v)
    if total_vol == 0:
        return sma(closes, period)
    return float(np.sum(c * v) / total_vol)


def ichimoku_base(highs: np.ndarray, lows: np.ndarray, period: int = 26) -> Optional[float]:
    """Ichimoku Base Line (Kijun-sen)."""
    if len(highs) < period or len(lows) < period:
        return None
    h = float(np.max(highs[-period:]))
    l = float(np.min(lows[-period:]))
    return (h + l) / 2.0


# ============================================================
# OSCILLATORS
# ============================================================

def rsi(data: np.ndarray, period: int = 14) -> Optional[float]:
    """Relative Strength Index."""
    if len(data) < period + 1:
        return None
    deltas = np.diff(data[-(period + 1):])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains) if len(gains) > 0 else 0
    avg_loss = np.mean(losses) if len(losses) > 0 else 0

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100.0 - (100.0 / (1.0 + rs)))


def stochastic_k(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                  k_period: int = 14, d_period: int = 3) -> tuple[Optional[float], Optional[float]]:
    """Stochastic %K and %D."""
    if len(closes) < k_period:
        return None, None

    # Calculate %K values for d_period
    k_values = []
    for i in range(min(d_period, len(closes) - k_period + 1)):
        idx = len(closes) - 1 - i
        start = idx - k_period + 1
        h = float(np.max(highs[start:idx + 1]))
        l = float(np.min(lows[start:idx + 1]))
        c = float(closes[idx])
        if h == l:
            k_values.append(50.0)
        else:
            k_values.append(((c - l) / (h - l)) * 100.0)

    k_val = k_values[0] if k_values else None
    d_val = float(np.mean(k_values)) if len(k_values) >= d_period else k_val

    return k_val, d_val


def cci(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 20) -> Optional[float]:
    """Commodity Channel Index."""
    if len(closes) < period:
        return None
    tp = (highs[-period:] + lows[-period:] + closes[-period:]) / 3.0
    tp_mean = float(np.mean(tp))
    mad = float(np.mean(np.abs(tp - tp_mean)))
    if mad == 0:
        return 0.0
    return float((tp[-1] - tp_mean) / (0.015 * mad))


def adx(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Optional[float]:
    """Average Directional Index."""
    if len(closes) < period + 1:
        return None

    n = len(closes)
    tr_list = []
    plus_dm_list = []
    minus_dm_list = []

    for i in range(1, n):
        h = float(highs[i])
        l = float(lows[i])
        pc = float(closes[i - 1])
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_list.append(tr)

        up_move = h - float(highs[i - 1])
        down_move = float(lows[i - 1]) - l

        plus_dm = up_move if up_move > down_move and up_move > 0 else 0
        minus_dm = down_move if down_move > up_move and down_move > 0 else 0
        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)

    if len(tr_list) < period:
        return None

    # Smoothed values
    atr = float(np.mean(tr_list[-period:]))
    smooth_plus = float(np.mean(plus_dm_list[-period:]))
    smooth_minus = float(np.mean(minus_dm_list[-period:]))

    if atr == 0:
        return 0.0

    plus_di = 100 * smooth_plus / atr
    minus_di = 100 * smooth_minus / atr

    di_sum = plus_di + minus_di
    if di_sum == 0:
        return 0.0

    dx = 100 * abs(plus_di - minus_di) / di_sum
    return dx


def awesome_oscillator(highs: np.ndarray, lows: np.ndarray) -> Optional[float]:
    """Awesome Oscillator."""
    if len(highs) < 34:
        return None
    median = (highs + lows) / 2.0
    sma5 = float(np.mean(median[-5:]))
    sma34 = float(np.mean(median[-34:]))
    return sma5 - sma34


def momentum(data: np.ndarray, period: int = 10) -> Optional[float]:
    """Momentum indicator."""
    if len(data) < period + 1:
        return None
    return float(data[-1] - data[-period - 1])


def macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """MACD Line, Signal, and Histogram."""
    if len(data) < slow:
        return None, None, None

    ema_fast = ema(data, fast)
    ema_slow = ema(data, slow)

    if ema_fast is None or ema_slow is None:
        return None, None, None

    macd_line = ema_fast - ema_slow

    # Calculate MACD values for signal period
    macd_values = []
    for i in range(min(signal + 5, len(data) - slow)):
        subset = data[:len(data) - i] if i > 0 else data
        ef = ema(subset, fast)
        es = ema(subset, slow)
        if ef is not None and es is not None:
            macd_values.insert(0, ef - es)

    if len(macd_values) >= signal:
        signal_line = float(np.mean(macd_values[-signal:]))
    else:
        signal_line = macd_line

    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def stoch_rsi(data: np.ndarray, rsi_period: int = 14, stoch_period: int = 14,
              k_period: int = 3, d_period: int = 3) -> tuple[Optional[float], Optional[float]]:
    """Stochastic RSI."""
    if len(data) < rsi_period + stoch_period:
        return None, None

    # Calculate RSI values
    rsi_values = []
    for i in range(stoch_period + d_period):
        end_idx = len(data) - i
        if end_idx < rsi_period + 1:
            break
        r = rsi(data[:end_idx], rsi_period)
        if r is not None:
            rsi_values.insert(0, r)

    if len(rsi_values) < stoch_period:
        return None, None

    # Stochastic of RSI
    recent_rsi = rsi_values[-stoch_period:]
    h = max(recent_rsi)
    l = min(recent_rsi)

    if h == l:
        k_val = 50.0
    else:
        k_val = ((recent_rsi[-1] - l) / (h - l)) * 100.0

    # %D is SMA of %K
    d_val = k_val  # Simplified

    return k_val, d_val


def williams_r(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Optional[float]:
    """Williams %R."""
    if len(closes) < period:
        return None
    h = float(np.max(highs[-period:]))
    l = float(np.min(lows[-period:]))
    c = float(closes[-1])
    if h == l:
        return -50.0
    return float(((h - c) / (h - l)) * -100.0)


def bull_bear_power(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 13) -> Optional[float]:
    """Bull Bear Power (Elder Ray)."""
    e = ema(closes, period)
    if e is None:
        return None
    bull = float(highs[-1]) - e
    bear = float(lows[-1]) - e
    return bull + bear


def ultimate_oscillator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                         p1: int = 7, p2: int = 14, p3: int = 28) -> Optional[float]:
    """Ultimate Oscillator."""
    if len(closes) < p3 + 1:
        return None

    bp_list = []
    tr_list = []
    for i in range(1, len(closes)):
        c = float(closes[i])
        pc = float(closes[i - 1])
        h = float(highs[i])
        l = float(lows[i])
        true_low = min(l, pc)
        bp = c - true_low
        tr = max(h, pc) - true_low
        bp_list.append(bp)
        tr_list.append(tr)

    if len(bp_list) < p3:
        return None

    def avg_ratio(period: int) -> float:
        bp_sum = sum(bp_list[-period:])
        tr_sum = sum(tr_list[-period:])
        return _safe_divide(bp_sum, tr_sum)

    a1 = avg_ratio(p1)
    a2 = avg_ratio(p2)
    a3 = avg_ratio(p3)

    return float(100.0 * (4 * a1 + 2 * a2 + a3) / 7.0)


# ============================================================
# PIVOT POINTS
# ============================================================

def calculate_pivots(high: float, low: float, close: float, open_price: Optional[float] = None) -> list[dict]:
    """Calculate all pivot point types."""
    p = (high + low + close) / 3.0

    # Classic
    classic_p = p
    classic_r1 = 2 * p - low
    classic_s1 = 2 * p - high
    classic_r2 = p + (high - low)
    classic_s2 = p - (high - low)
    classic_r3 = high + 2 * (p - low)
    classic_s3 = low - 2 * (high - p)

    # Fibonacci
    diff = high - low
    fib_p = p
    fib_r1 = p + 0.382 * diff
    fib_s1 = p - 0.382 * diff
    fib_r2 = p + 0.618 * diff
    fib_s2 = p - 0.618 * diff
    fib_r3 = p + 1.0 * diff
    fib_s3 = p - 1.0 * diff

    # Camarilla
    cam_r1 = close + diff * 1.1 / 12.0
    cam_s1 = close - diff * 1.1 / 12.0
    cam_r2 = close + diff * 1.1 / 6.0
    cam_s2 = close - diff * 1.1 / 6.0
    cam_r3 = close + diff * 1.1 / 4.0
    cam_s3 = close - diff * 1.1 / 4.0

    # Woodie
    woodie_p = (high + low + 2 * close) / 4.0
    woodie_r1 = 2 * woodie_p - low
    woodie_s1 = 2 * woodie_p - high
    woodie_r2 = woodie_p + diff
    woodie_s2 = woodie_p - diff

    # DM
    if open_price is not None:
        if close < open_price:
            dm_x = high + 2 * low + close
        elif close > open_price:
            dm_x = 2 * high + low + close
        else:
            dm_x = high + low + 2 * close
    else:
        dm_x = high + low + 2 * close
    dm_p = dm_x / 4.0
    dm_r1 = dm_x / 2.0 - low
    dm_s1 = dm_x / 2.0 - high

    pivots = [
        {
            "name": "R3",
            "classic": round(classic_r3, 2),
            "fibonacci": round(fib_r3, 2),
            "camarilla": round(cam_r3, 2),
            "woodie": None,
            "dm": None,
        },
        {
            "name": "R2",
            "classic": round(classic_r2, 2),
            "fibonacci": round(fib_r2, 2),
            "camarilla": round(cam_r2, 2),
            "woodie": round(woodie_r2, 2),
            "dm": None,
        },
        {
            "name": "R1",
            "classic": round(classic_r1, 2),
            "fibonacci": round(fib_r1, 2),
            "camarilla": round(cam_r1, 2),
            "woodie": round(woodie_r1, 2),
            "dm": round(dm_r1, 2),
        },
        {
            "name": "P",
            "classic": round(classic_p, 2),
            "fibonacci": round(fib_p, 2),
            "camarilla": round(close, 2),
            "woodie": round(woodie_p, 2),
            "dm": round(dm_p, 2),
        },
        {
            "name": "S1",
            "classic": round(classic_s1, 2),
            "fibonacci": round(fib_s1, 2),
            "camarilla": round(cam_s1, 2),
            "woodie": round(woodie_s1, 2),
            "dm": round(dm_s1, 2),
        },
        {
            "name": "S2",
            "classic": round(classic_s2, 2),
            "fibonacci": round(fib_s2, 2),
            "camarilla": round(cam_s2, 2),
            "woodie": round(woodie_s2, 2),
            "dm": None,
        },
        {
            "name": "S3",
            "classic": round(classic_s3, 2),
            "fibonacci": round(fib_s3, 2),
            "camarilla": round(cam_s3, 2),
            "woodie": None,
            "dm": None,
        },
    ]
    return pivots


# ============================================================
# SIGNAL CLASSIFICATION
# ============================================================

def classify_ma_action(price: float, ma_value: Optional[float]) -> str:
    """Classify MA signal based on price vs MA."""
    if ma_value is None:
        return "Neutral"
    if price > ma_value:
        return "Buy"
    elif price < ma_value:
        return "Sell"
    return "Neutral"


def classify_rsi(value: Optional[float]) -> str:
    if value is None:
        return "Neutral"
    if value < 30:
        return "Buy"
    elif value > 70:
        return "Sell"
    return "Neutral"


def classify_stochastic(k: Optional[float], d: Optional[float]) -> str:
    if k is None:
        return "Neutral"
    if k < 20:
        return "Buy"
    elif k > 80:
        return "Sell"
    return "Neutral"


def classify_cci(value: Optional[float]) -> str:
    if value is None:
        return "Neutral"
    if value < -100:
        return "Buy"
    elif value > 100:
        return "Sell"
    return "Neutral"


def classify_adx(value: Optional[float]) -> str:
    if value is None:
        return "Neutral"
    if value > 25:
        return "Buy"
    elif value < 20:
        return "Neutral"
    return "Neutral"


def classify_ao(value: Optional[float]) -> str:
    if value is None:
        return "Neutral"
    if value > 0:
        return "Buy"
    elif value < 0:
        return "Sell"
    return "Neutral"


def classify_momentum(value: Optional[float]) -> str:
    if value is None:
        return "Neutral"
    if value > 0:
        return "Buy"
    elif value < 0:
        return "Sell"
    return "Neutral"


def classify_macd(hist: Optional[float]) -> str:
    if hist is None:
        return "Neutral"
    if hist > 0:
        return "Buy"
    elif hist < 0:
        return "Sell"
    return "Neutral"


def classify_williams(value: Optional[float]) -> str:
    if value is None:
        return "Neutral"
    if value < -80:
        return "Buy"
    elif value > -20:
        return "Sell"
    return "Neutral"


def classify_bbp(value: Optional[float]) -> str:
    if value is None:
        return "Neutral"
    if value > 0:
        return "Buy"
    elif value < 0:
        return "Sell"
    return "Neutral"


def classify_uo(value: Optional[float]) -> str:
    if value is None:
        return "Neutral"
    if value < 30:
        return "Buy"
    elif value > 70:
        return "Sell"
    return "Neutral"


def classify_stoch_rsi(k: Optional[float]) -> str:
    if k is None:
        return "Neutral"
    if k < 20:
        return "Buy"
    elif k > 80:
        return "Sell"
    return "Neutral"
