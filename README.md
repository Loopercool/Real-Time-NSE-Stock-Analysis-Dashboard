# 📈 Real-Time NSE Stock Analysis Dashboard

An all-in-one stock analysis web app for Indian equities (NSE) — built using **Streamlit**, **Plotly**, and **yfinance**.  
It visualizes technical indicators, trend signals, news headlines, and buy/sell recommendations to help traders make smarter decisions.

---

## 🚀 Features

- 📊 **Candlestick Chart** with Volume
- 🧠 **Buy/Sell Recommendations** (Intraday, Short-Term, Long-Term)
- 📈 **Indicators**: RSI, SMA (20 & 50), MACD, Bollinger Bands
- 🟩 **Support & Resistance** detection (auto-calculated)
- 📉 **Returns, Volatility & Volume Stats**
- 📰 **Live Stock News** from Yahoo Finance
- 📥 Export processed data as CSV

---

## 🔧 How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Real-Time-NSE-Stock-Analysis-Dashboard.git
cd Real-Time-NSE-Stock-Analysis-Dashboard

# 2. (Optional) Create a virtual environment
python -m venv venv
venv\Scripts\activate  # For Windows
# OR
source venv/bin/activate  # For macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
