import json
import os
import re
import requests
import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, FeatureUnion

# ==========================================
# 1. 页面基本配置与高级 5 星级奢华 CSS 样式
# ==========================================
st.set_page_config(
    page_title="The Royal Apex Hotel & Suites | Luxury Assistant",
    page_icon="👑",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 注入自定义高端奢华 CSS 样式 (Dark Gold & Champagne Luxury Theme)
st.markdown("""
<style>
    /* 全局背景与字体配置 */
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Plus+Jakarta+Sans:wght@300;400;600&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        color: #e6edf3;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* 顶部黑金奢华 Hero Header */
    .hotel-header {
        text-align: center;
        padding: 30px 20px 20px 20px;
        background: rgba(22, 27, 34, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 0 15px rgba(212, 175, 55, 0.08);
    }

    .hotel-title {
        font-family: 'Cinzel', serif;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 3px;
        background: linear-gradient(135deg, #FFF0C1 0%, #D4AF37 50%, #996515 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        text-transform: uppercase;
    }

    .hotel-subtitle {
        font-size: 13px;
        letter-spacing: 2px;
        color: #c9d1d9;
        text-transform: uppercase;
        font-weight: 300;
    }

    .gold-divider {
        height: 1px;
        width: 80px;
        background: linear-gradient(90deg, transparent, #D4AF37, transparent);
        margin: 12px auto;
    }

    /* 快捷功能卡片容器 (Quick Action Badges) */
    .badge-container {
        display: flex;
        justify-content: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }

    .quick-badge {
        background: rgba(212, 175, 55, 0.08);
        border: 1px solid rgba(212, 175, 55, 0.25);
        color: #f0e6d2;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 400;
        letter-spacing: 0.5px;
    }

    /* 侧边栏奢华美化 */
    [data-testid="stSidebar"] {
        background-color: #090d12 !important;
        border-right: 1px solid rgba(212, 175, 55, 0.15);
    }

    .sidebar-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(212, 175, 55, 0.2);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 15px;
    }

    .sidebar-title {
        font-family: 'Cinzel', serif;
        color: #D4AF37;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    /* 对话气泡微调 */
    .stChatMessage {
        background-color: rgba(22, 27, 34, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        margin-bottom: 10px;
    }

    /* 输入框样式修正 */
    .stChatInputContainer {
        border-radius: 25px !important;
        border: 1px solid rgba(212, 175, 55, 0.4) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }

    /* 隐藏 Streamlit 默认 Header 与 Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 顶部奢华 Header 渲染
st.markdown("""
<div class="hotel-header">
    <div class="hotel-title">✨ The Royal Apex ✨</div>
    <div class="hotel-subtitle">HOTEL & SUITES • CONCIERGE AI ASSISTANT</div>
    <div class="gold-divider"></div>
    <div style="font-size: 13px; color: #8b949e; font-style: italic;">
        "Excellence in Every Detail — How may our Concierge assist you today?"
    </div>
</div>

<div class="badge-container">
    <span class="quick-badge">🔑 Check-in / Out</span>
    <span class="quick-badge">📶 High-Speed Wi-Fi</span>
    <span class="quick-badge">🍽️ Michelin Dining</span>
    <span class="quick-badge">🌤️ Live Weather</span>
    <span class="quick-badge">🚗 Valet Parking</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. 侧边栏 (Sidebar) 5星级酒店服务信息
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏨 HOTEL ESSENTIALS</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-card">
        <p style="margin:0; font-size:12px; color:#c9d1d9;"><b>🕒 Check-in:</b> 15:00 PM</p>
        <p style="margin:4px 0 0 0; font-size:12px; color:#c9d1d9;"><b>🕚 Check-out:</b> 12:00 PM</p>
        <p style="margin:4px 0 0 0; font-size:12px; color:#c9d1d9;"><b>📞 Concierge:</b> Dial '0'</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-title">💎 VIP SERVICES</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-card">
        <p style="margin:0; font-size:12px; color:#c9d1d9;">• 24/7 In-Room Fine Dining</p>
        <p style="margin:4px 0 0 0; font-size:12px; color:#c9d1d9;">• Executive Spa & Wellness</p>
        <p style="margin:4px 0 0 0; font-size:12px; color:#c9d1d9;">• Airport Chauffeur Transfer</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Greetings! I am your Royal Apex Virtual Concierge. How may I be of service to you today?"}
        ]
        st.rerun()

# ==========================================
# 3. 动态天气 API 获取函数
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
                f"🌤️ **Royal Apex Concierge Weather Desk**\n\n"
                f"📌 **Current Status**: {parse_wmo(curr_code)} | **Temperature**: {curr_temp}°C\n\n"
                f"• **Today ({dates[0]})**: {parse_wmo(codes[0])} | 🌡️ {min_temps[0]}°C to {max_temps[0]}°C\n"
                f"• **Tomorrow ({dates[1]})**: {parse_wmo(codes[1])} | 🌡️ {min_temps[1]}°C to {max_temps[1]}°C\n"
                f"• **Day After ({dates[2]})**: {parse_wmo(codes[2])} | 🌡️ {min_temps[2]}°C to {max_temps[2]}°C\n\n"
                f"💼 *Complimentary designer umbrellas are available at the Grand Concierge Desk upon request.*"
            )
            return reply
        else:
            return "☀️ The current climate at Royal Apex is pleasantly warm (28°C - 32°C). Please feel free to reach out to Concierge for further assistance."
    except Exception as e:
        return f"☀️ Currently pleasant and suitable for local exploration."

# ==========================================
# 4. 文本清洗与模型训练逻辑
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
            "greet": "Welcome to The Royal Apex Hotel.",
            "ask_wifi": "Wi-Fi: RoyalApex_Guest",
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
# 5. Session State 与预测逻辑
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Greetings! I am your Royal Apex Virtual Concierge. How may I be of service to you today?"}
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
# 6. 对话界面渲染
# ==========================================
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask about Wi-Fi, Breakfast, Check-in, or Weather..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    bot_reply = get_bot_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.chat_message("assistant").write(bot_reply)
