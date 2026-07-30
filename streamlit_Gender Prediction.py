import json
import os
import re
import requests
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, FeatureUnion

# ==========================================
# 1. 页面基本配置与 5 星级奢华米白配色样式
# ==========================================
st.set_page_config(
    page_title="The Grand Apex Resort & Spa | Virtual Concierge",
    page_icon="👑",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 注入高奢米白/香槟金 UI CSS 样式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

    /* 全局背景：优雅温暖的米白色渐变 */
    .stApp {
        background: linear-gradient(180deg, #FDFBF7 0%, #F4EFE6 100%);
        color: #2C2A29;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* 顶部 Header 区域 */
    .hotel-header {
        text-align: center;
        padding: 24px 20px 16px 20px;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(184, 150, 92, 0.25);
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
    }

    .hotel-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 32px;
        font-weight: 700;
        letter-spacing: 4px;
        color: #1A1A1A;
        margin-bottom: 2px;
        text-transform: uppercase;
    }

    .hotel-subtitle {
        font-size: 11px;
        letter-spacing: 3px;
        color: #B8965C;
        text-transform: uppercase;
        font-weight: 600;
    }

    .gold-divider {
        height: 1px;
        width: 60px;
        background: #B8965C;
        margin: 10px auto;
        opacity: 0.6;
    }

    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background-color: #FAFAFC !important;
        border-right: 1px solid rgba(184, 150, 92, 0.15);
    }

    .sidebar-card {
        background: #FFFFFF;
        border: 1px solid rgba(184, 150, 92, 0.2);
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }

    .sidebar-title {
        font-family: 'Cormorant Garamond', serif;
        color: #B8965C;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    /* 对话气泡美化 */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(184, 150, 92, 0.15) !important;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    }

    /* 隐藏默认 Header & Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 1. 顶部 Header 渲染
st.markdown("""
<div class="hotel-header">
    <div class="hotel-subtitle">WELCOMING YOU TO THE ULTIMATE LUXURY</div>
    <div class="hotel-title">THE GRAND APEX</div>
    <div class="gold-divider"></div>
    <div style="font-size: 12px; color: #666; font-style: italic;">
        "Excellence in Every Detail — Dedicated Concierge Service"
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. 长方形自动轮播广告（HTML5/JS Component）
# ==========================================
auto_slider_html = """
<!DOCTYPE html>
<html>
<head>
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: transparent; }
    
    /* 长方形轮播卡片容器 (21:9 比例) */
    .slider-container {
        position: relative;
        width: 100%;
        height: 220px; /* 控制极佳的长方形高度 */
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        border: 1px solid rgba(184, 150, 92, 0.3);
    }

    .slide {
        position: absolute;
        width: 100%;
        height: 100%;
        opacity: 0;
        transition: opacity 1s ease-in-out;
        background-size: cover;
        background-position: center;
    }

    .slide.active {
        opacity: 1;
    }

    /* 图片上的半透明暗色遮罩与文本 */
    .slide-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 20px;
        background: linear-gradient(to top, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0) 100%);
        color: #ffffff;
    }

    .slide-title {
        font-size: 18px;
        font-weight: 600;
        letter-spacing: 1px;
        margin-bottom: 4px;
        color: #FDFBF7;
    }

    .slide-desc {
        font-size: 12px;
        color: #D1C7BD;
        font-weight: 300;
    }

    /* 底部圆点指示器 */
    .dots-container {
        position: absolute;
        bottom: 12px;
        right: 20px;
        display: flex;
        gap: 6px;
    }

    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: rgba(255,255,255,0.4);
        transition: all 0.3s ease;
    }

    .dot.active {
        background: #B8965C;
        width: 20px;
        border-radius: 10px;
    }
</style>
</head>
<body>

<div class="slider-container">
    <!-- Slide 1 -->
    <div class="slide active" style="background-image: url('https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80');">
        <div class="slide-overlay">
            <div class="slide-title">👑 Royal Apex Penthouse Suite</div>
            <div class="slide-desc">Panoramic skyline views with private butler service.</div>
        </div>
    </div>
    <!-- Slide 2 -->
    <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80');">
        <div class="slide-overlay">
            <div class="slide-title">🏊 Infinity Sky Pool & Spa</div>
            <div class="slide-desc">Heated rooftop pool overlooking the heart of the city.</div>
        </div>
    </div>
    <!-- Slide 3 -->
    <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?auto=format&fit=crop&w=1200&q=80');">
        <div class="slide-overlay">
            <div class="slide-title">🍽️ Michelin Three-Star Dining</div>
            <div class="slide-desc">Exquisite culinary creations curated by Master Chefs.</div>
        </div>
    </div>

    <div class="dots-container">
        <div class="dot active"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    </div>
</div>

<script>
    let currentSlide = 0;
    const slides = document.querySelectorAll('.slide');
    const dots = document.querySelectorAll('.dot');
    const totalSlides = slides.length;

    function showSlide(index) {
        slides.forEach(s => s.classList.remove('active'));
        dots.forEach(d => d.classList.remove('active'));
        
        slides[index].classList.add('active');
        dots[index].classList.add('active');
    }

    function nextSlide() {
        currentSlide = (currentSlide + 1) % totalSlides;
        showSlide(currentSlide);
    }

    // 每 3.5 秒自动平滑切换 Slide
    setInterval(nextSlide, 3500);
</script>

</body>
</html>
"""

# 渲染自定义 HTML5/JS 组件（设置高度为 230px）
components.html(auto_slider_html, height=230)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 3. 侧边栏 (Sidebar) 5星级酒店服务信息
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏨 GUEST ESSENTIALS</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-card">
        <p style="margin:0; font-size:12px; color:#4A4A4A;"><b>🕒 Check-in:</b> 15:00 PM</p>
        <p style="margin:4px 0 0 0; font-size:12px; color:#4A4A4A;"><b>🕚 Check-out:</b> 12:00 PM</p>
        <p style="margin:4px 0 0 0; font-size:12px; color:#4A4A4A;"><b>📞 Concierge:</b> Dial '0'</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-title">💎 VIP PREMIER SERVICES</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-card">
        <p style="margin:0; font-size:12px; color:#4A4A4A;">• 24/7 In-Room Fine Dining</p>
        <p style="margin:4px 0 0 0; font-size:12px; color:#4A4A4A;">• Executive Spa & Sauna Retreat</p>
        <p style="margin:4px 0 0 0; font-size:12px; color:#4A4A4A;">• Private Airport Limousine Transfer</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Greetings! I am your Grand Apex Virtual Concierge. How may I assist your stay today?"}
        ]
        st.rerun()

# ==========================================
# 4. 动态天气 API 获取函数
# ==========================================
def get_realtime_weather():
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            "latitude=3.139&longitude=101.6869&"
            "current_weather=true&"
            "daily=weathercode,temperature_2m_max,temperature_2m_min&"
            "timezone=auto"
        )
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            
            def parse_wmo(code):
                if code in [0, 1]: return "☀️ Clear Skies"
                elif code in [2, 3]: return "⛅ Partly Cloudy"
                elif code in [45, 48]: return "🌫️ Foggy"
                elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95]: return "🌧️ Showers / Rain"
                return "🌤️ Pleasant"

            current = data.get("current_weather", {})
            curr_temp = current.get("temperature", "N/A")
            curr_code = current.get("weathercode", 0)
            
            daily = data.get("daily", {})
            dates = daily.get("time", ["Today", "Tomorrow", "Day After"])
            codes = daily.get("weathercode", [0, 0, 0])
            max_temps = daily.get("temperature_2m_max", [0, 0, 0])
            min_temps = daily.get("temperature_2m_min", [0, 0, 0])

            reply = (
                f"🌤️ **Grand Apex Concierge Weather Desk**\n\n"
                f"📌 **Current Status**: {parse_wmo(curr_code)} | **Temperature**: {curr_temp}°C\n\n"
                f"• **Today ({dates[0]})**: {parse_wmo(codes[0])} | 🌡️ {min_temps[0]}°C to {max_temps[0]}°C\n"
                f"• **Tomorrow ({dates[1]})**: {parse_wmo(codes[1])} | 🌡️ {min_temps[1]}°C to {max_temps[1]}°C\n"
                f"• **Day After ({dates[2]})**: {parse_wmo(codes[2])} | 🌡️ {min_temps[2]}°C to {max_temps[2]}°C\n\n"
                f"💼 *Complimentary luxury umbrellas are available at the Grand Concierge Desk upon request.*"
            )
            return reply
        else:
            return "☀️ The current climate at Grand Apex is pleasantly warm (28°C - 32°C). Please feel free to reach out to Concierge for further assistance."
    except Exception as e:
        return f"☀️ Currently pleasant and suitable for local exploration."

# ==========================================
# 5. 文本清洗与模型训练逻辑
# ==========================================
def clean_text(text):
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s\u4e00-\u9fa5]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

@st.cache_resource
def load_and_train_model():
    dataset_file = 'dataset.json'
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        data = {"intents": []}

    X, y = [], []
    responses_map = {}
    
    for intent in data.get('intents', []):
        tag = intent.get('tag')
        responses = intent.get('responses', [""])
        responses_map[tag] = responses[0] if responses else "Allow us to check this for you."
        
        for pattern in intent.get('patterns', []):
            cleaned_pattern = clean_text(pattern)
            if cleaned_pattern:
                X.append(cleaned_pattern)
                y.append(tag)

    if not X:
        X = ["hi", "wifi", "weather"]
        y = ["greet", "ask_wifi", "ask_weather"]
        responses_map = {
            "greet": "Welcome to The Grand Apex Resort.",
            "ask_wifi": "Wi-Fi: GrandApex_Guest",
            "ask_weather": "API_WEATHER"
        }

    union = FeatureUnion([
        ('word_tf', TfidfVectorizer(ngram_range=(1, 3), token_pattern=r'\S+')),
        ('char_tf', TfidfVectorizer(ngram_range=(2, 4), analyzer='char_wb'))
    ])
    
    model = make_pipeline(union, LogisticRegression(C=5.0))
    model.fit(X, y)
    return model, responses_map

model, responses_map = load_and_train_model()

# ==========================================
# 6. Session State 与预测逻辑
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Greetings! I am your Grand Apex Virtual Concierge. How may I be of service to you today?"}
    ]

if "last_intent" not in st.session_state:
    st.session_state.last_intent = None

def get_bot_response(user_input):
    cleaned_input = clean_text(user_input)
    if not cleaned_input:
        return "Please feel free to ask any question regarding our amenities or services."
        
    probs = model.predict_proba([cleaned_input])[0]
    max_idx = np.argmax(probs)
    confidence = probs[max_idx]
    predicted_tag = model.classes_[max_idx]
    
    if confidence < 0.18:
        return "I apologize, but I did not quite catch that. Would you like information regarding Check-in/Out, High-Speed Wi-Fi, Breakfast, or Weather Forecasts? You may also press '0' on your room phone to connect with Front Desk."
    
    st.session_state.last_intent = predicted_tag

    if predicted_tag == "ask_weather":
        return get_realtime_weather()
        
    if predicted_tag == "ask_wifi_steps" and st.session_state.last_intent != "ask_wifi":
        return responses_map.get("ask_wifi_steps", "May I confirm if you require step-by-step guidance for our Wi-Fi connection?")

    return responses_map.get(predicted_tag, "Thank you for asking. Our team is at your service.")

# ==========================================
# 7. 对话界面渲染
# ==========================================
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask about Wi-Fi, Breakfast, Spa, Check-in, or Weather..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    bot_reply = get_bot_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.chat_message("assistant").write(bot_reply)
