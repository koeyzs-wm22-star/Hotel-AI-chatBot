import json
import os
import re
import time
import datetime
import requests
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, FeatureUnion

# ==========================================
# 1. Page Config & Session State Setup
# ==========================================
st.set_page_config(
    page_title="The Grand Apex Resort & Spa | Executive Concierge",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Page Navigation State
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# Chat History State (FIXED: Properly initializing message list)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Greetings! It is my absolute pleasure to welcome you to The Grand Apex Resort & Spa. How may I assist your stay today?",
            "time": datetime.datetime.now().strftime("%I:%M %p")
        }
    ]

# Spa Reservation Context States
if "awaiting_spa_booking" not in st.session_state:
    st.session_state.awaiting_spa_booking = False

if "latest_spa_booking" not in st.session_state:
    st.session_state.latest_spa_booking = None


# ==========================================
# 2. Page Navigation & Utility Helpers
# ==========================================
def navigate_to(page_name):
    """Handles seamless page switching between TV Dashboard and Chat Hub."""
    st.session_state.page = page_name

def clear_chat_history():
    """Resets chat conversation and active booking states."""
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Greetings! It is my absolute pleasure to welcome you to The Grand Apex Resort & Spa. How may I assist your stay today?",
            "time": datetime.datetime.now().strftime("%I:%M %p")
        }
    ]
    st.session_state.awaiting_spa_booking = False
    st.session_state.latest_spa_booking = None

def clean_text(text):
    """Cleans text input for the machine learning classifier."""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s\u4e00-\u9fa5]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ==========================================
# 3. Real-Time Weather API Integration
# ==========================================
def get_realtime_weather():
    """Fetches real-time weather using Open-Meteo API with WMO translation."""
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            "latitude=3.139&longitude=101.6869&"
            "current_weather=true&"
            "daily=weathercode,temperature_2m_max,temperature_2m_min&"
            "timezone=auto"
        )
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            def parse_wmo(code):
                if code in [0, 1]: return "☀️ Clear & Sunny"
                elif code in [2, 3]: return "⛅ Light Clouds"
                elif code in [45, 48]: return "🌫️ Mist & Fog"
                elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95]: return "🌧️ Gentle Rain"
                return "🌤️ Pleasant"

            current = data.get("current_weather", {})
            curr_temp = current.get("temperature", 28)
            curr_code = current.get("weathercode", 0)
            
            daily = data.get("daily", {})
            dates = daily.get("time", ["Today", "Tomorrow", "Day After"])
            max_temps = daily.get("temperature_2m_max", [30, 31, 30])
            min_temps = daily.get("temperature_2m_min", [24, 24, 25])

            return {
                "success": True,
                "temp": curr_temp,
                "condition": parse_wmo(curr_code),
                "formatted_text": (
                    f"🌤️ <strong>Grand Apex Advisory Weather Service</strong><br><br>"
                    f"It is currently <strong>{curr_temp}°C</strong> with <strong>{parse_wmo(curr_code)}</strong> over the resort grounds.<br><br>"
                    f"<strong>3-Day Horizon:</strong><br>"
                    f"• <strong>Today ({dates[0]})</strong>: {min_temps[0]}°C to {max_temps[0]}°C<br>"
                    f"• <strong>Tomorrow ({dates[1]})</strong>: {min_temps[1]}°C to {max_temps[1]}°C<br>"
                    f"• <strong>Day After ({dates[2]})</strong>: {min_temps[2]}°C to {max_temps[2]}°C<br><br>"
                    f"🌂 <i>Should you wish to step out for sightseeing, luxury umbrellas and chauffeur-driven limousines are available at the Concierge Desk.</i>"
                )
            }
        else:
            return {
                "success": False,
                "temp": 28,
                "condition": "☀️ Sunny & Warm",
                "formatted_text": "☀️ The weather around Grand Apex is delightfully warm (28°C). Please let me know if you would like me to reserve an outdoor table for lunch."
            }
    except Exception:
        return {
            "success": False,
            "temp": 28,
            "condition": "☀️ Sunny & Clear",
            "formatted_text": "☀️ Weather forecast updated: Mild and suitable for local exploration. May I reserve a table at our Sky Garden Lounge for you?"
        }


# ==========================================
# 4. Internal Call & VIP Pass Card Generators
# ==========================================
def render_internal_call_card():
    """Generates the hotel direct internal call card component."""
    return """
📞 <strong>Grand Apex Internal Communications Desk</strong><br><br>
I can connect you directly with our specialized hotel departments. Pick up your in-room phone or dial below:

<div class="call-card">
    <div style="font-weight:700; font-size:14px; color:#1A1A1A;">🛎️ Grand Concierge & Front Desk</div>
    <div style="font-size:12px; color:#666; margin-bottom:6px;">For immediate check-in, check-out, or room key requests.</div>
    <a href="tel:0" class="call-btn">📞 Dial Extension '0'</a>
</div>

<div class="call-card">
    <div style="font-weight:700; font-size:14px; color:#1A1A1A;">🤵 Executive Butler Service</div>
    <div style="font-size:12px; color:#666; margin-bottom:6px;">For luggage unpacking, shoe shine, or VIP room preferences.</div>
    <a href="tel:801" class="call-btn">📞 Dial Extension '801'</a>
</div>

<div class="call-card">
    <div style="font-weight:700; font-size:14px; color:#1A1A1A;">🧹 Housekeeping & Amenities</div>
    <div style="font-size:12px; color:#666; margin-bottom:6px;">For extra towels, pillow menu, or room cleaning service.</div>
    <a href="tel:802" class="call-btn">📞 Dial Extension '802'</a>
</div>
"""

def render_spa_vip_pass(booking_details):
    """Generates the visual VIP Pass Pass for spa bookings."""
    return f"""
✨ <strong>Spa Reservation Confirmed</strong>

<div class="spa-pass-card">
    <div class="pass-header">
        <div class="pass-title">GH EXECUTIVE SPA VIP PASS</div>
        <div style="background: #FFF3E0; border: 1px solid #EF6C00; color: #E65100; font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 700;">
            ⏳ UNDER REVIEW
        </div>
    </div>
    <div class="pass-grid">
        <div>
            <div class="pass-label">GUEST NAME</div>
            <div class="pass-val">Mr. Alexander Vance</div>
        </div>
        <div>
            <div class="pass-label">SUITE</div>
            <div class="pass-val">Penthouse 1808</div>
        </div>
        <div>
            <div class="pass-label">BOOKING DETAILS</div>
            <div class="pass-val">{booking_details}</div>
        </div>
        <div>
            <div class="pass-label">LOCATION</div>
            <div class="pass-val">Apex Spa (5th Floor)</div>
        </div>
    </div>
</div>
"""


# ==========================================
# 5. ML Classifier & Response Pipeline
# ==========================================
LUXURY_RESPONSES = {
    "greet": "Greetings! It is my absolute pleasure to welcome you to The Grand Apex Resort & Spa. How may I be of service to you today?",
    "ask_wifi": """
📶 <strong>High-Speed Complimentary Wi-Fi</strong>

<div class="wifi-card">
    <div style="font-size: 10px; color: #7A7570; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">SUITE 1808 HIGH-SPEED NETWORK</div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
        <div>
            <div style="font-size: 11px; color: #7A7570;">WIFI NAME</div>
            <div style="font-size: 14px; font-weight: 700; color: #1A1A1A;">GrandApex_Guest</div>
        </div>
        <div>
            <div style="font-size: 11px; color: #7A7570;">PASSWORD</div>
            <div style="font-size: 14px; font-weight: 700; color: #8C6B2D;">Your Last Name</div>
        </div>
    </div>
</div>
<i>If you require high-bandwidth access for video conferencing, our IT Butler is available 24/7 by dialing '0'.</i>
""",

"ask_wifi_steps": """
📶 <strong>How to Connect to GrandApex_Guest Wi-Fi</strong><br><br>

1️⃣ Open <strong>Settings → Wi-Fi</strong> on your device.<br><br>

2️⃣ Select the network:
<strong>GrandApex_Guest</strong><br><br>

3️⃣ Wait for the login portal to appear automatically.
If it does not appear, open your browser and visit:
<strong>http://1.1.1.1</strong><br><br>

4️⃣ Enter:
<ul>
<li>Room Number</li>
<li>Guest Last Name</li>
</ul>

5️⃣ Click <strong>Connect</strong>.

<hr>

✅ Internet access is complimentary throughout the resort.

If you experience any issues, please dial <strong>Extension '0'</strong> for our IT Butler.
""",
    "ask_services": """
✨ <strong>Welcome to Exceptional Hospitality at The Grand Apex</strong><br><br>
It is our privilege to provide a wide range of world-class amenities and personalized services during your stay:<br><br>
🍷 <strong>Gastronomy & Dining</strong><br>
• 24-Hour In-Room Gourmet Dining<br>
• Michelin-Starred Fine Dining & Sky Garden Bar<br><br>
🧖‍♀️ <strong>Wellness & Leisure</strong><br>
• Apex Executive Spa & Thermal Suites (Floor 5)<br>
• Heated Rooftop Infinity Sky Pool & Cabanas<br>
• 24/7 Technogym Fitness Suite<br><br>
🛎️ <strong>Personalized Guest Care</strong><br>
• Executive Butler & Express Pressing Service<br>
• Private Airport Limousine Transfer<br>
• Direct In-Room Concierge Extension<br><br>
💡 <i>May I assist you with reserving a spa appointment, booking a restaurant table, or arranging transport?</i>
""",
    "ask_breakfast": """
🥂 <strong>Michelin-Star Breakfast Service</strong><br><br>
Breakfast is served daily at <strong>The Grand Atrium</strong> on Floor 1 from <strong>06:30 AM to 10:30 AM</strong>.<br><br>
Alternatively, featured in-room breakfast options include:<br>
• <strong>👑 Truffle Omelette</strong> — <i>$38</i><br>
• <strong>🥐 Parisian Bakery Basket</strong> — <i>$28</i><br>
• <strong>🥑 Avocado & Egg Tartine</strong> — <i>$32</i>
""",
    "ask_checkin": "🗝️ <strong>Check-in & Check-out Policies</strong><br><br>• <strong>Standard Check-in</strong>: 15:00 PM<br>• <strong>Standard Check-out</strong>: 12:00 PM (Noon)<br><br><i>If you require an extended Late Check-out or priority luggage storage, please inform me, and I will coordinate with the Front Desk immediately.</i>",
    "ask_spa": """
🧖‍♀️ <strong>Apex Executive Wellness & Spa</strong><br><br>
Located on Floor 5, our Spa offers signature aromatherapy, hot stone therapy, and luxury facials.<br><br>
🕒 <strong>Operating Hours:</strong> Daily <strong>09:00 AM – 22:00 PM</strong> (Last appointment at 20:30 PM)<br><br>
💵 <strong>Signature Menu & Pricing:</strong><br>
• <i>Apex Aromatherapy Massage</i> (60 min) — <strong>$180</strong><br>
• <i>Deep Tissue Recovery Therapy</i> (60 min) — <strong>$200</strong><br>
• <i>Himalayan Hot Stone Rejuvenation</i> (90 min) — <strong>$260</strong><br>
• <i>Customized Hydrating Facial</i> (60 min) — <strong>$190</strong><br><br>
📞 <strong>Reservation:</strong> Dial <strong>Ext '802'</strong> from your room phone, or tell me your preferred date, time, and guest count to hold a slot!
""",
    "ask_spa_booking": """
📅 <strong>Spa Reservation Request</strong><br><br>
I would be delighted to arrange this for you, Mr. Vance! To secure your preferred time, please specify:<br>
1. <strong>Your preferred date & time</strong> (e.g., Today at 15:00 PM)<br>
2. <strong>Number of guests</strong> (e.g., 1 pax)<br><br>
Alternatively, you may dial <strong>Ext '802'</strong> to speak directly with our Spa Receptionist for immediate confirmation.
""",
    "ask_dining": "🍽️ <strong>Gastronomic Experiences</strong><br><br>The Grand Apex features three award-winning venues:<br>1. <strong>L'Aura (Floor 48)</strong> - Michelin French Fine Dining<br>2. <strong>Sakura Sky Lounge (Floor 49)</strong> - Contemporary Omakase<br>3. <strong>The Atrium (Floor 1)</strong> - All-Day International Buffet"
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

    # 1. Internal Call Training Samples
    call_patterns = ["call front desk", "call butler", "internal call", "phone number", "contact housekeeping", "call hotel", "dial front desk", "phone front desk", "打电话", "联系前台", "呼叫管家", "打给前台", "内线电话"]
    for p in call_patterns:
        X.append(clean_text(p))
        y.append("internal_call")

    # 2. Services Training Samples
    service_patterns = [
        "what services do you have", "what services", "hotel services", "services", 
        "what amenities are available", "amenities", "what can I do at this hotel", 
        "hotel facilities", "list your services", "what do you offer", "facilities",
        "有什么服务", "酒店有什么设施", "你们提供什么服务", "服务项目"
    ]
    for p in service_patterns:
        X.append(clean_text(p))
        y.append("ask_services")

    # 3. Spa Menu & Pricing Samples
    spa_patterns = [
        "spa", "spa price", "spa pricing", "how much is spa", "spa menu", 
        "spa hours", "when is spa open", "massage", "massage price", "spa price list",
        "spa价格", "spa多少钱", "按摩多少钱", "spa营业时间"
    ]
    for p in spa_patterns:
        X.append(clean_text(p))
        y.append("ask_spa")

    booking_patterns = [
        "how to book spa", "I want to book spa", "book a massage", "make spa appointment", "reserve spa", "book spa",
        "怎么预约spa", "帮我订spa", "我想做spa", "预约spa"
    ]
    for p in booking_patterns:
        X.append(clean_text(p))
        y.append("ask_spa_booking")

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

# Train & Load Classifier
model = load_and_train_model()

def get_bot_response(user_input):
    cleaned_input = clean_text(user_input)
    
    if not cleaned_input or not cleaned_input.strip():
        return "Greetings! How may I assist your stay at The Grand Apex today?"

    # Context intercept for Spa Reservation follow-up
    if st.session_state.awaiting_spa_booking:
        st.session_state.awaiting_spa_booking = False
        st.session_state.latest_spa_booking = user_input.strip()
        return render_spa_vip_pass(user_input.strip())
        
    try:
        probs = model.predict_proba([cleaned_input])[0]
        max_idx = np.argmax(probs)
        confidence = probs[max_idx]
        predicted_tag = model.classes_[max_idx]
        
        if confidence < 0.18:
            return (
                "I apologize, but I want to ensure you receive the most precise assistance. "
                "Could you please specify if you are asking about <strong>Wi-Fi</strong>, <strong>Breakfast</strong>, <strong>Services</strong>, or <strong>Check-in</strong>?<br><br>"
                "You may also dial <strong>'0'</strong> on your room phone to connect directly with the Front Desk."
            )
        
        if predicted_tag in ["ask_spa", "ask_spa_booking"]:
            st.session_state.awaiting_spa_booking = True
            return LUXURY_RESPONSES.get(predicted_tag)

        if predicted_tag == "ask_weather":
            weather_res = get_realtime_weather()
            return weather_res["formatted_text"]

        if predicted_tag == "internal_call":
            return render_internal_call_card()

        return LUXURY_RESPONSES.get(predicted_tag, "Thank you. Our Concierge Desk is entirely at your service.")
        
    except Exception:
        return "I am at your service. Please feel free to ask about our room amenities, dining, or guest services."


# ==========================================
# 6. Styling Injection (Bright Luxury Theme)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    .stApp {
        background: linear-gradient(180deg, #FAF8F5 0%, #F3EFEA 100%);
        color: #1A1A1A;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(184, 150, 92, 0.35);
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 8px 30px rgba(184, 150, 92, 0.08);
        margin-bottom: 20px;
    }

    /* Left / Right Speech Bubble Chat Layout */
    [data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] { display: none !important; }
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 0px !important;
        box-shadow: none !important;
    }

    .chat-row-user {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 14px;
    }
    .chat-row-assistant {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 14px;
    }

    .chat-bubble {
        max-width: 82%;
        padding: 14px 18px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.5;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        position: relative;
    }

    .bubble-assistant {
        background-color: #FFFFFF;
        color: #1A1A1A;
        border: 1px solid rgba(197, 160, 89, 0.3);
        border-bottom-left-radius: 4px;
    }

    .bubble-user {
        background: linear-gradient(135deg, #F5E8D0 0%, #EAD5B3 100%);
        color: #1A1A1A;
        border: 1px solid #C5A059;
        border-bottom-right-radius: 4px;
    }

    .msg-meta {
        font-size: 10px;
        color: #7A7570;
        margin-top: 6px;
        text-align: right;
    }

    .chat-bubble strong { color: #8C6B2D !important; }

    /* Custom Sub-Card Components inside Chat */
    .spa-pass-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #FAF6F0 100%) !important;
        border: 2px solid #C5A059 !important;
        border-radius: 14px;
        padding: 16px;
        margin: 10px 0 4px 0;
        box-shadow: 0 6px 20px rgba(197, 160, 89, 0.12) !important;
        position: relative;
        overflow: hidden;
    }
    .spa-pass-card::before {
        content: "";
        position: absolute;
        top: 0; right: 0; width: 5px; height: 100%;
        background: linear-gradient(180deg, #D4AF37 0%, #AA7C11 100%);
    }
    .pass-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px dashed rgba(197, 160, 89, 0.5);
        padding-bottom: 8px;
        margin-bottom: 10px;
    }
    .pass-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 18px;
        font-weight: 700;
        color: #8C6B2D !important;
        letter-spacing: 1px;
    }
    .pass-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        font-size: 12px;
    }
    .pass-label {
        font-size: 9px;
        color: #7A7570 !important;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }
    .pass-val {
        font-size: 13px;
        font-weight: 600;
        color: #1A1A1A !important;
    }

    .wifi-card {
        background: #FAF6F0 !important;
        border: 1px solid #C5A059 !important;
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0;
    }

    .call-card {
        background: #FAF6F0 !important;
        border: 1px solid #C5A059 !important;
        border-radius: 10px;
        padding: 12px 14px;
        margin-top: 8px;
    }
    .call-btn {
        display: inline-block;
        background-color: #C5A059;
        color: white !important;
        padding: 6px 14px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 12px;
        font-weight: 600;
        margin-top: 4px;
    }

    .header-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 34px;
        font-weight: 700;
        color: #1A1A1A;
    }
    .header-sub {
        font-size: 13px;
        color: #8C6B2D;
        letter-spacing: 2px;
        text-transform: uppercase;
        font-weight: 600;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #E8F5E9;
        border: 1px solid #2E7D32;
        color: #1B5E20;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #2E7D32;
        border-radius: 50%;
        box-shadow: 0 0 8px #2E7D32;
    }

    .guest-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 58px;
        font-weight: 700;
        color: #1A1A1A;
        margin: 5px 0;
    }

    [data-testid="stChatInput"] {
        background-color: #FFFFFF !important;
        border: 1px solid #C5A059 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
    }

    .stButton>button {
        border: 1px solid #C5A059 !important;
        background: #FFFFFF !important;
        color: #8C6B2D !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background: #C5A059 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(197, 160, 89, 0.3) !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 7. PAGE 1: Luxury Dashboard & Banner Slider
# ==========================================
if st.session_state.page == "dashboard":
    weather_data = get_realtime_weather()
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(197, 160, 89, 0.3); padding-bottom: 15px; margin-bottom: 20px;">
        <div style="font-family: 'Cormorant Garamond', serif; font-size: 26px; font-weight: 700; color: #8C6B2D; letter-spacing: 3px;">THE GRAND APEX RESORT & SPA</div>
        <div style="font-size: 13px; color: #555555; letter-spacing: 1px; font-weight: 500;">SUITE 1808 &nbsp;|&nbsp; {datetime.datetime.now().strftime("%I:%M %p")} &nbsp;|&nbsp; {weather_data['temp']}°C {weather_data['condition'].split()[0]}</div>
    </div>
    """, unsafe_allow_html=True)

    # 21:9 Auto-Slider Banner
    auto_slider_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: transparent; }
        .slider-container {
            position: relative; width: 100%; height: 210px; border-radius: 16px; overflow: hidden;
            box-shadow: 0 8px 25px rgba(197, 160, 89, 0.15); border: 1px solid rgba(197, 160, 89, 0.4);
        }
        .slide { position: absolute; width: 100%; height: 100%; opacity: 0; transition: opacity 1s ease-in-out; background-size: cover; background-position: center; }
        .slide.active { opacity: 1; }
        .slide-overlay {
            position: absolute; bottom: 0; left: 0; right: 0; padding: 20px;
            background: linear-gradient(to top, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0) 100%); color: #ffffff;
        }
        .slide-title { font-size: 18px; font-weight: 600; letter-spacing: 1px; margin-bottom: 4px; color: #FDFBF7; }
        .slide-desc { font-size: 12px; color: #D1C7BD; font-weight: 300; }
        .dots-container { position: absolute; bottom: 12px; right: 20px; display: flex; gap: 6px; }
        .dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.4); transition: all 0.3s ease; }
        .dot.active { background: #C5A059; width: 20px; border-radius: 10px; }
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
        <div class="dots-container"><div class="dot active"></div><div class="dot"></div><div class="dot"></div></div>
    </div>
    <script>
        let currentSlide = 0; const slides = document.querySelectorAll('.slide'); const dots = document.querySelectorAll('.dot');
        function showSlide(index) {
            slides.forEach(s => s.classList.remove('active')); dots.forEach(d => d.classList.remove('active'));
            slides[index].classList.add('active'); dots[index].classList.add('active');
        }
        setInterval(() => { currentSlide = (currentSlide + 1) % slides.length; showSlide(currentSlide); }, 3500);
    </script>
    </body>
    </html>
    """
    components.html(auto_slider_html, height=220)

    st.markdown("""
    <div style="text-align: center; margin: 20px 0 30px 0;">
        <div style="font-size: 13px; letter-spacing: 4px; text-transform: uppercase; color: #8C6B2D; font-weight: 600;">Welcome to Your Suite</div>
        <div class="guest-name">Mr. Alexander Vance</div>
        <div style="display: inline-block; background: #FAF6F0; border: 1px solid #C5A059; color: #8C6B2D; padding: 6px 18px; border-radius: 20px; font-size: 13px; font-weight: 600;">⭐ Apex Platinum VIP Honor Guest</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #7A7570; margin-bottom: 8px; font-weight: 600;">📅 Stay Duration</div>
            <div style="font-size: 20px; font-weight: 700; color: #1A1A1A;">28 Jul – 03 Aug 2026</div>
            <div style="font-size: 12px; color: #8C6B2D; margin-top: 6px; font-weight: 500;">Express Check-out @ 12:00 PM</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #7A7570; margin-bottom: 8px; font-weight: 600;">👑 Apex Rewards</div>
            <div style="font-size: 20px; font-weight: 700; color: #1A1A1A;">48,500 Points</div>
            <div style="font-size: 12px; color: #8C6B2D; margin-top: 6px; font-weight: 500;">Complimentary Spa Access Ready</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        booking_disp = st.session_state.latest_spa_booking or "No Active Bookings"
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #7A7570; margin-bottom: 8px; font-weight: 600;">🧖 Active Reservations</div>
            <div style="font-size: 18px; font-weight: 700; color: #1A1A1A;">{booking_disp}</div>
            <div style="font-size: 12px; color: #8C6B2D; margin-top: 6px; font-weight: 500;">{"⏳ Request Under Review" if st.session_state.latest_spa_booking else "Ready for Booking"}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        if st.button("💬 Open Private Executive Concierge", use_container_width=True):
            navigate_to("chat")
            st.rerun()


# ==========================================
# 8. PAGE 2: Left/Right Chat Interface
# ==========================================
elif st.session_state.page == "chat":
    top_c1, top_c2 = st.columns([4, 1])
    with top_c1:
        st.markdown("""
        <div>
            <div class="header-sub">The Grand Apex Hospitality Network</div>
            <div class="header-title">Executive Virtual Butler & Concierge</div>
        </div>
        """, unsafe_allow_html=True)
    with top_c2:
        if st.button("⬅️ Back to TV Home", use_container_width=True):
            navigate_to("dashboard")
            st.rerun()

    st.divider()

    left_col, main_chat_col = st.columns([1, 2.8], gap="large")

    # --- LEFT SIDEBAR ---
    with left_col:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #7A7570; margin-bottom: 12px; font-weight: 600;">DUTY BUTLER</div>
            <div class="status-badge"><span class="pulse-dot"></span> Duty Butler: Online</div>
            <div style="margin-top: 15px; font-size: 13px; color: #555;">
                Welcome, <strong>Mr. Vance</strong>.<br>
                How may our concierge team complement your stay today?
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Reset Chat Session", use_container_width=True):
            clear_chat_history()
            st.rerun()

    # --- MAIN CHAT AREA ---
    with main_chat_col:
        # Chat Messages Box
        chat_box = st.container(height=450)
        with chat_box:
            for msg in st.session_state.messages:
                role = msg["role"]
                timestamp = msg.get("time", datetime.datetime.now().strftime("%I:%M %p"))

                if role == "user":
                    user_html = (
                        f'<div class="chat-row-user">'
                        f'<div class="chat-bubble bubble-user">'
                        f'<div>{msg["content"]}</div>'
                        f'<div class="msg-meta">{timestamp}</div>'
                        f'</div></div>'
                    )
                    st.markdown(user_html, unsafe_allow_html=True)
                else:
                    assistant_html = (
                        f'<div class="chat-row-assistant">'
                        f'<div class="chat-bubble bubble-assistant">'
                        f'<div>{msg["content"]}</div>'
                        f'<div class="msg-meta">{timestamp}</div>'
                        f'</div></div>'
                    )
                    st.markdown(assistant_html, unsafe_allow_html=True)

        # Chat Input Bar
        user_prompt = st.chat_input("Type your request here (e.g., Wi-Fi, Spa, Breakfast)...")
        if user_prompt:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            
            # Save User Message
            st.session_state.messages.append({
                "role": "user", 
                "content": user_prompt,
                "time": current_time
            })
            
            # Generate & Save Response
            response_text = get_bot_response(user_prompt)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_text,
                "time": current_time
            })
            
            st.rerun()
