import streamlit as st
import yfinance as yf
import anthropic
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# إعدادات النظام الاحترافي
st.set_page_config(page_title="منصة التحليل الفني الذكية", layout="wide")
st.title("🛡️ نظام الاستشارة المالية المتكامل (التحليل الذكي)")

# جلب المفتاح
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    st.error("⚠️ خطأ: المفتاح غير موجود في Secrets.")
    st.stop()

# مدخلات ذكية
col_in1, col_in2 = st.columns([3, 1])
with col_in1:
    symbol = st.text_input("🔍 رمز السهم (مثال: 1120.SR للراجحي أو 2222.SR لأرامكو)", value="1120.SR")
with col_in2:
    period = st.selectbox("📅 المدى الزمني للتحليل", options=['6mo', '1y', '2y'], index=0)

if st.button("بدء التحليل الاستراتيجي 🚀"):
    try:
        data = yf.download(symbol, period=period)
        if not data.empty:
            # --- 1. حساب المؤشرات المتقدمة ---
            # RSI 14
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            data['RSI'] = 100 - (100 / (1 + (gain / loss)))

            # المتوسطات الأسية (EMA) للتقاطعات الذهبية
            data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
            data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()

            # --- 2. رسم الشارت الاحترافي (4 مستويات) ---
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.5, 0.2, 0.3],
                               subplot_titles=("حركة السعر والترند", "الزخم (RSI)", "حجم التداول (Volume)"))

            # أ- الشموع + المتوسطات الأسية
            fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], 
                          low=data['Low'], close=data['Close'], name='السعر'), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['EMA20'], name='EMA 20 (سريع)', line=dict(color='yellow', width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], name='EMA 50 (بطيء)', line=dict(color='cyan', width=1.5)), row=1, col=1)

            # ب- RSI مع مناطق التشبع
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='magenta')), row=2, col=1)
            fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0, row=2, col=1)
            fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0, row=2, col=1)

            # ج- حجم التداول (Volume)
            colors = ['red' if row['Open'] > row['Close'] else 'green' for index, row in data.iterrows()]
            fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='السيولة', marker_color=colors), row=3, col=1)

            fig.update_layout(height=900, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_view=True)

            # --- 3. استشارة Claude كخبير استراتيجي ---
            client = anthropic.Anthropic(api_key=api_key)
            last_price = data['Close'].iloc[-1]
            rsi_now = data['RSI'].iloc[-1]
            vol_avg = data['Volume'].tail(10).mean()
            vol_now = data['Volume'].iloc[-1]

            strategy_prompt = f"""
            أنت الآن 'مستشار مالي معتمد'. حلل سهم {symbol} بناءً على هذه البيانات الرقمية:
            - السعر الحالي: {last_price:.2f}
            - RSI: {rsi_now:.2f}
            - تقاطع المتوسطات: EMA20 هو {data['EMA20'].iloc[-1]:.2f} و EMA50 هو {data['EMA50'].iloc[-1]:.2f}
            - السيولة: الحجم الحالي {vol_now} مقارنة بمتوسط {vol_avg:.0f}

            المطلوب تقرير استراتيجي شديد الجدية:
            1. **تقييم الاتجاه**: هل السهم في مسار صاعد حقيقي أم ارتداد وهمي؟
            2. **قراءة السيولة**: هل أحجام التداول تدعم الحركة السعرية الحالية؟
            3. **خطة العمل**: حدد نقطة الدخول (Entry)، الهدف الأول والثاني، ونقطة وقف الخسارة (SL) الصارمة.
            4. **الخلاصة**: (شراء / بيع / مراقبة) مع تبرير فني مبني على المؤشرات المذكورة.
            """

            with st.spinner('جاري صياغة التقرير الاستراتيجي...'):
                message = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": strategy_prompt}]
                )
                st.markdown("### 📋 التقرير الفني والاستشارة المالية")
                st.success(message.content[0].text)
    except Exception as e:
        st.error(f"حدث خطأ في النظام: {e}")
