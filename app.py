import streamlit as st
import yfinance as yf
import anthropic
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="نظام التحليل الاستراتيجي", layout="wide")
st.title("🛡️ منصة الاستشارة المالية الاحترافية")

# جلب المفتاح الآمن
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    st.error("⚠️ المفتاح غير موجود في Secrets.")
    st.stop()

symbol = st.text_input("🔍 رمز السهم (مثال: 1120.SR)", value="1120.SR")
period = st.selectbox("📅 المدى الزمني", options=['6mo', '1y'], index=0)

if st.button("تشغيل التحليل العميق 🚀"):
    try:
        # حل مشكلة الخطأ الذي ظهر في الصورة
        df = yf.download(symbol, period=period)
        
        if df.empty or len(df) < 10:
            st.error("❌ لا توجد بيانات كافية لهذا الرمز.")
        else:
            # 1. حساب المؤشرات (بناء النظام الذكي)
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            
            # Bollinger Bands (لقياس الانفجار السعري)
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['Std'] = df['Close'].rolling(window=20).std()
            df['Upper'] = df['MA20'] + (df['Std'] * 2)
            df['Lower'] = df['MA20'] - (df['Std'] * 2)

            # 2. رسم الشارت الثلاثي
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.6, 0.2, 0.2])

            # شارت الشموع والبولنجر
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='السعر'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], name='سقف السعر', line=dict(color='rgba(173, 216, 230, 0.4)')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], name='قاع السعر', line=dict(color='rgba(173, 216, 230, 0.4)')), row=1, col=1)

            # شارت RSI
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='orange')), row=2, col=1)
            
            # شارت السيولة
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='السيولة'), row=3, col=1)

            fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_view=True)

            # 3. الاستشارة المالية الذكية
            client = anthropic.Anthropic(api_key=api_key)
            current_price = float(df['Close'].iloc[-1])
            
            prompt = f"""
            كمحلل مالي خبير، حلل سهم {symbol} بالسعر {current_price:.2f}.
            بناءً على RSI ({df['RSI'].iloc[-1]:.2f}) والسيولة ونطاق بولنجر:
            1. ما هي 'نقطة الدخول' الدقيقة؟
            2. ما هو 'الهدف' الأول والثاني؟
            3. حدد 'وقف الخسارة' الذي لا يمكن التنازل عنه.
            4. قدم نصيحة استثمارية (شراء/بيع/انتظار) مع السبب.
            """

            with st.spinner('جاري استخلاص التوصية...'):
                msg = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                st.markdown("### 📋 التوصية الاستثمارية النهائية")
                st.info(msg.content[0].text)

    except Exception as e:
        st.error(f"حدث خطأ: {str(e)}")
