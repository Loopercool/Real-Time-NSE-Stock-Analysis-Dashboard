import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from datetime import datetime

# Page config
st.set_page_config(page_title="TradingView Lite", layout="wide")
st.title("📈 TradingView Lite")
st.markdown("NSE stock analysis with candlestick, RSI, SMA, volume, and strategy meter")

# User input
ticker_input = st.text_input("Enter NSE stock symbol (e.g. TCS, INFY, RELIANCE, NIFTY)", "TCS").upper()

# ✅ Handle special index tickers like NIFTY
if ticker_input == "NIFTY":
    ticker = "^NSEI"
else:
    ticker = ticker_input + ".NS"

# 📅 Date picker
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime(2023, 1, 1))
with col2:
    end_date = st.date_input("End Date", datetime(2024, 1, 1))

if start_date >= end_date:
    st.error("⚠️ End date must be after start date.")
    st.stop()

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# 🔽 Fetch data
st.write(f"📥 Downloading data for `{ticker}`")
data = yf.download(ticker, start=start_date, end=end_date, group_by='ticker')

# 🧹 Flatten columns if needed
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(1)

# 🔍 Check OHLC
ohlc_cols = ['Open', 'High', 'Low', 'Close']
if not all(col in data.columns for col in ohlc_cols):
    st.error("Missing OHLC columns")
    st.stop()

data = data.dropna(subset=ohlc_cols)


# 📌 Support/Resistance detection
def find_support_resistance(df, window=10):
    highs, lows = df["High"], df["Low"]
    support, resistance = [], []
    for i in range(window, len(df) - window):
        if all(lows[i] < lows[i - j] and lows[i] < lows[i + j] for j in range(1, window)):
            support.append((df.index[i], lows[i]))
        if all(highs[i] > highs[i - j] and highs[i] > highs[i + j] for j in range(1, window)):
            resistance.append((df.index[i], highs[i]))
    return support, resistance

support_lvls, resistance_lvls = find_support_resistance(data)



# 📈 Custom SMA
data["SMA20"] = data["Close"].rolling(window=20).mean()
data["SMA50"] = data["Close"].rolling(window=50).mean()

# 📉 Custom RSI
delta = data["Close"].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
data["RSI"] = 100 - (100 / (1 + rs))

# 📊 Candlestick + SMA + Volume
st.subheader("📊 Candlestick with SMA + Volume")

fig = go.Figure()

# Candlestick
fig.add_trace(go.Candlestick(
    x=data.index,
    open=data["Open"],
    high=data["High"],
    low=data["Low"],
    close=data["Close"],
    name="Candlestick"
))

# SMA
fig.add_trace(go.Scatter(x=data.index, y=data["SMA20"], mode='lines', name='SMA 20', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=data.index, y=data["SMA50"], mode='lines', name='SMA 50', line=dict(color='blue')))

# Volume
fig.add_trace(go.Bar(x=data.index, y=data["Volume"], name="Volume", yaxis="y2", marker_color='rgba(180,180,180,0.2)'))

fig.update_layout(
    xaxis_rangeslider_visible=False,
    template="plotly_dark",
    yaxis=dict(title="Price"),
    yaxis2=dict(
        overlaying='y',
        side='right',
        showgrid=False,
        title='Volume',
        range=[0, data["Volume"].max() * 4]
    ),
    legend=dict(orientation="h", y=1.02),
)



# Draw support lines (last 3)
for dt, lvl in support_lvls[-3:]:
    fig.add_hline(y=lvl, line=dict(color="green", dash="dot"), 
                  annotation_text=f"Support {round(lvl, 2)}", 
                  annotation_position="bottom right")

# Draw resistance lines (last 3)
for dt, lvl in resistance_lvls[-3:]:
    fig.add_hline(y=lvl, line=dict(color="red", dash="dot"), 
                  annotation_text=f"Resistance {round(lvl, 2)}", 
                  annotation_position="top right")




st.plotly_chart(fig, use_container_width=True)

# 📉 RSI Chart
st.subheader("📉 RSI Chart")
rsi_fig = go.Figure()
rsi_fig.add_trace(go.Scatter(x=data.index, y=data["RSI"], name="RSI", line=dict(color="purple")))
rsi_fig.update_layout(yaxis=dict(range=[0, 100]), template="plotly_dark")
st.plotly_chart(rsi_fig, use_container_width=True)

# 📌 Buy Strength Meter
st.subheader("📌 Buy Strength Meter")

# ✅ Safe RSI fallback
if data["RSI"].dropna().empty:
    latest_rsi = 50  # Neutral fallback
else:
    latest_rsi = data["RSI"].dropna().iloc[-1]

# Safe SMA fallback
try:
    sma_diff = data["SMA20"].iloc[-1] - data["SMA50"].iloc[-1]
except:
    sma_diff = 0

score = 0
if latest_rsi < 30: score += 2
elif latest_rsi < 50: score += 1
if sma_diff > 0: score += 2
elif sma_diff > -5: score += 1

meter = "❌ Sell"
if score >= 4:
    meter = "🔥 Strong Buy"
elif score >= 3:
    meter = "✅ Buy"
elif score == 2:
    meter = "🤔 Hold"
elif score == 1:
    meter = "⚠️ Weak Hold"

st.markdown(f"### {meter}")






# 📘 Strategy Summary
st.markdown("### 📘 Strategy Summary")
st.write(f"""
- **RSI:** {round(latest_rsi, 2)} (Below 30 = oversold, Above 70 = overbought)
- **SMA20 vs SMA50 Difference:** {round(sma_diff, 2)}
- **Final Signal:** Based on trend and momentum, this stock is rated: **{meter}**
""")

# 🧠 Ensure return columns are available for AI logic
data["Daily Return"] = data["Close"].pct_change()
data["7D Return"] = data["Close"].pct_change(periods=7)
data["30D Return"] = data["Close"].pct_change(periods=30)

latest_close = data["Close"].iloc[-1]
return_1d = data["Daily Return"].iloc[-1] * 100 if not pd.isna(data["Daily Return"].iloc[-1]) else 0
return_7d = data["7D Return"].iloc[-1] * 100 if not pd.isna(data["7D Return"].iloc[-1]) else 0
return_30d = data["30D Return"].iloc[-1] * 100 if not pd.isna(data["30D Return"].iloc[-1]) else 0
volatility = data["Daily Return"].std() * 100
avg_volume = round(data["Volume"].rolling(14).mean().iloc[-1], 2)
vol_now = data["Volume"].iloc[-1]


# 🤖 AI-Powered Signal Generator
st.markdown("## 🤖 AI Buy/Sell Recommendations")

def get_intraday_signal(ret_1d, vol, vol_now, avg_vol):
    if ret_1d > 1 and vol_now > 1.5 * avg_vol:
        return "🔥 Buy (High Momentum)"
    elif ret_1d < -1 and vol_now > 1.5 * avg_vol:
        return "⚠️ Sell (High Drop)"
    else:
        return "🤔 Hold"

def get_short_term_signal(rsi, sma20, sma50, ret_7d):
    if rsi < 30:
        return "💰 Buy (Oversold)"
    elif sma20 > sma50 and ret_7d > 1:
        return "✅ Buy (Bullish Crossover)"
    elif rsi > 70 or ret_7d < -1:
        return "❌ Sell"
    else:
        return "🤔 Hold"

def get_long_term_signal(ret_30d, sma20, sma50, rsi):
    if ret_30d > 5 and sma20 > sma50 and rsi < 70:
        return "📈 Strong Buy (Uptrend)"
    elif ret_30d < -5 or rsi > 80:
        return "❌ Exit"
    else:
        return "🤔 Hold"

# Calculate required values
vol_now = data["Volume"].iloc[-1]

# Generate signals
intraday_signal = get_intraday_signal(return_1d, volatility, vol_now, avg_volume)
short_term_signal = get_short_term_signal(latest_rsi, data["SMA20"].iloc[-1], data["SMA50"].iloc[-1], return_7d)
long_term_signal = get_long_term_signal(return_30d, data["SMA20"].iloc[-1], data["SMA50"].iloc[-1], latest_rsi)

# Display AI Recommendations
st.markdown("### 🕒 Intraday Signal")
st.success(intraday_signal)

st.markdown("### 📅 Short-Term Signal (1–7 Days)")
st.success(short_term_signal)

st.markdown("### 📆 Long-Term Signal (30+ Days)")
st.success(long_term_signal)


# 🔹 Line charts: Closing Price & Returns
col1, col2 = st.columns(2)
with col1:
    st.subheader("🔹 Closing Price")
    st.line_chart(data["Close"])
with col2:
    st.subheader("🔹 Daily Returns")
    st.line_chart(data["Close"].pct_change().dropna())

# 📤 Download CSV
st.markdown("### 📤 Download Data")
csv = data.to_csv(index=True).encode('utf-8')
st.download_button(
    label="📄 Download CSV",
    data=csv,
    file_name=f"{ticker_input}_data.csv",
    mime='text/csv'
)
# ⬇️ Existing code stays unchanged above this line

# === Manually calculated indicators (no pandas_ta)
import numpy as np

# 1. Bollinger Bands
data["SMA20"] = data["Close"].rolling(window=20).mean()
data["BB_std"] = data["Close"].rolling(window=20).std()
data["BB_upper"] = data["SMA20"] + (2 * data["BB_std"])
data["BB_lower"] = data["SMA20"] - (2 * data["BB_std"])

# 2. MACD
ema12 = data["Close"].ewm(span=12, adjust=False).mean()
ema26 = data["Close"].ewm(span=26, adjust=False).mean()
data["MACD"] = ema12 - ema26
data["MACD_signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
data["MACD_hist"] = data["MACD"] - data["MACD_signal"]

# 3. RSI
delta = data["Close"].diff()
gain = np.where(delta > 0, delta, 0)
loss = np.where(delta < 0, -delta, 0)
avg_gain = pd.Series(gain).rolling(window=14).mean()
avg_loss = pd.Series(loss).rolling(window=14).mean()
rs = avg_gain / avg_loss
data["RSI"] = 100 - (100 / (1 + rs))

# Add this block at the BOTTOM of your current app.py

# 📊 Step 1: Add financial performance metrics
st.markdown("### 📈 Additional Metrics")

# Calculate % returns
data["Daily Return"] = data["Close"].pct_change()
data["7D Return"] = data["Close"].pct_change(periods=7)
data["30D Return"] = data["Close"].pct_change(periods=30)

# Latest values
latest_close = data["Close"].iloc[-1]
return_1d = data["Daily Return"].iloc[-1] * 100 if not pd.isna(data["Daily Return"].iloc[-1]) else 0
return_7d = data["7D Return"].iloc[-1] * 100 if not pd.isna(data["7D Return"].iloc[-1]) else 0
return_30d = data["30D Return"].iloc[-1] * 100 if not pd.isna(data["30D Return"].iloc[-1]) else 0
volatility = data["Daily Return"].std() * 100  # in %
avg_volume = round(data["Volume"].rolling(14).mean().iloc[-1], 2)

# Display in columns
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📉 1-Day Return (%)", f"{return_1d:.2f}%")
    st.metric("📈 7-Day Return (%)", f"{return_7d:.2f}%")
    st.metric("📈 30-Day Return (%)", f"{return_30d:.2f}%")
with col2:
    st.metric("📊 Volatility (Std Dev)", f"{volatility:.2f}%")
    st.metric("📊 Avg Vol (14D)", f"{avg_volume:,.0f}")
with col3:
    st.metric("💰 Latest Close", f"{latest_close:,.2f}")


import feedparser

st.markdown("## 📰 Latest News Headlines")

def get_news(ticker_name):
    rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker_name}&region=US&lang=en-US"
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        return None
    return feed.entries[:5]  # Get top 5 articles

# Get raw ticker (e.g., TCS instead of TCS.NS)
news_ticker = ticker_input if ticker_input != "NIFTY" else "NSEI"
news_items = get_news(news_ticker)

if news_items:
    for item in news_items:
        st.markdown(f"- [{item.title}]({item.link})")
else:
    st.info("No news found for this ticker.")


