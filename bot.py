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
# 1. Page Configuration & Theme
# ==========================================
st.set_page_config(
    page_title="The Grand Apex Resort & Spa | In-Room Concierge",
    page_icon="👑",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

    .stApp {
        background: linear-gradient(180deg, #FDFBF7 0%, #F4EFE6 100%);
        color: #2C2A29;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* In-Room Smart TV / Display Header */
    .room-display-card {
        background: #1A1A1A;
        color: #FDFBF7;
        padding: 20px 24px;
        border-radius: 16px;
        border: 1px solid #B8965C;
        margin-bottom: 24px;
        box-shadow: 0 12px 35px rgba(0,0,0,0.18);
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .room-display-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(184, 150, 92, 0.3);
        padding-bottom: 12px;
        margin-bottom: 14px;
    }

    .hotel-brand {
        font-family: 'Cormorant Garamond', serif;
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 2px;
        color: #B8965C;
    }

    .room-number-badge {
        background: #B8965C;
        color: #1A1A1A;
        font-weight: 700;
        font-size: 13px;
        padding: 4px 12px;
        border-radius: 20px;
        letter-spacing: 1px;
    }

    .room-display-body {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        font-size: 13px;
    }

    .status-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }

    .status-active {
        background: rgba(46, 125, 50, 0.2);
        color: #81C784;
        border: 1px solid #4CAF50;
    }

    .status-pending {
        background: rgba(230, 81, 0, 0.2);
        color: #FFB74D;
        border: 1px solid #FF9800;
    }

    /* Chat bubble styling */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(184, 150, 92, 0.15) !important;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Greetings Mr. Vance! Welcome to The Grand Apex Resort & Spa. How may I assist your stay today?"}
    ]

if "awaiting_spa_booking" not in st.session_state:
    st.session_state.awaiting_spa_booking = False

if "latest_spa_booking" not in st.session_state:
    st.session_state.latest_spa_booking = None

# ==========================================
# 2. In-Room Smart TV / Display Screen
# ==========================================
booking_status_html = f"""
<div class="room-display-card">
    <div class="room-display-header">
        <div class="hotel-brand">THE GRAND APEX RESORT & SPA</div>
        <div class="room-number-badge">ROOM 1808 • PENTHOUSE</div>
    </div>
    <div class="room-display-body">
        <div>
            <div style="color: #A09D9A; font-size: 11px;">GUEST NAME</div>
            <div style="font-weight: 600; font-size: 15px;">Mr. Alexander Vance</div>
        </div>
        <div>
            <div style="color: #A09D9A; font-size: 11px;">CHECK-OUT DATE</div>
            <div style="font-weight: 600; font-size: 15px;">03 Aug 2026 (12:00 PM)</div>
        </div>
        <div>
            <div style="color: #A09D9A; font-size: 11px;">VIP STATUS</div>
            <div style="color: #B8965C; font-weight: 600;">⭐ Apex Platinum Member</div>
        </div>
        <div>
            <div style="color: #A09D9A; font-size: 11px;">ACTIVE SPA RESERVATION</div>
            <div>
                {f'<span class="status-pill status-pending">⏳ {st.session_state.latest_spa_booking}</span>' if st.session_state.latest_spa_booking else '<span class="status-pill status-active">None</span>'}
            </div>
        </div>
    </div>
</div>
"""
st.markdown(booking_status_html, unsafe_allow_html=True)

# ==========================================
# 3. Sidebar Panel
# ==========================================
with st.sidebar:
    st.markdown("### 🏨 Guest Quick Actions")
    dept = st.selectbox("Direct Dial Extension:", ["Front Desk (Ext 0)", "Private Butler (Ext 801)", "Housekeeping (Ext 802)"])
    if st.button("📞 Dial Extension", use_container_width=True):
        st.toast(f"Dialing {dept} from room phone...")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🧹 Reset Screen & Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Greetings Mr. Vance! Welcome to The Grand Apex Resort & Spa. How may I assist your stay today?"}
        ]
        st.session_state.awaiting_spa_booking = False
        st.session_state.latest_spa_booking = None
        st.rerun()

# ==========================================
# 4. Spa Booking Validation Function
# ==========================================
def validate_spa_booking(text):
    text_lower = text.lower()
    
    # 1. Detect Guest Count (e.g., 1pax, 2 pax, 3 people, 1 person)
    has_pax = bool(re.search(r'\b\d+\s*(pax|people|person|guests?|位|人)\b', text_lower))
    
    # 2. Strip explicit date patterns (1/8/2026, 31-07-2026) so numbers don't mess up time checking
    cleaned_time_text = re.sub(r'\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b', '', text_lower)
    
    # 3. Check if time/date is present
    has_time_or_date = bool(re.search(
        r'(\b\d{1,2}(:\d{2})?\s*(am|pm)\b|\b\d{1,2}:\d{2}\b|\btoday\b|\btomorrow\b|\b\d{1,2}(st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b|\b(july|august|september|october|november|december|january|february|march|april|june)\b|\b\d+\s*(点|点半|号)\b)', 
        text_lower
    )) or bool(re.search(r'\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b', text_lower))
    
    # Check operating hours (09:00 AM to 20:30 PM)
    time_match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b|\b(\d{1,2}):(\d{2})\b', cleaned_time_text)
    
    if time_match:
        if time_match.group(1): # Format with am/pm (e.g. 11:30am)
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3)
            
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
        else: # 24-hr format (e.g. 20:30)
            hour = int(time_match.group(4))
            minute = int(time_match.group(5))
            
        if hour > 20 or (hour == 20 and minute > 30):
            return {
                "valid": False,
                "msg": "⏰ **Appointment Hours Exceeded**\n\nOur last available spa treatment slot starts at **20:30 PM** (Spa closes at 22:00 PM).\n\nPlease select a time **between 09:00 AM and 20:30 PM**."
            }
        elif hour < 9:
            return {
                "valid": False,
                "msg": "⏰ **Spa Operating Hours Alert**\n\nOur Spa opens at **09:00 AM** daily. Please select a time after 09:00 AM."
            }

    if not has_pax and not has_time_or_date:
        return {
            "valid": False,
            "msg": "⚠️ **Details Missing**\n\nTo process your reservation, please provide **both** your preferred date/time (e.g., *1/8/2026 11:30am*) and guest count (e.g., *1 pax*)."
        }
    elif not has_pax:
        return {
            "valid": False,
            "msg": "⚠️ **Number of Guests Needed**\n\nGot the time! Could you also specify **how many guests (pax)** will be attending?"
        }
    elif not has_time_or_date:
        return {
            "valid": False,
            "msg": "⚠️ **Preferred Time Needed**\n\nGot it! Could you please let us know **what date and time** you would like to reserve? (Last appointment is at 20:30 PM)"
        }

    return {"valid": True, "msg": "OK"}

# ==========================================
# 5. NLP Model Setup
# ==========================================
def clean_text(text):
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

@st.cache_resource
def load_model():
    X = [
        "luxury facial booking", "book spa", "reserve facial", "i want to book spa",
        "spa price", "spa hours", "what services do you have", "wifi password", "breakfast time"
    ]
    y = [
        "ask_spa_booking", "ask_spa_booking", "ask_spa_booking", "ask_spa_booking",
        "ask_spa", "ask_spa", "ask_services", "ask_wifi", "ask_breakfast"
    ]
    
    union = FeatureUnion([
        ('word_tf', TfidfVectorizer(ngram_range=(1, 3), token_pattern=r'\S+')),
        ('char_tf', TfidfVectorizer(ngram_range=(2, 4), analyzer='char_wb'))
    ])
    model = make_pipeline(union, LogisticRegression(C=5.0))
    model.fit(X, y)
    return model

model = load_model()

# ==========================================
# 6. Response Handler
# ==========================================
def get_bot_response(user_input):
    cleaned = clean_text(user_input)

    # Contextual check: If already expecting spa details
    if st.session_state.awaiting_spa_booking:
        check = validate_spa_booking(user_input)
        if not check["valid"]:
            return check["msg"]
        
        # Approved! Reset wait state & update room display
        st.session_state.awaiting_spa_booking = False
        st.session_state.latest_spa_booking = user_input.strip()
        
        return (
            "✨ **Spa Reservation Request Received!**\n\n"
            f"Thank you, Mr. Vance. We have registered your booking request for: **\"{user_input.strip()}\"**.\n\n"
            "Your request status has been updated on your **Room Display Screen** above. Our Spa team will verify the slot immediately."
        )

    # Intent Prediction
    pred = model.predict([cleaned])[0]

    if pred == "ask_spa_booking":
        st.session_state.awaiting_spa_booking = True
        return (
            "📅 **Apex Spa Reservation Desk**\n\n"
            "I would be delighted to reserve this for you, Mr. Vance! Please provide:\n"
            "1. **Preferred Date & Time** (e.g., *1/8/2026 11:30am*)\n"
            "2. **Number of Guests** (e.g., *1 pax*)"
        )
    elif pred == "ask_spa":
        return "🧖‍♀️ **Apex Executive Spa (Floor 5)**\nOperating Hours: 09:00 AM – 22:00 PM (Last slot 20:30 PM)."
    
    return "Thank you Mr. Vance. Our Virtual Concierge Desk is entirely at your service."

# ==========================================
# 7. Render Chat Stream
# ==========================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Message Concierge Desk..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        response = get_bot_response(prompt)
        st.markdown(response)
        
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun() # Refresh page so the Room Display header updates instantly!
