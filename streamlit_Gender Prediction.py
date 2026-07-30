import json
import os
import re
import time
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

# 注入 UI CSS 样式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

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

    /* 电话内线呼叫卡片样式 */
    .call-card {
        background: #FFFFFF;
        border: 1px solid #B8965C;
        border-radius: 10px;
        padding: 16px;
        margin-top: 10px;
        box-shadow: 0 4px 15px rgba(184, 150, 92, 0.1);
    }

    .call-btn {
        display: inline-block;
        background-color: #B8965C;
        color: white !important;
        padding: 8px 16px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
        transition: all 0.2s ease;
    }

    .call-btn:hover {
        background-color: #967843;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 1. 顶部 Header
st.markdown("""
<div class="hotel-header">
    <div class="hotel-subtitle">WELCOMING YOU TO THE ULTIMATE LUXURY</div>
    <div class="hotel-title">THE GRAND APEX</div>
    <div class="gold-divider"></div>
    <div style="font-size: 12px; color: #666; font-style: italic;">
        "Excellence in Every Detail — Dedicated Virtual Concierge Desk"
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. 长方形 21:9 自动轮播 Banner 组件
# ==========================================
auto_slider_html = """
<!DOCTYPE html>
<html>
<head>
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: transparent; }
    
    .slider-container {
        position: relative;
        width: 100%;
        height: 220px;
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

    .slide.active { opacity: 1; }

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
    <div class="slide active" style="background-image: url('https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=80');">
        <div class="slide-overlay">
            <div class="slide-title">👑 Grand Apex Penthouse Suite</div>
            <div class="slide-desc">Panoramic skyline views with private butler service.</div>
        </div>
    </div>
    <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=80');">
        <div class="slide-overlay">
            <div class="slide-title">🏊 Infinity Sky Pool & Spa</div>
            <div class="slide-desc">Heated rooftop pool overlooking the heart of the city.</div>
        </div>
    </div>
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

    setInterval(nextSlide, 3500);
</script>

</body>
</html>
"""

components.html(auto_slider_html, height=230)
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 3. 侧边栏服务面板与【一键内部电话 Quick Call】
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏨 GUEST ESSENTIALS</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-card">
        <p style="margin:0; font-size:12px; color:#4A4A4A;"><b>🕒 Check-in:</b> 15:00 PM</p>
        <p style="margin:4px 0 0 0; font-size:12px; color:#4A4A4A;"><b>🕚 Check-out:</b> 12:00 PM</p>
        <p style="margin:4px 0 0 0; font-size:12px; color:#4A4A4A;"><b>📞 Direct In-Room Dial:</b> Press '0'</p>
    </div>
    """, unsafe_allow_html=True)

    # 快捷内部呼叫专区
    st.markdown('<div class="sidebar-title">📞 DIRECT INTERNAL CALL</div>', unsafe_allow_html=True)
    dept = st.selectbox("Select Department:", ["Front Desk (Ext 0)", "Private Butler (Ext 801)", "Housekeeping (Ext 802)", "In-Room Dining (Ext 803)"])
    if st.button("📞 Call Department Now", use_container_width=True):
        st.toast(f"📞 Connecting you to {dept}... Please pick up your in-room phone.")

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Greetings! It is my absolute pleasure to welcome you to The Grand Apex. How may I assist your stay today?"}
        ]
        st.rerun()

# ==========================================
# 4. 实时天气响应
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
                if code in [0, 1]: return "☀️ Clear & Sunny"
                elif code in [2, 3]: return "⛅ Light Clouds"
                elif code in [45, 48]: return "🌫️ Mist & Fog"
                elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95]: return "🌧️ Gentle Rain"
                return "🌤️ Pleasant"

            current = data.get("current_weather", {})
            curr_temp = current.get("temperature", "N/A")
            curr_code = current.get("weathercode", 0)
            
            daily = data.get("daily", {})
            dates = daily.get("time", ["Today", "Tomorrow", "Day After"])
            max_temps = daily.get("temperature_2m_max", [0, 0, 0])
            min_temps = daily.get("temperature_2m_min", [0, 0, 0])

            reply = (
                f"🌤️ **Grand Apex Advisory Weather Service**\n\n"
                f"It is currently **{curr_temp}°C** with **{parse_wmo(curr_code)}** over the resort grounds.\n\n"
                f"**3-Day Horizon:**\n"
                f"• **Today ({dates[0]})**: {min_temps[0]}°C to {max_temps[0]}°C\n"
                f"• **Tomorrow ({dates[1]})**: {min_temps[1]}°C to {max_temps[1]}°C\n"
                f"• **Day After ({dates[2]})**: {min_temps[2]}°C to {max_temps[2]}°C\n\n"
                f"🌂 *Should you wish to step out for sightseeing, luxury umbrellas and chauffeur-driven limousines are available at the Concierge Desk.*"
            )
            return reply
        else:
            return "☀️ The weather around Grand Apex is delightfully warm. Please let me know if you would like me to reserve an outdoor table for lunch."
    except Exception:
        return "☀️ Weather forecast updated: Mild and suitable for local exploration. May I reserve a table at our Sky Garden Lounge for you?"

# ==========================================
# 5. Internal Call（内部呼叫）专用卡片生成器
# ==========================================
def render_internal_call_card():
    return """
📞 **Grand Apex Internal Communications Desk**

I can connect you directly with our specialized hotel departments. Please choose an option below or pick up your in-room landline phone:

<div class="call-card">
    <div style="font-weight:600; font-size:14px; color:#1A1A1A;">🛎️ Grand Concierge & Front Desk</div>
    <div style="font-size:12px; color:#666;">For immediate check-in, check-out, or room key requests.</div>
    <a href="tel:0" class="call-btn">📞 Dial Extension '0'</a>
</div>

<div class="call-card">
    <div style="font-weight:600; font-size:14px; color:#1A1A1A;">🤵 Executive Butler Service</div>
    <div style="font-size:12px; color:#666;">For luggage unpacking, shoe shine, or VIP room preferences.</div>
    <a href="tel:801" class="call-btn">📞 Dial Extension '801'</a>
</div>

<div class="call-card">
    <div style="font-weight:600; font-size:14px; color:#1A1A1A;">🧹 Housekeeping & Amenities</div>
    <div style="font-size:12px; color:#666;">For extra towels, pillow menu, or room cleaning service.</div>
    <a href="tel:802" class="call-btn">📞 Dial Extension '802'</a>
</div>
"""

# ==========================================
# 6. 模型训练与高级话术映射（加入 Internal Call 识别）
# ==========================================
def clean_text(text):
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s\u4e00-\u9fa5]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

LUXURY_RESPONSES = {
    "greet": "Greetings! It is my absolute pleasure to welcome you to The Grand Apex Resort & Spa. How may I be of service to you today?",
    "ask_wifi": "📶 **High-Speed Complimentary Wi-Fi**\n\nPlease select the network **`GrandApex_Guest`**. No password is required—simply enter your Room Number and Last Name on the login page.\n\n*If you require high-bandwidth access for video conferencing, our IT Butler is available 24/7 by dialing '0'.*",
    
    # 确认这一段在你的代码里！
    "ask_services": (
        "✨ **Welcome to Exceptional Hospitality at The Grand Apex**\n\n"
        "It is our privilege to provide a wide range of world-class amenities and personalized services during your stay:\n\n"
        "🍷 **Gastronomy & Dining**\n"
        "• 24-Hour In-Room Gourmet Dining\n"
        "• Michelin-Starred Fine Dining & Sky Garden Bar\n\n"
        "🧖‍♀️ **Wellness & Leisure**\n"
        "• Apex Executive Spa & Thermal Suites (Floor 5)\n"
        "• Heated Rooftop Infinity Sky Pool & Cabanas\n"
        "• 24/7 Technogym Fitness Suite\n\n"
        "🛎️ **Personalized Guest Care**\n"
        "• Executive Butler & Express Pressing Service\n"
        "• Private Airport Limousine Transfer\n"
        "• Direct In-Room Concierge Extension\n\n"
        "💡 *May I assist you with reserving a spa appointment, booking a restaurant table, or arranging transport?*"
    ),
    
    "ask_breakfast": "🥂 **Michelin-Star Breakfast Service**\n...",
    # ... 其余项保持不变
}
@st.cache_resource
def load_and_train_model():
    dataset_file = 'dataset.json'
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {"intents": []}

    X, y = [], []
    for intent in data.get('intents', []):
        tag = intent.get('tag')
        for pattern in intent.get('patterns', []):
            cleaned_pattern = clean_text(pattern)
            if cleaned_pattern:
                X.append(cleaned_pattern)
                y.append(tag)

    # 1. 显式补充 Internal Call 样本
    call_patterns = ["call front desk", "call butler", "internal call", "phone number", "contact housekeeping", "call hotel", "dial front desk", "phone front desk", "打电话", "联系前台", "呼叫管家", "打给前台", "内线电话"]
    for p in call_patterns:
        X.append(clean_text(p))
        y.append("internal_call")

    # 2. 【关键修正】显式强补充 ask_services 的训练样本！
    service_patterns = [
        "what services do you have", "what services", "hotel services", "services", 
        "what amenities are available", "amenities", "what can I do at this hotel", 
        "hotel facilities", "list your services", "what do you offer", "facilities",
        "有什么服务", "酒店有什么设施", "你们提供什么服务", "服务项目"
    ]
    for p in service_patterns:
        X.append(clean_text(p))
        y.append("ask_services")

    if not X:
        X = ["hi", "wifi", "weather", "breakfast", "spa", "checkin", "call front desk", "services"]
        y = ["greet", "ask_wifi", "ask_weather", "ask_breakfast", "ask_spa", "ask_checkin", "internal_call", "ask_services"]

    union = FeatureUnion([
        ('word_tf', TfidfVectorizer(ngram_range=(1, 3), token_pattern=r'\S+')),
        ('char_tf', TfidfVectorizer(ngram_range=(2, 4), analyzer='char_wb'))
    ])
    
    model = make_pipeline(union, LogisticRegression(C=5.0))
    model.fit(X, y)
    return model

# ==========================================
# 7. 对话渲染与逻辑触发
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Greetings! It is my absolute pleasure to welcome you to The Grand Apex Resort & Spa. How may I assist your stay today?"}
    ]

def get_bot_response(user_input):
    cleaned_input = clean_text(user_input)
    if not cleaned_input:
        return "It would be my delight to assist you. Please feel free to ask about our suites, spa, fine dining, or guest services."
        
    probs = model.predict_proba([cleaned_input])[0]
    max_idx = np.argmax(probs)
    confidence = probs[max_idx]
    predicted_tag = model.classes_[max_idx]
    
    if confidence < 0.18:
        return (
            "I apologize, but I want to ensure you receive the most precise assistance. "
            "Could you please clarify if your query pertains to **Wi-Fi**, **Breakfast & Dining**, **Spa Reservations**, or **Check-in/Out**?\n\n"
            "Alternatively, you may press **'0'** on your room telephone to speak directly with our Duty Manager."
        )
    
    if predicted_tag == "ask_weather":
        return get_realtime_weather()

    if predicted_tag == "internal_call":
        return render_internal_call_card()

    return LUXURY_RESPONSES.get(predicted_tag, "Thank you for bringing this to my attention. Our Concierge Desk is entirely at your service.")

# 渲染聊天记录
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Ask about Wi-Fi, Breakfast, Spa, Internal Call, or Weather..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = get_bot_response(prompt)
        
        # 判断是否包含 HTML (如 internal_call 卡片)，如果是 HTML 就直接渲染，不走打字机效果
        if "<div class=" in full_response:
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
        else:
            typed_text = ""
            for chunk in full_response.split(" "):
                typed_text += chunk + " "
                time.sleep(0.02)
                message_placeholder.markdown(typed_text + "▌")
            message_placeholder.markdown(full_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})
