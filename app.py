import streamlit as st
import anthropic
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="محلل التداول الذكي", layout="wide")

# جلب المفتاح من الإعدادات الآمنة
api_key = st.secrets["ANTHROPIC_API_KEY"]

st.title("🚀 محلل التداول الذكي")

symbol = st.text_input("🔍 رمز السهم أو العملة (مثال: 2222.SR)", "2222.SR")
asset_type = st.selectbox("📂 النوع", ["سهم", "عملة رقمية"])
analyze_btn = st.button("تحليل الآن 🚀")

if analyze_btn:
    try:
        # جلب البيانات
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        
        # رسم الشارت
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        st.plotly_chart(fig)

        # تحليل Claude
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            system="أنت محلل مالي صارم. حلل البيانات وقدم أهدافاً دقيقة ووقف خسارة.",
            messages=[{"role": "user", "content": f"السعر الحالي لـ {symbol} هو {hist['Close'].iloc[-1]}. حلل الاتجاه."}]
        )
        st.success(response.content[0].text)
    except Exception as e:
        st.error(f"خطأ: تأكد من الرمز وإعدادات المفتاح.")
