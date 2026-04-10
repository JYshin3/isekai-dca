"""
이세계 DCA — Adaptive DCA Dashboard
Target: $500,000 in 3 years | Monthly Investment: $2,000
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import os
import requests
from pathlib import Path

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="이세계 DCA",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Dark Fantasy Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;900&family=IBM+Plex+Mono:wght@300;400;600&display=swap');

:root {
    --bg-primary: #070a0f;
    --bg-secondary: #0d1117;
    --bg-card: #0f1620;
    --bg-card2: #111927;
    --accent-gold: #c9a84c;
    --accent-blue: #4fa3e0;
    --accent-green: #3ecf8e;
    --accent-red: #e05c5c;
    --accent-orange: #e08c3c;
    --accent-purple: #9b6dff;
    --text-primary: #e8e6f0;
    --text-muted: #6b7a99;
    --border: #1e2a3a;
    --border-glow: #c9a84c33;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Mono', monospace;
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

.stApp {
    background: radial-gradient(ellipse at top left, #0d1628 0%, #070a0f 60%);
}

/* Header */
.isekai-header {
    text-align: center;
    padding: 2rem 0 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.isekai-header h1 {
    font-family: 'Cinzel', serif;
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(135deg, #c9a84c, #f0d080, #c9a84c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 4px;
    margin: 0;
    text-shadow: none;
}
.isekai-header p {
    color: var(--text-muted);
    font-size: 0.8rem;
    letter-spacing: 2px;
    margin-top: 0.5rem;
}

/* Cards */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem;
    margin-bottom: 1rem;
}
.card-gold {
    border-color: var(--accent-gold);
    box-shadow: 0 0 20px var(--border-glow);
}

/* Metric boxes */
.metric-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
.metric-label {
    font-size: 0.65rem;
    color: var(--text-muted);
    letter-spacing: 2px;
    text-transform: uppercase;
}
.metric-value {
    font-family: 'Cinzel', serif;
    font-size: 1.6rem;
    font-weight: 600;
    color: var(--accent-gold);
    margin: 0.3rem 0;
}
.metric-sub {
    font-size: 0.7rem;
    color: var(--text-muted);
}

/* Signal badges */
.signal-buy { background: #1a3a2a; color: #3ecf8e; border: 1px solid #3ecf8e55; padding: 3px 10px; border-radius: 4px; font-size: 0.7rem; letter-spacing: 1px; }
.signal-strong-buy { background: #0f2a1a; color: #2fff9e; border: 1px solid #2fff9e; padding: 3px 10px; border-radius: 4px; font-size: 0.7rem; letter-spacing: 1px; font-weight: 600; }
.signal-hold { background: #2a2a1a; color: #c9a84c; border: 1px solid #c9a84c55; padding: 3px 10px; border-radius: 4px; font-size: 0.7rem; letter-spacing: 1px; }
.signal-stop { background: #3a1a1a; color: #e05c5c; border: 1px solid #e05c5c55; padding: 3px 10px; border-radius: 4px; font-size: 0.7rem; letter-spacing: 1px; }

/* Section title */
.section-title {
    font-family: 'Cinzel', serif;
    font-size: 0.9rem;
    color: var(--accent-gold);
    letter-spacing: 3px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
    text-transform: uppercase;
}

/* Ticker row */
.ticker-header {
    font-family: 'Cinzel', serif;
    font-size: 1.1rem;
    color: var(--text-primary);
    letter-spacing: 2px;
}

/* Amount highlight */
.amount-highlight {
    font-family: 'Cinzel', serif;
    color: var(--accent-green);
    font-size: 1.3rem;
    font-weight: 600;
}
.amount-zero {
    color: var(--text-muted);
    font-size: 0.9rem;
}

/* Progress bar custom */
.progress-container {
    background: #1a2233;
    border-radius: 4px;
    height: 6px;
    margin: 4px 0;
}
.progress-fill {
    height: 6px;
    border-radius: 4px;
    background: linear-gradient(90deg, #c9a84c, #f0d080);
}

/* RSI gauge colors */
.rsi-hot { color: #e05c5c; }
.rsi-warm { color: #e08c3c; }
.rsi-cool { color: #3ecf8e; }
.rsi-cold { color: #4fa3e0; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}

/* Streamlit overrides */
.stButton > button {
    background: var(--bg-card2);
    color: var(--accent-gold);
    border: 1px solid var(--accent-gold);
    border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 1px;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: var(--accent-gold);
    color: var(--bg-primary);
}

div[data-testid="stMetricValue"] {
    font-family: 'Cinzel', serif !important;
    color: var(--accent-gold) !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 1px;
    color: var(--text-muted);
}
.stTabs [aria-selected="true"] {
    color: var(--accent-gold) !important;
}

.stDataFrame { font-size: 0.8rem; }

hr { border-color: var(--border); }

/* Table styling */
table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
th { color: var(--text-muted); font-size: 0.65rem; letter-spacing: 2px; border-bottom: 1px solid var(--border); padding: 0.5rem; }
td { padding: 0.6rem 0.5rem; border-bottom: 1px solid var(--border)20; }

/* Rebalance action */
.rebal-buy { color: #3ecf8e; font-weight: 600; }
.rebal-sell { color: #e05c5c; font-weight: 600; }
.rebal-hold { color: var(--text-muted); }

/* Warning box */
.warning-box {
    background: #2a1a0a;
    border: 1px solid #e08c3c55;
    border-left: 3px solid var(--accent-orange);
    border-radius: 4px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.78rem;
    color: #e08c3c;
}
.info-box {
    background: #0a1a2a;
    border: 1px solid #4fa3e055;
    border-left: 3px solid var(--accent-blue);
    border-radius: 4px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.78rem;
    color: #4fa3e0;
}
.success-box {
    background: #0a2a1a;
    border: 1px solid #3ecf8e55;
    border-left: 3px solid var(--accent-green);
    border-radius: 4px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.78rem;
    color: #3ecf8e;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS & CONFIG
# ─────────────────────────────────────────────
TICKERS = {
    "GOOGL": {"name": "Alphabet", "weight": 0.30, "color": "#4fa3e0", "monthly_base": 600},
    "IREN":  {"name": "IREN Ltd", "weight": 0.40, "color": "#c9a84c", "monthly_base": 800},
    "NXE":   {"name": "NexGen Energy", "weight": 0.10, "color": "#9b6dff", "monthly_base": 200},
    "IONQ":  {"name": "IonQ", "weight": 0.05, "color": "#e05c5c", "monthly_base": 100},
    "MU":    {"name": "Micron Technology", "weight": 0.15, "color": "#3ecf8e", "monthly_base": 300},
}
MONTHLY_BUDGET = 2000
PORTFOLIO_TARGET = 500000
INVESTMENT_MONTHS = 36

# Indicator params per ticker
INDICATOR_PARAMS = {
    "GOOGL": {"rsi_period": 14, "stoch_k": 14, "stoch_d": 14, "macd": (12,26,9), "bb_std": 2.0, "atr_period": 14, "adx_period": 14},
    "IREN":  {"rsi_period": 20, "stoch_k": 20, "stoch_d": 10, "macd": (20,40,9), "bb_std": 2.5, "atr_period": 20, "adx_period": 20},
    "NXE":   {"rsi_period": 20, "stoch_k": 20, "stoch_d": 10, "macd": (20,40,9), "bb_std": 2.0, "atr_period": 20, "adx_period": 20},
    "MU":    {"rsi_period": 20, "stoch_k": 20, "stoch_d": 10, "macd": (24,52,9), "bb_std": 2.5, "atr_period": 20, "adx_period": 20},
    "IONQ":  {"rsi_period": 14, "stoch_k": 14, "stoch_d": 14, "macd": (24,52,9), "bb_std": 2.0, "atr_period": 14, "adx_period": 14},
}

PORTFOLIO_FILE = Path("portfolio.json")

# ─────────────────────────────────────────────
# DATA FUNCTIONS
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패 ({ticker}): {e}")
        return pd.DataFrame()

def compute_indicators(df: pd.DataFrame, params: dict) -> dict:
    if df.empty or len(df) < 60:
        return {}
    close = df["Close"].astype(float)
    high  = df["High"].astype(float)
    low   = df["Low"].astype(float)
    vol   = df["Volume"].astype(float)

    # RSI
    rsi_s = ta.rsi(close, length=params["rsi_period"])
    rsi = float(rsi_s.iloc[-1]) if rsi_s is not None and not rsi_s.empty else 50.0

    # StochRSI
    srsi = ta.stochrsi(close, length=params["stoch_k"], rsi_length=params["rsi_period"],
                       k=params["stoch_k"], d=params["stoch_d"])
    stoch_k = float(srsi[f"STOCHRSIk_{params['rsi_period']}_{params['stoch_k']}_{params['stoch_k']}_{params['stoch_d']}"].iloc[-1]) if srsi is not None and not srsi.empty else 50.0
    stoch_d = float(srsi[f"STOCHRSId_{params['rsi_period']}_{params['stoch_k']}_{params['stoch_k']}_{params['stoch_d']}"].iloc[-1]) if srsi is not None and not srsi.empty else 50.0

    # MACD
    fast, slow, sig = params["macd"]
    macd_df = ta.macd(close, fast=fast, slow=slow, signal=sig)
    macd_hist = 0.0
    macd_val  = 0.0
    if macd_df is not None and not macd_df.empty:
        hist_col = f"MACDh_{fast}_{slow}_{sig}"
        macd_col = f"MACD_{fast}_{slow}_{sig}"
        if hist_col in macd_df.columns:
            macd_hist = float(macd_df[hist_col].iloc[-1])
        if macd_col in macd_df.columns:
            macd_val = float(macd_df[macd_col].iloc[-1])
        # Check histogram direction (last 2)
        if hist_col in macd_df.columns and len(macd_df) >= 2:
            macd_hist_prev = float(macd_df[hist_col].iloc[-2])
        else:
            macd_hist_prev = macd_hist

    # Bollinger Bands
    bb = ta.bbands(close, length=20, std=params["bb_std"])
    bb_lower = bb[f"BBL_20_{params['bb_std']}"].iloc[-1] if bb is not None else close.iloc[-1]
    bb_upper = bb[f"BBU_20_{params['bb_std']}"].iloc[-1] if bb is not None else close.iloc[-1]
    bb_mid   = bb[f"BBM_20_{params['bb_std']}"].iloc[-1] if bb is not None else close.iloc[-1]

    # MA
    sma80  = float(ta.sma(close, length=80).iloc[-1]) if len(df) >= 80 else float(close.mean())
    sma200 = float(ta.sma(close, length=200).iloc[-1]) if len(df) >= 200 else float(close.mean())
    ema20  = float(ta.ema(close, length=20).iloc[-1])

    # ATR
    atr_s = ta.atr(high, low, close, length=params["atr_period"])
    atr = float(atr_s.iloc[-1]) if atr_s is not None else 0.0
    atr_avg = float(atr_s.rolling(30).mean().iloc[-1]) if atr_s is not None and len(atr_s) >= 30 else atr

    # ADX
    adx_df = ta.adx(high, low, close, length=params["adx_period"])
    adx_col = f"ADX_{params['adx_period']}"
    adx = float(adx_df[adx_col].iloc[-1]) if adx_df is not None and adx_col in adx_df.columns else 20.0

    # Volume spike
    vol_avg = float(vol.rolling(20).mean().iloc[-1])
    vol_spike = float(vol.iloc[-1]) / vol_avg if vol_avg > 0 else 1.0

    # Z-Score (30-day)
    z_period = 30
    if len(close) >= z_period:
        z_mean = close.rolling(z_period).mean()
        z_std  = close.rolling(z_period).std()
        z_score = float(((close - z_mean) / z_std).iloc[-1])
    else:
        z_score = 0.0

    # Price
    price_now  = float(close.iloc[-1])
    price_prev = float(close.iloc[-2]) if len(close) > 1 else price_now
    price_chg  = (price_now - price_prev) / price_prev * 100

    # 1-week change
    price_1w = float(close.iloc[-6]) if len(close) > 6 else price_now
    chg_1w = (price_now - price_1w) / price_1w * 100

    # Higher Low detection (simple: last low > prev low)
    recent_lows = low.rolling(5).min()
    higher_low = bool(recent_lows.iloc[-1] > recent_lows.iloc[-6]) if len(recent_lows) >= 6 else False

    return {
        "price": price_now,
        "price_chg": price_chg,
        "chg_1w": chg_1w,
        "rsi": rsi,
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
        "macd_hist": macd_hist,
        "macd_hist_prev": macd_hist_prev if 'macd_hist_prev' in dir() else macd_hist,
        "macd_val": macd_val,
        "bb_lower": float(bb_lower),
        "bb_upper": float(bb_upper),
        "bb_mid": float(bb_mid),
        "sma80": sma80,
        "sma200": sma200,
        "ema20": ema20,
        "atr": atr,
        "atr_avg": atr_avg,
        "adx": adx,
        "vol_spike": vol_spike,
        "z_score": z_score,
        "higher_low": higher_low,
    }

# ─────────────────────────────────────────────
# SIGNAL ENGINE
# ─────────────────────────────────────────────
def get_iren_signal(ind: dict) -> dict:
    rsi = ind.get("rsi", 50)
    atr = ind.get("atr", 0)
    atr_avg = ind.get("atr_avg", 1)
    z = ind.get("z_score", 0)
    price = ind.get("price", 0)
    ema20 = ind.get("ema20", price)
    macd_hist = ind.get("macd_hist", 0)
    macd_hist_prev = ind.get("macd_hist_prev", macd_hist)
    stoch_k = ind.get("stoch_k", 50)
    stoch_d = ind.get("stoch_d", 50)
    higher_low = ind.get("higher_low", False)
    price_chg = ind.get("price_chg", 0)

    # ATR excessive check
    atr_excessive = (atr > atr_avg * 2) if atr_avg > 0 else False

    # Signal level
    if rsi > 60 or atr_excessive:
        level, multiplier = "STOP", 0
        signal_text = "❌ 매수 중단 (RSI 과열)" if rsi > 60 else "❌ 매수 중단 (변동성 과다)"
    elif 35 <= rsi <= 60:
        level, multiplier = "BUY", 1
        signal_text = "✅ 기본 매수"
    elif rsi < 25 and price_chg <= -10:
        level, multiplier = "STRONG_BUY_3X", 3
        signal_text = "🔥 3배 매수 (RSI<25 + 폭락 -10%)"
    elif rsi < 35:
        level, multiplier = "STRONG_BUY_2X", 2
        signal_text = "⚡ 2배 매수 (RSI<35)"
    else:
        level, multiplier = "BUY", 1
        signal_text = "✅ 기본 매수"

    # Ignition bonus (+$300)
    ignition_conditions = {
        "MA20 위 회복": price > ema20,
        "MACD 히스토 상승": macd_hist > macd_hist_prev,
        "Higher Low 확인": higher_low,
        "StochRSI 20→40 돌파": stoch_k > 40 and stoch_d < stoch_k and stoch_k > 20,
    }
    ignition_met = sum(ignition_conditions.values())
    ignition_bonus = 300 if (ignition_met >= 2 and multiplier > 0) else 0

    return {
        "level": level,
        "multiplier": multiplier,
        "signal_text": signal_text,
        "ignition_conditions": ignition_conditions,
        "ignition_met": ignition_met,
        "ignition_bonus": ignition_bonus,
        "base_amount": 800,
        "recommended_amount": min(800 * multiplier + ignition_bonus, MONTHLY_BUDGET - 600),
    }

def get_nxe_signal(ind: dict, uranium_price: float = 68.0) -> dict:
    rsi = ind.get("rsi", 50)
    if uranium_price > 82:
        level, multiplier = "STOP", 0
        signal_text = f"❌ 매수 중단 (우라늄 ${uranium_price:.0f} > $82)"
    elif 75 <= uranium_price <= 82:
        level, multiplier = "BUY", 1
        signal_text = f"✅ 기본 매수 (우라늄 ${uranium_price:.0f})"
    elif 70 <= uranium_price < 75:
        level, multiplier = "STRONG_BUY_2X", 2
        signal_text = f"⚡ 2배 매수 (우라늄 ${uranium_price:.0f})"
    else:  # < 70
        level, multiplier = "STRONG_BUY_3X", 3
        signal_text = f"🔥 3배 매수 (우라늄 ${uranium_price:.0f} < $70)"

    return {
        "level": level,
        "multiplier": multiplier,
        "signal_text": signal_text,
        "base_amount": 200,
        "recommended_amount": 200 * multiplier,
        "uranium_price": uranium_price,
    }

def get_ionq_signal(ind: dict) -> dict:
    rsi = ind.get("rsi", 50)
    if rsi > 65:
        level, multiplier = "STOP", 0
        signal_text = f"❌ 매수 중단 (RSI {rsi:.0f} > 65)"
    elif 45 <= rsi <= 65:
        level, multiplier = "BUY", 1
        signal_text = f"✅ 기본 매수 (RSI {rsi:.0f})"
    elif 30 <= rsi < 45:
        level, multiplier = "STRONG_BUY_2X", 2
        signal_text = f"⚡ 2배 매수 (RSI {rsi:.0f} < 45)"
    else:
        level, multiplier = "STRONG_BUY_3X", 3
        signal_text = f"🔥 3배 매수 (RSI {rsi:.0f} < 30)"

    return {
        "level": level,
        "multiplier": multiplier,
        "signal_text": signal_text,
        "base_amount": 100,
        "recommended_amount": 100 * multiplier,
    }

def get_mu_signal(ind: dict, earnings_drop: bool = False) -> dict:
    rsi = ind.get("rsi", 50)
    if rsi > 65:
        level, multiplier = "STOP", 0
        signal_text = f"❌ 매수 중단 (RSI {rsi:.0f} > 65)"
    elif 45 <= rsi <= 65:
        level, multiplier = "BUY", 1
        signal_text = f"✅ 기본 매수 (RSI {rsi:.0f})"
    else:
        level, multiplier = "STRONG_BUY_2X", 2
        signal_text = f"⚡ 2배 매수 (RSI {rsi:.0f} < 45)"

    earnings_bonus = 300 if earnings_drop else 0
    if earnings_drop and multiplier > 0:
        signal_text += " + 실적 후 급락 보너스 +$300"

    return {
        "level": level,
        "multiplier": multiplier,
        "signal_text": signal_text,
        "base_amount": 300,
        "recommended_amount": 300 * multiplier + earnings_bonus,
        "earnings_bonus": earnings_bonus,
    }

def get_googl_signal(ind: dict) -> dict:
    return {
        "level": "BUY",
        "multiplier": 1,
        "signal_text": "✅ 고정 매수 (DCA 앵커)",
        "base_amount": 600,
        "recommended_amount": 600,
    }

def compute_monthly_allocation(signals: dict, budget: int = 2000) -> dict:
    """Budget-constrained allocation with GOOGL as absorber"""
    # GOOGL fixed first
    googl_base = 600
    remaining = budget - googl_base

    # Priority order: IREN > MU > NXE > IONQ
    priority = ["IREN", "MU", "NXE", "IONQ"]
    allocation = {"GOOGL": googl_base}
    spent = googl_base

    for ticker in priority:
        sig = signals.get(ticker, {})
        amt = sig.get("recommended_amount", 0)
        if amt > 0 and spent + amt <= budget:
            allocation[ticker] = amt
            spent += amt
        elif amt > 0 and spent < budget:
            # Partial fill
            allocation[ticker] = budget - spent
            spent = budget
        else:
            allocation[ticker] = 0

    # Any remaining -> GOOGL
    leftover = budget - spent
    if leftover > 0:
        allocation["GOOGL"] = allocation.get("GOOGL", 0) + leftover

    return allocation

# ─────────────────────────────────────────────
# PORTFOLIO STATE (JSON persistence)
# ─────────────────────────────────────────────
def load_portfolio() -> dict:
    default = {
        "holdings": {t: {"shares": 0.0, "avg_cost": 0.0, "total_invested": 0.0} for t in TICKERS},
        "total_invested": 0.0,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "monthly_log": [],
        "uranium_price": 68.0,
        "earnings_drop_mu": False,
    }
    if PORTFOLIO_FILE.exists():
        try:
            with open(PORTFOLIO_FILE) as f:
                data = json.load(f)
                # Merge defaults
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                return data
        except:
            return default
    return default

def save_portfolio(pf: dict):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(pf, f, indent=2, default=str)

# ─────────────────────────────────────────────
# REBALANCING ENGINE
# ─────────────────────────────────────────────
def compute_rebalance(portfolio: dict, current_prices: dict) -> dict:
    holdings = portfolio["holdings"]

    # Current values
    values = {}
    for t, h in holdings.items():
        p = current_prices.get(t, 0)
        values[t] = h["shares"] * p

    total_value = sum(values.values())
    if total_value == 0:
        return {"total_value": 0, "actions": [], "weights": {}}

    # Current weights
    current_weights = {t: v / total_value for t, v in values.items()}
    target_weights = {t: info["weight"] for t, info in TICKERS.items()}

    actions = []

    # Rule 1: IREN > 50% → trim
    if current_weights.get("IREN", 0) > 0.50:
        excess_val = (current_weights["IREN"] - 0.40) * total_value
        actions.append({
            "type": "TRIM",
            "ticker": "IREN",
            "reason": f"비중 {current_weights['IREN']*100:.1f}% > 50% 초과",
            "amount": excess_val,
            "redistribute": {"GOOGL": 0.50, "MU": 0.30, "NXE": 0.20},
        })

    # Rule 2: GOOGL > 40% → move to IREN
    if current_weights.get("GOOGL", 0) > 0.40:
        excess_val = (current_weights["GOOGL"] - 0.30) * total_value
        actions.append({
            "type": "ROTATE",
            "ticker": "GOOGL→IREN",
            "reason": f"GOOGL 비중 {current_weights['GOOGL']*100:.1f}% > 40% — 성장주로 이동",
            "amount": excess_val,
        })

    # Rule 4: IONQ > 10% → trim to GOOGL
    if current_weights.get("IONQ", 0) > 0.10:
        excess_val = (current_weights["IONQ"] - 0.05) * total_value
        actions.append({
            "type": "TRIM",
            "ticker": "IONQ",
            "reason": f"IONQ 비중 {current_weights['IONQ']*100:.1f}% > 10% — GOOGL로 이동",
            "amount": excess_val,
        })

    # General rebalance suggestions
    for t in TICKERS:
        diff = (target_weights[t] - current_weights.get(t, 0)) * 100
        if abs(diff) >= 5:  # >5% drift
            actions.append({
                "type": "REBALANCE",
                "ticker": t,
                "reason": f"목표 {target_weights[t]*100:.0f}% vs 현재 {current_weights.get(t,0)*100:.1f}% (차이 {diff:+.1f}%)",
                "amount": abs(diff / 100 * total_value),
                "direction": "BUY" if diff > 0 else "SELL",
            })

    return {
        "total_value": total_value,
        "current_weights": current_weights,
        "target_weights": target_weights,
        "values": values,
        "actions": actions,
    }

# ─────────────────────────────────────────────
# GOAL TRACKER
# ─────────────────────────────────────────────
def compute_goal_progress(portfolio: dict, current_prices: dict) -> dict:
    holdings = portfolio["holdings"]
    total_value = sum(h["shares"] * current_prices.get(t, 0) for t, h in holdings.items())
    total_invested = portfolio.get("total_invested", 0)
    unrealized_pnl = total_value - total_invested

    start = datetime.strptime(portfolio.get("start_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
    elapsed_months = max((datetime.now() - start).days / 30, 0.1)
    remaining_months = max(INVESTMENT_MONTHS - elapsed_months, 0)

    # Simple projection: remaining investment + growth
    avg_monthly_return = 0.008  # ~10% annual conservative
    future_contributions = MONTHLY_BUDGET * remaining_months
    projected = total_value * (1 + avg_monthly_return) ** remaining_months + \
                MONTHLY_BUDGET * ((1 + avg_monthly_return) ** remaining_months - 1) / avg_monthly_return

    return {
        "total_value": total_value,
        "total_invested": total_invested,
        "unrealized_pnl": unrealized_pnl,
        "pnl_pct": (unrealized_pnl / total_invested * 100) if total_invested > 0 else 0,
        "goal_pct": (total_value / PORTFOLIO_TARGET * 100),
        "elapsed_months": elapsed_months,
        "remaining_months": remaining_months,
        "projected": projected,
        "projected_optimistic": projected * 1.8,
        "projected_conservative": projected * 0.6,
    }

# ─────────────────────────────────────────────
# CHART FUNCTIONS
# ─────────────────────────────────────────────
def make_price_chart(df: pd.DataFrame, ticker: str, ind: dict) -> go.Figure:
    params = INDICATOR_PARAMS[ticker]
    color = TICKERS[ticker]["color"]

    fig = make_subplots(
        rows=3, cols=1,
        row_heights=[0.55, 0.25, 0.20],
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=("", "RSI", "MACD 히스토그램"),
    )

    close = df["Close"].astype(float)
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=close,
        name=ticker,
        increasing_line_color=color,
        decreasing_line_color="#e05c5c",
        increasing_fillcolor=color + "88",
        decreasing_fillcolor="#e05c5c88",
    ), row=1, col=1)

    # MA lines
    sma80 = ta.sma(close, length=80)
    sma200 = ta.sma(close, length=200)
    if sma80 is not None:
        fig.add_trace(go.Scatter(x=df.index, y=sma80, name="SMA80",
                                  line=dict(color="#c9a84c", width=1, dash="dot")), row=1, col=1)
    if sma200 is not None:
        fig.add_trace(go.Scatter(x=df.index, y=sma200, name="SMA200",
                                  line=dict(color="#9b6dff", width=1, dash="dot")), row=1, col=1)

    # BB
    bb = ta.bbands(close, length=20, std=params["bb_std"])
    if bb is not None:
        fig.add_trace(go.Scatter(x=df.index, y=bb[f"BBU_20_{params['bb_std']}"],
                                  name="BB Upper", line=dict(color="#4fa3e055", width=1),
                                  showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=bb[f"BBL_20_{params['bb_std']}"],
                                  name="BB Lower", line=dict(color="#4fa3e055", width=1),
                                  fill="tonexty", fillcolor="#4fa3e011", showlegend=False), row=1, col=1)

    # RSI
    rsi_s = ta.rsi(close, length=params["rsi_period"])
    if rsi_s is not None:
        fig.add_trace(go.Scatter(x=df.index, y=rsi_s, name="RSI",
                                  line=dict(color=color, width=1.5)), row=2, col=1)
        fig.add_hline(y=60, line_color="#e05c5c55", line_dash="dot", row=2, col=1)
        fig.add_hline(y=35, line_color="#3ecf8e55", line_dash="dot", row=2, col=1)
        fig.add_hline(y=25, line_color="#3ecf8ebb", line_dash="dot", row=2, col=1)

    # MACD
    fast, slow, sig = params["macd"]
    macd_df = ta.macd(close, fast=fast, slow=slow, signal=sig)
    if macd_df is not None:
        hist_col = f"MACDh_{fast}_{slow}_{sig}"
        if hist_col in macd_df.columns:
            hist = macd_df[hist_col]
            colors = ["#3ecf8e" if v >= 0 else "#e05c5c" for v in hist]
            fig.add_trace(go.Bar(x=df.index, y=hist, name="MACD Hist",
                                  marker_color=colors, opacity=0.8), row=3, col=1)

    fig.update_layout(
        height=500,
        paper_bgcolor="#0f1620",
        plot_bgcolor="#070a0f",
        font=dict(family="IBM Plex Mono", size=10, color="#6b7a99"),
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        xaxis_rangeslider_visible=False,
    )
    for i in range(1, 4):
        fig.update_xaxes(gridcolor="#1e2a3a", row=i, col=1)
        fig.update_yaxes(gridcolor="#1e2a3a", row=i, col=1)

    return fig

def make_portfolio_pie(weights: dict, values: dict) -> go.Figure:
    labels = list(weights.keys())
    vals = [values.get(t, 0) for t in labels]
    colors = [TICKERS[t]["color"] for t in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=vals,
        hole=0.65,
        marker=dict(colors=colors, line=dict(color="#070a0f", width=2)),
        textinfo="label+percent",
        textfont=dict(family="IBM Plex Mono", size=11),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="#0f1620",
        plot_bgcolor="#0f1620",
        font=dict(color="#e8e6f0"),
        margin=dict(l=0, r=0, t=0, b=0),
        height=250,
        showlegend=False,
    )
    return fig

# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────

# Header
st.markdown("""
<div class="isekai-header">
    <h1>⚔ 이세계 DCA ⚔</h1>
    <p>ADAPTIVE DCA SYSTEM · TARGET $500,000 · 36 MONTHS</p>
</div>
""", unsafe_allow_html=True)

# Load portfolio state
portfolio = load_portfolio()

# Sidebar
with st.sidebar:
    st.markdown('<div class="section-title">⚙ 시스템 설정</div>', unsafe_allow_html=True)

    uranium_price = st.number_input(
        "우라늄 현물가 (U₃O₈ $/lb)",
        min_value=30.0, max_value=150.0,
        value=float(portfolio.get("uranium_price", 68.0)),
        step=0.5,
        help="UxC 또는 Cameco 사이트에서 주 1회 업데이트"
    )
    portfolio["uranium_price"] = uranium_price

    earnings_drop_mu = st.checkbox(
        "MU 실적 발표 후 -10% 급락?",
        value=portfolio.get("earnings_drop_mu", False),
    )
    portfolio["earnings_drop_mu"] = earnings_drop_mu

    st.markdown("---")
    st.markdown('<div class="section-title">📁 포트폴리오 입력</div>', unsafe_allow_html=True)

    with st.expander("보유 주식 입력", expanded=False):
        for t in TICKERS:
            h = portfolio["holdings"][t]
            col1, col2 = st.columns(2)
            with col1:
                h["shares"] = st.number_input(f"{t} 주수", min_value=0.0, value=float(h["shares"]), step=0.01, key=f"sh_{t}")
            with col2:
                h["avg_cost"] = st.number_input(f"평균단가", min_value=0.0, value=float(h["avg_cost"]), step=0.01, key=f"ac_{t}")
            h["total_invested"] = h["shares"] * h["avg_cost"]

        portfolio["total_invested"] = sum(h["total_invested"] for h in portfolio["holdings"].values())
        portfolio["start_date"] = st.text_input("투자 시작일 (YYYY-MM-DD)", value=portfolio.get("start_date", datetime.now().strftime("%Y-%m-%d")))

    if st.button("💾 저장"):
        save_portfolio(portfolio)
        st.success("저장 완료!")

    st.markdown("---")
    refresh = st.button("🔄 데이터 새로고침")
    if refresh:
        st.cache_data.clear()
        st.rerun()

    st.markdown(f'<div class="metric-label" style="margin-top:1rem">마지막 업데이트</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:#6b7a99; font-size:0.7rem">{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)

# ─── FETCH DATA ───
with st.spinner("시장 데이터 로딩 중..."):
    market_data = {}
    indicators = {}
    current_prices = {}
    for t in TICKERS:
        df = fetch_data(t, "1y")
        market_data[t] = df
        if not df.empty:
            ind = compute_indicators(df, INDICATOR_PARAMS[t])
            indicators[t] = ind
            current_prices[t] = ind.get("price", 0)
        else:
            indicators[t] = {}
            current_prices[t] = 0

# ─── COMPUTE SIGNALS ───
signals = {
    "GOOGL": get_googl_signal(indicators.get("GOOGL", {})),
    "IREN":  get_iren_signal(indicators.get("IREN", {})),
    "NXE":   get_nxe_signal(indicators.get("NXE", {}), uranium_price),
    "IONQ":  get_ionq_signal(indicators.get("IONQ", {})),
    "MU":    get_mu_signal(indicators.get("MU", {}), earnings_drop_mu),
}
allocation = compute_monthly_allocation(signals, MONTHLY_BUDGET)
goal = compute_goal_progress(portfolio, current_prices)
rebal = compute_rebalance(portfolio, current_prices)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tabs = st.tabs(["📡 오늘의 신호", "📊 종목 분석", "💰 이번 달 DCA", "⚖ 리밸런싱", "🎯 목표 추적"])

# ════════════════════════════════
# TAB 1: 오늘의 신호
# ════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-title">⚡ 실시간 매수 신호</div>', unsafe_allow_html=True)

    total_today = sum(allocation.values())
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">이번 달 총 매수</div>
            <div class="metric-value">${total_today:,.0f}</div>
            <div class="metric-sub">예산 ${MONTHLY_BUDGET:,}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        active_signals = sum(1 for s in signals.values() if s["multiplier"] > 0)
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">활성 신호</div>
            <div class="metric-value">{active_signals}/5</div>
            <div class="metric-sub">종목</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        strong_signals = sum(1 for s in signals.values() if s["multiplier"] >= 2)
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">강력 신호 (2x+)</div>
            <div class="metric-value" style="color:#e05c5c">{strong_signals}</div>
            <div class="metric-sub">종목</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        iren_ig = signals.get("IREN", {}).get("ignition_met", 0)
        ig_color = "#3ecf8e" if iren_ig >= 2 else "#c9a84c" if iren_ig == 1 else "#6b7a99"
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">IREN 불타기 조건</div>
            <div class="metric-value" style="color:{ig_color}">{iren_ig}/4</div>
            <div class="metric-sub">{"🔥 보너스 +$300 활성" if iren_ig >= 2 else "미충족"}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Signal cards per ticker
    for t, info in TICKERS.items():
        ind = indicators.get(t, {})
        sig = signals.get(t, {})
        alloc = allocation.get(t, 0)
        price = current_prices.get(t, 0)
        price_chg = ind.get("price_chg", 0)
        rsi = ind.get("rsi", 0)
        mult = sig.get("multiplier", 0)

        # Color coding
        if mult == 0:
            border_color = "#e05c5c"
            badge_html = '<span class="signal-stop">STOP</span>'
        elif mult >= 3:
            border_color = "#3ecf8e"
            badge_html = '<span class="signal-strong-buy">3× 매수</span>'
        elif mult == 2:
            border_color = "#c9a84c"
            badge_html = '<span class="signal-strong-buy" style="background:#2a1a0a;color:#e08c3c;border-color:#e08c3c">2× 매수</span>'
        else:
            border_color = "#4fa3e0"
            badge_html = '<span class="signal-buy">기본 매수</span>'

        chg_color = "#3ecf8e" if price_chg >= 0 else "#e05c5c"
        chg_sign = "▲" if price_chg >= 0 else "▼"

        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1.5, 1.5, 1.5, 2])
        with col1:
            st.markdown(f"""<div style="padding:0.8rem;background:#0f1620;border:1px solid {border_color}44;border-left:3px solid {border_color};border-radius:6px">
                <div style="font-family:'Cinzel',serif;font-size:1rem;color:#e8e6f0">{t}</div>
                <div style="font-size:0.65rem;color:#6b7a99">{info['name']}</div>
                {badge_html}
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div style="padding:0.8rem;background:#0f1620;border:1px solid #1e2a3a;border-radius:6px;height:100%">
                <div style="color:#6b7a99;font-size:0.6rem">현재가</div>
                <div style="font-size:1.1rem;color:{info['color']}">${price:,.2f}</div>
                <div style="font-size:0.7rem;color:{chg_color}">{chg_sign} {abs(price_chg):.2f}%</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            rsi_color = "#e05c5c" if rsi > 65 else "#e08c3c" if rsi > 50 else "#3ecf8e" if rsi < 35 else "#4fa3e0"
            st.markdown(f"""<div style="padding:0.8rem;background:#0f1620;border:1px solid #1e2a3a;border-radius:6px;text-align:center">
                <div style="color:#6b7a99;font-size:0.6rem">RSI({INDICATOR_PARAMS[t]['rsi_period']})</div>
                <div style="font-size:1.3rem;color:{rsi_color};font-family:'Cinzel',serif">{rsi:.0f}</div>
            </div>""", unsafe_allow_html=True)
        with col4:
            z = ind.get("z_score", 0)
            z_color = "#3ecf8e" if z < -1.5 else "#e05c5c" if z > 1.5 else "#c9a84c"
            st.markdown(f"""<div style="padding:0.8rem;background:#0f1620;border:1px solid #1e2a3a;border-radius:6px;text-align:center">
                <div style="color:#6b7a99;font-size:0.6rem">Z-Score</div>
                <div style="font-size:1.3rem;color:{z_color};font-family:'Cinzel',serif">{z:+.2f}</div>
            </div>""", unsafe_allow_html=True)
        with col5:
            alloc_color = "#3ecf8e" if alloc > 0 else "#6b7a99"
            st.markdown(f"""<div style="padding:0.8rem;background:#0f1620;border:1px solid #1e2a3a;border-radius:6px;text-align:center">
                <div style="color:#6b7a99;font-size:0.6rem">이번 달 매수</div>
                <div style="font-size:1.1rem;color:{alloc_color};font-family:'Cinzel',serif">${alloc:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with col6:
            st.markdown(f"""<div style="padding:0.8rem;background:#0f1620;border:1px solid #1e2a3a;border-radius:6px">
                <div style="color:#6b7a99;font-size:0.6rem">신호</div>
                <div style="font-size:0.75rem;color:#e8e6f0;margin-top:0.2rem">{sig.get('signal_text','')}</div>
            </div>""", unsafe_allow_html=True)

        # IREN ignition detail
        if t == "IREN" and sig.get("ignition_met", 0) > 0:
            ign = sig.get("ignition_conditions", {})
            ign_text = " · ".join([f"{'✅' if v else '❌'} {k}" for k, v in ign.items()])
            st.markdown(f'<div class="info-box">🔥 불타기 조건: {ign_text}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # NXE uranium detail
    st.markdown("---")
    u_color = "#e05c5c" if uranium_price > 82 else "#e08c3c" if uranium_price > 75 else "#3ecf8e" if uranium_price < 70 else "#c9a84c"
    st.markdown(f"""<div class="card">
        <div class="section-title">☢ 우라늄 가격 모니터</div>
        <div style="display:flex;gap:2rem;align-items:center">
            <div>
                <div style="color:#6b7a99;font-size:0.7rem">현재 우라늄 (U₃O₈)</div>
                <div style="font-family:'Cinzel',serif;font-size:2rem;color:{u_color}">${uranium_price:.1f}/lb</div>
            </div>
            <div style="flex:1">
                <div style="margin-bottom:0.5rem;font-size:0.75rem">
                    <span style="color:#e05c5c">■</span> &gt;$82 매수중단 &nbsp;
                    <span style="color:#e08c3c">■</span> $75-82 기본(1×) &nbsp;
                    <span style="color:#c9a84c">■</span> $70-75 2× &nbsp;
                    <span style="color:#3ecf8e">■</span> &lt;$70 3×
                </div>
                <div style="background:#1a2233;border-radius:4px;height:12px;position:relative">
                    <div style="position:absolute;left:{min((uranium_price-50)/80*100, 100):.0f}%;top:-2px;width:4px;height:16px;background:{u_color};border-radius:2px"></div>
                    <div style="position:absolute;left:{(82-50)/80*100:.0f}%;top:0;width:1px;height:12px;background:#e05c5c44"></div>
                    <div style="position:absolute;left:{(75-50)/80*100:.0f}%;top:0;width:1px;height:12px;background:#e08c3c44"></div>
                    <div style="position:absolute;left:{(70-50)/80*100:.0f}%;top:0;width:1px;height:12px;background:#c9a84c44"></div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:0.6rem;color:#6b7a99;margin-top:2px">
                    <span>$50</span><span>$70</span><span>$75</span><span>$82</span><span>$130</span>
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

# ════════════════════════════════
# TAB 2: 종목 분석
# ════════════════════════════════
with tabs[1]:
    selected = st.selectbox("종목 선택", list(TICKERS.keys()), format_func=lambda t: f"{t} — {TICKERS[t]['name']}")
    df = market_data.get(selected, pd.DataFrame())
    ind = indicators.get(selected, {})
    params = INDICATOR_PARAMS[selected]

    if not df.empty and ind:
        # Indicator grid
        metrics = [
            ("RSI", f"{ind.get('rsi',0):.1f}", f"기간 {params['rsi_period']}"),
            ("StochRSI K", f"{ind.get('stoch_k',0):.1f}", f"기간 {params['stoch_k']}/{params['stoch_d']}"),
            ("MACD Hist", f"{ind.get('macd_hist',0):+.3f}", f"({params['macd'][0]},{params['macd'][1]},{params['macd'][2]})"),
            ("Z-Score", f"{ind.get('z_score',0):+.2f}", "30일 기준"),
            ("ATR", f"{ind.get('atr',0):.2f}", f"기간 {params['atr_period']}"),
            ("ADX", f"{ind.get('adx',0):.1f}", f"기간 {params['adx_period']}"),
            ("SMA 80", f"${ind.get('sma80',0):,.2f}", "중기 추세"),
            ("SMA 200", f"${ind.get('sma200',0):,.2f}", "장기 추세"),
            ("거래량 배율", f"{ind.get('vol_spike',0):.1f}×", "vs 20일 평균"),
            ("1주 수익률", f"{ind.get('chg_1w',0):+.1f}%", "5거래일"),
        ]
        cols = st.columns(5)
        for i, (label, val, sub) in enumerate(metrics):
            with cols[i % 5]:
                st.markdown(f"""<div class="metric-box" style="margin-bottom:0.5rem">
                    <div class="metric-label">{label}</div>
                    <div style="font-size:1rem;color:{TICKERS[selected]['color']};font-family:'Cinzel',serif">{val}</div>
                    <div class="metric-sub">{sub}</div>
                </div>""", unsafe_allow_html=True)

        # Chart
        st.markdown("<br>", unsafe_allow_html=True)
        fig = make_price_chart(df, selected, ind)
        st.plotly_chart(fig, use_container_width=True)

        # Indicator summary table
        st.markdown('<div class="section-title">📋 지표 파라미터 설정</div>', unsafe_allow_html=True)
        param_df = pd.DataFrame([
            {"지표": "RSI", "설정값": str(params["rsi_period"]), "비고": "고변동 종목 20, GOOGL/IONQ 14"},
            {"지표": "StochRSI", "설정값": f"K={params['stoch_k']}, D={params['stoch_d']}", "비고": "비대칭 구조로 가짜신호 감소"},
            {"지표": "MACD", "설정값": f"({params['macd'][0]},{params['macd'][1]},{params['macd'][2]})", "비고": "AI종목 장기 추세 포착"},
            {"지표": "Bollinger", "설정값": f"20, σ={params['bb_std']}", "비고": "고변동 종목 2.5σ"},
            {"지표": "ATR", "설정값": str(params["atr_period"]), "비고": "변동성 과다 시 매수 중단"},
            {"지표": "ADX", "설정값": str(params["adx_period"]), "비고": "추세 강도 판단"},
        ])
        st.dataframe(param_df, use_container_width=True, hide_index=True)
    else:
        st.warning("데이터를 불러오는 중입니다. 잠시 후 다시 시도하세요.")

# ════════════════════════════════
# TAB 3: 이번 달 DCA
# ════════════════════════════════
with tabs[2]:
    st.markdown('<div class="section-title">💰 이번 달 DCA 배분 계획</div>', unsafe_allow_html=True)

    # Big allocation view
    total_alloc = sum(allocation.values())
    googl_extra = allocation.get("GOOGL", 0) - 600  # extra absorbed

    if googl_extra > 0:
        st.markdown(f'<div class="info-box">ℹ️ 고위험 종목 조건 미충족으로 GOOGL에 ${googl_extra:.0f} 추가 흡수 (총 ${allocation.get("GOOGL",0):,.0f})</div>', unsafe_allow_html=True)

    # Allocation bars
    for t, info in TICKERS.items():
        amt = allocation.get(t, 0)
        sig = signals.get(t, {})
        pct_of_budget = amt / MONTHLY_BUDGET * 100
        bar_color = info["color"]

        col1, col2, col3 = st.columns([2, 4, 2])
        with col1:
            st.markdown(f'<div style="font-family:Cinzel,serif;font-size:0.9rem;color:#e8e6f0;padding-top:0.5rem">{t}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div style="padding-top:0.6rem">
                <div style="background:#1a2233;border-radius:3px;height:8px">
                    <div style="width:{min(pct_of_budget,100):.0f}%;height:8px;background:{bar_color};border-radius:3px;opacity:{'0.9' if amt > 0 else '0.2'}"></div>
                </div>
            </div>""", unsafe_allow_html=True)
        with col3:
            if amt > 0:
                st.markdown(f'<div style="text-align:right;font-size:1rem;color:{bar_color};font-family:Cinzel,serif;padding-top:0.3rem">${amt:,.0f}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="text-align:right;font-size:0.8rem;color:#6b7a99;padding-top:0.5rem">— 매수 중단</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Detail table
    st.markdown('<div class="section-title">📋 종목별 상세 계획</div>', unsafe_allow_html=True)

    rows = []
    for t, info in TICKERS.items():
        sig = signals.get(t, {})
        amt = allocation.get(t, 0)
        price = current_prices.get(t, 0)
        shares = amt / price if price > 0 and amt > 0 else 0
        rows.append({
            "종목": t,
            "신호": sig.get("signal_text", ""),
            "배율": f"{sig.get('multiplier',0)}×",
            "배정액": f"${amt:,.0f}",
            "매수 주수": f"{shares:.4f} 주" if shares > 0 else "—",
            "현재가": f"${price:,.2f}",
        })

    df_plan = pd.DataFrame(rows)
    st.dataframe(df_plan, use_container_width=True, hide_index=True)

    # Monthly flow rules reminder
    st.markdown("---")
    st.markdown('<div class="section-title">📌 월별 DCA 운용 규칙</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="card">
<table>
<tr><th>단계</th><th>행동</th><th>비고</th></tr>
<tr><td>1단계</td><td>GOOGL $600 선매수</td><td>매달 고정, 신호 무관</td></tr>
<tr><td>2단계</td><td>IREN 신호 확인 → 배정</td><td>최우선 순위</td></tr>
<tr><td>3단계</td><td>MU 신호 확인 → 배정</td><td>2순위</td></tr>
<tr><td>4단계</td><td>NXE 우라늄 기준 → 배정</td><td>3순위</td></tr>
<tr><td>5단계</td><td>IONQ 신호 확인 → 배정</td><td>4순위</td></tr>
<tr><td>6단계</td><td>잔액 → GOOGL 추가 흡수</td><td>한 달 내 100% 집행</td></tr>
</table>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════
# TAB 4: 리밸런싱
# ════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-title">⚖ 분기별 리밸런싱 분석</div>', unsafe_allow_html=True)

    if rebal["total_value"] > 0:
        col1, col2 = st.columns([1, 1])

        with col1:
            # Pie chart
            st.markdown('<div class="section-title">현재 비중</div>', unsafe_allow_html=True)
            fig_pie = make_portfolio_pie(rebal["current_weights"], rebal["values"])
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Weight comparison
            st.markdown('<div class="section-title">비중 비교</div>', unsafe_allow_html=True)
            for t, info in TICKERS.items():
                cur = rebal["current_weights"].get(t, 0) * 100
                tgt = rebal["target_weights"].get(t, 0) * 100
                diff = cur - tgt
                diff_color = "#e05c5c" if abs(diff) > 5 else "#c9a84c" if abs(diff) > 2 else "#6b7a99"

                st.markdown(f"""<div style="margin-bottom:0.6rem">
                    <div style="display:flex;justify-content:space-between;font-size:0.75rem;margin-bottom:2px">
                        <span style="color:{info['color']}">{t}</span>
                        <span style="color:{diff_color}">{cur:.1f}% <span style="color:#6b7a99">/ 목표 {tgt:.0f}%</span> ({diff:+.1f}%)</span>
                    </div>
                    <div style="display:flex;gap:4px;height:8px">
                        <div style="width:{min(cur,100):.0f}%;background:{info['color']};border-radius:2px;opacity:0.9"></div>
                    </div>
                    <div style="background:#1e2a3a;height:2px;margin-top:1px">
                        <div style="width:{min(tgt,100):.0f}%;background:#1e2a3a44"></div>
                    </div>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        # Actions
        st.markdown('<div class="section-title">🚨 리밸런싱 액션 필요 항목</div>', unsafe_allow_html=True)

        if rebal["actions"]:
            for action in rebal["actions"]:
                if action["type"] == "TRIM":
                    st.markdown(f"""<div class="warning-box">
                        ⚠️ <b>{action['ticker']}</b> 비중 초과 — {action['reason']}<br>
                        → 초과분 <b>${action['amount']:,.0f}</b> 매도 후 분산 재배치
                    </div>""", unsafe_allow_html=True)
                elif action["type"] == "ROTATE":
                    st.markdown(f"""<div class="info-box">
                        🔄 <b>{action['ticker']}</b> 로테이션 — {action['reason']}<br>
                        → 초과분 <b>${action['amount']:,.0f}</b>를 IREN으로 이동
                    </div>""", unsafe_allow_html=True)
                elif action["type"] == "REBALANCE":
                    color_class = "success-box" if action.get("direction") == "BUY" else "warning-box"
                    st.markdown(f"""<div class="{color_class}">
                        {'📈' if action.get('direction')=='BUY' else '📉'} <b>{action['ticker']}</b> — {action['reason']}<br>
                        → {'추가 매수' if action.get('direction')=='BUY' else '일부 매도'} 약 <b>${action['amount']:,.0f}</b>
                    </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="success-box">✅ 현재 리밸런싱 불필요 — 모든 비중이 목표 범위 내</div>', unsafe_allow_html=True)

        # Weight table
        st.markdown("---")
        st.markdown('<div class="section-title">📊 포트폴리오 상세</div>', unsafe_allow_html=True)
        rows = []
        for t, info in TICKERS.items():
            h = portfolio["holdings"][t]
            cur_price = current_prices.get(t, 0)
            val = h["shares"] * cur_price
            avg = h["avg_cost"]
            pnl = (cur_price - avg) / avg * 100 if avg > 0 else 0
            rows.append({
                "종목": t,
                "보유 주수": f"{h['shares']:.4f}",
                "평균단가": f"${avg:,.2f}",
                "현재가": f"${cur_price:,.2f}",
                "평가액": f"${val:,.0f}",
                "수익률": f"{pnl:+.1f}%",
                "현재 비중": f"{rebal['current_weights'].get(t,0)*100:.1f}%",
                "목표 비중": f"{info['weight']*100:.0f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    else:
        st.markdown('<div class="info-box">📌 보유 주식을 입력하면 리밸런싱 분석이 활성화됩니다. 사이드바에서 입력하세요.</div>', unsafe_allow_html=True)

    # Rules reminder
    st.markdown("---")
    st.markdown('<div class="section-title">📋 리밸런싱 규칙 (3개월마다 1회)</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="card">
<table>
<tr><th>규칙</th><th>조건</th><th>액션</th></tr>
<tr><td>Rule 1</td><td>IREN 비중 > 50%</td><td>초과분 → GOOGL 50% / MU 30% / NXE 20% 분산</td></tr>
<tr><td>Rule 2</td><td>GOOGL 비중 > 40%</td><td>초과분 → IREN으로 로테이션</td></tr>
<tr><td>Rule 3</td><td>NXE 음봉 3개월 연속</td><td>NXE 비중 +5% 증가 (바닥 신호)</td></tr>
<tr><td>Rule 4</td><td>IONQ 비중 > 10%</td><td>초과분 → GOOGL로 이동</td></tr>
</table>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════
# TAB 5: 목표 추적
# ════════════════════════════════
with tabs[4]:
    st.markdown('<div class="section-title">🎯 $500,000 목표 추적</div>', unsafe_allow_html=True)

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-box card-gold">
            <div class="metric-label">현재 포트 가치</div>
            <div class="metric-value">${goal['total_value']:,.0f}</div>
            <div class="metric-sub">목표 $500,000</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">목표 달성률</div>
            <div class="metric-value" style="color:{'#3ecf8e' if goal['goal_pct']>50 else '#c9a84c'}">{goal['goal_pct']:.1f}%</div>
            <div class="metric-sub">{goal['elapsed_months']:.0f}개월 경과</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        pnl_color = "#3ecf8e" if goal['unrealized_pnl'] >= 0 else "#e05c5c"
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">평가 손익</div>
            <div class="metric-value" style="color:{pnl_color}">{goal['pnl_pct']:+.1f}%</div>
            <div class="metric-sub">${goal['unrealized_pnl']:+,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">총 투자금</div>
            <div class="metric-value" style="color:#4fa3e0">${goal['total_invested']:,.0f}</div>
            <div class="metric-sub">잔여 {goal['remaining_months']:.0f}개월</div>
        </div>""", unsafe_allow_html=True)

    # Goal progress bar
    st.markdown(f"""<div style="margin:1.5rem 0">
        <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:#6b7a99;margin-bottom:4px">
            <span>$0</span><span style="color:#c9a84c">${goal['total_value']:,.0f}</span><span>$500,000</span>
        </div>
        <div style="background:#1a2233;border-radius:6px;height:16px;position:relative">
            <div style="width:{min(goal['goal_pct'],100):.1f}%;height:16px;background:linear-gradient(90deg,#c9a84c,#f0d080);border-radius:6px;position:relative">
                <div style="position:absolute;right:-1px;top:-2px;width:4px;height:20px;background:#fff;border-radius:2px;opacity:0.8"></div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Projection chart
    st.markdown('<div class="section-title">📈 목표 달성 시뮬레이션</div>', unsafe_allow_html=True)

    months = list(range(0, 37))
    current_val = goal["total_value"]

    # Three scenarios
    def project(start, monthly, rate):
        vals = [start]
        for _ in range(36):
            vals.append(vals[-1] * (1 + rate) + monthly)
        return vals

    opt_vals = project(current_val, MONTHLY_BUDGET, 0.035)   # ~50% annual
    mid_vals = project(current_val, MONTHLY_BUDGET, 0.015)   # ~20% annual
    con_vals = project(current_val, MONTHLY_BUDGET, 0.003)   # ~4% annual

    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(x=months, y=opt_vals, name="낙관 (월 3.5%)",
                                   line=dict(color="#3ecf8e", width=2)))
    fig_proj.add_trace(go.Scatter(x=months, y=mid_vals, name="중립 (월 1.5%)",
                                   line=dict(color="#c9a84c", width=2)))
    fig_proj.add_trace(go.Scatter(x=months, y=con_vals, name="보수 (월 0.3%)",
                                   line=dict(color="#4fa3e0", width=2, dash="dot")))
    fig_proj.add_hline(y=500000, line_color="#e05c5c", line_dash="dash",
                        annotation_text="목표 $500K", annotation_font_color="#e05c5c")
    fig_proj.add_trace(go.Scatter(x=[0], y=[current_val], mode="markers",
                                   marker=dict(color="#fff", size=8), name="현재"))

    fig_proj.update_layout(
        height=350,
        paper_bgcolor="#0f1620",
        plot_bgcolor="#070a0f",
        font=dict(family="IBM Plex Mono", size=10, color="#6b7a99"),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(bgcolor="#0f1620", font=dict(size=10)),
        xaxis=dict(title="개월", gridcolor="#1e2a3a"),
        yaxis=dict(title="포트폴리오 가치 ($)", gridcolor="#1e2a3a",
                   tickformat="$,.0f"),
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    # Monthly investment needed
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    scenarios = [
        ("🐂 낙관 시나리오", opt_vals[-1], "#3ecf8e"),
        ("⚖ 중립 시나리오", mid_vals[-1], "#c9a84c"),
        ("🐻 보수 시나리오", con_vals[-1], "#4fa3e0"),
    ]
    for col, (label, final, color) in zip([col1, col2, col3], scenarios):
        with col:
            hit = "✅ 달성" if final >= 500000 else f"❌ ${final/500000*100:.0f}%"
            st.markdown(f"""<div class="metric-box">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color:{color}">${final:,.0f}</div>
                <div class="metric-sub">36개월 후 | {hit}</div>
            </div>""", unsafe_allow_html=True)

    # NXE 3-month trend (Rule 3 monitor)
    st.markdown("---")
    st.markdown('<div class="section-title">☢ NXE 3개월 연속 음봉 모니터 (Rule 3)</div>', unsafe_allow_html=True)
    nxe_df = market_data.get("NXE", pd.DataFrame())
    if not nxe_df.empty and len(nxe_df) >= 60:
        monthly_nxe = nxe_df["Close"].resample("ME").last().pct_change().tail(4)
        neg_streak = 0
        for r in monthly_nxe.iloc[1:].values:
            if r < 0:
                neg_streak += 1
            else:
                neg_streak = 0
        streak_color = "#e05c5c" if neg_streak >= 3 else "#c9a84c" if neg_streak >= 2 else "#6b7a99"
        st.markdown(f"""<div class="{'warning-box' if neg_streak >= 3 else 'card'}">
            {'🔥 <b>신이 준 바닥 시그널!</b> NXE 3개월 연속 음봉 — 비중 +5% 증가 검토' if neg_streak >= 3 else f'NXE 연속 음봉: <b style="color:{streak_color}">{neg_streak}개월</b> (3개월 충족 시 비중 +5% 신호)'}
        </div>""", unsafe_allow_html=True)
