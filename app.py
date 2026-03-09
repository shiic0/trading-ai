import streamlit as st
import yfinance as yf
import anthropic
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# 1. إعدادات المنصة الاحترافية
st.set_page_config(page_title="نظام التحليل الاستراتيجي الذكي", layout="wide")
st.title("🛡️ منصة الاستشارة المالية المتكاملة")
st.markdown("---")

# 2. جلب المفتاح السري من Streamlit Secrets
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    st.error("⚠️ خطأ: المفتاح السري (ANTHROPIC_API_KEY) غير موجود في إعدادات Secrets.")
    st.stop()

# 3. واجهة المدخلات
col_input1, col_input2 = st.columns([2, 1])
with col_input1:
    symbol = st.text_input("🔍 أدخل رمز السهم (مثال: 1120.SR للراجحي أو 2222.SR لأرامكو)", value="1120.SR")
with col_input2:
    period = st.selectbox("📅 الفترة الزمنية للتحليل", options=['6mo', '1y', '2y'], index=0)

if st.button("بدء التحليل الاستراتيجي العميق 🚀"):
    try:
        # 4. جلب البيانات وحل مشكلة التنسيق الجديد لـ yfinance
        with st.spinner('جاري سحب بيانات السوق...'):
            df = yf.download(symbol, period=period, interval="1d")
            
            # معالجة مشكلة MultiIndex في الأعمدة (حل مشكلة لا توجد بيانات)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

        # التحقق من صحة البيانات
        if df.empty or len(df) < 20:
            st.warning(f"⚠️ تعذر العثور على بيانات كافية للرمز {symbol}. تأكد من إضافة .SR للأسهم السعودية.")
            st.stop()

        # 5. حساب المؤشرات الفنية المتقدمة
        # أ- مؤشر القوة النسبية (RSI)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / loss)))

        # ب- المتوسطات المتحركة الأسية (EMA) للترند
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

        # 6. رسم الشارت الاحترافي (3 مستويات)
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.5, 0.2, 0.3],
                           subplot_titles=("حركة السعر والترند", "مؤشر الزخم (RSI)", "حجم التداول والسيولة"))

        # المستوى 1: الشموع والترند
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                      low=df['Low'], close=df['Close'], name='السعر'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='EMA 20 (سريع)', line=dict(color='yellow', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA 50 (بطيء)', line=dict(color='cyan', width=1)), row=1, col=1)

        # المستوى 2: RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='magenta')), row=2, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, line_width=0, row=2, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, line_width=0, row=2, col=1)

        # المستوى 3: السيولة (Volume)
        bar_colors = ['red' if row['Open'] > row['Close'] else 'green' for _, row in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='السيولة', marker_color=bar_colors), row=3, col=1)

        fig.update_layout(height=900, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_view=True)

        # 7. ذكاء Claude AI للاستشارة المالية
        client = anthropic.Anthropic(api_key=api_key)
        last_price = float(df['Close'].iloc[-1])
        rsi_val = float(df['RSI'].iloc[-1])
        
        prompt = f"""
        بصفتك مستشاراً مالياً محترفاً، حلل سهم {symbol} بناءً على البيانات التالية:
        - السعر الحالي: {last_price:.2f}
        - مؤشر القوة النسبية (RSI): {rsi_val:.2f}
        - حالة المتوسطات: EMA20={df['EMA20'].iloc[-1]:.2f}, EMA50={df['EMA50'].iloc[-1]:.2f}
        
        المطلوب تقرير استشاري يتضمن:
        1. تقييم الاتجاه العام (هل هناك اختراق أو كسر؟).
        2. نقاط الدخول المثالية (Entry Points).
        3. أهداف البيع القريبة والبعيدة.
        4. نقطة وقف الخسارة (Stop Loss) الصارمة.
        5. التوصية النهائية (شراء / بيع / مراقبة) مع التبرير.
        الرد يكون باللغة العربية بأسلوب احترافي.
        """

        with st.spinner('جاري صياغة الاستشارة المالية...'):
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            st.markdown("### 📋 التقرير المالي والاستشارة")
            st.success(message.content[0].text)

    except Exception as e:
        st.error(f"❌ حدث خطأ غير متوقع: {str(e)}")
