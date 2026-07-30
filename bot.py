import re
import datetime
import streamlit as st

# ==========================================
# 1. Page Config & State Setup
# ==========================================
st.set_page_config(
    page_title="Grand Apex Executive Concierge",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session States
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Good morning, Mr. Vance. I am your Apex Virtual Concierge. How may I personalize your stay today?",
            "time": datetime.datetime.now().strftime("%I:%M %p")
        }
    ]

if "awaiting_spa_booking" not in st.session_state:
    st.session_state.awaiting_spa_booking = False

if "latest_spa_booking" not in st.session_state:
    st.session_state.latest_spa_booking = None

# Custom CSS for Bright Luxury Theme with Left/Right Speech Bubbles
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Bright Luxury Ivory & Gold Theme */
    .stApp {
        background: linear-gradient(180deg, #FAF8F5 0%, #F3EFEA 100%);
        color: #1A1A1A;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Glassmorphism Luxury Container - Bright White & Warm Gold */
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(184, 150, 92, 0.35);
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 8px 30px rgba(184, 150, 92, 0.08);
        margin-bottom: 20px;
    }

    /* ==========================================
       💬 CHATBOT MESSAGES - LEFT / RIGHT LAYOUT
       ========================================== */

    /* Hide Default Avatar & Container Borders */
    [data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] {
        display: none !important;
    }
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 0px !important;
        box-shadow: none !important;
    }

    /* Message Flex Wrapper */
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

    /* Chat Bubbles Base */
    .chat-bubble {
        max-width: 80%;
        padding: 14px 18px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.5;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        position: relative;
    }

    /* Assistant Bubble (Left Aligned - Crisp White) */
    .bubble-assistant {
        background-color: #FFFFFF;
        color: #1A1A1A;
        border: 1px solid rgba(197, 160, 89, 0.3);
        border-bottom-left-radius: 4px;
    }

    /* User Bubble (Right Aligned - Soft Luxury Champagne Gold) */
    .bubble-user {
        background: linear-gradient(135deg, #F5E8D0 0%, #EAD5B3 100%);
        color: #1A1A1A;
        border: 1px solid #C5A059;
        border-bottom-right-radius: 4px;
    }

    /* Timestamp metadata inside bubbles */
    .msg-meta {
        font-size: 10px;
        color: #7A7570;
        margin-top: 6px;
        text-align: right;
    }

    /* Headers and bold text inside chat bubbles */
    .chat-bubble strong {
        color: #8C6B2D !important;
    }

    /* 🎟️ VISUAL SPA TICKET / CONFIRMATION CARD */
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

    /* 📶 VISUAL WIFI ACCESS CARD */
    .wifi-card {
        background: #FAF6F0 !important;
        border: 1px solid #C5A059 !important;
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0;
    }

    /* Executive Concierge Header */
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

    /* Status Pulse Pill */
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

    .info-tag {
        background: rgba(197, 160, 89, 0.12);
        border: 1px solid rgba(197, 160, 89, 0.4);
        color: #725318;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }

    .guest-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 58px;
        font-weight: 700;
        color: #1A1A1A;
        margin: 5px 0;
    }

    /* Custom Streamlit Input Box */
    [data-testid="stChatInput"] {
        background-color: #FFFFFF !important;
        border: 1px solid #C5A059 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
    }

    /* Custom Streamlit Buttons Styling */
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

    /* Hide Default Chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Date & Booking Validation
# ==========================================
def validate_spa_booking(text):
    text_lower = text.lower()
    has_pax = bool(re.search(r'\b\d+\s*(pax|people|person|guests?|位|人)\b', text_lower))
    cleaned_time_text = re.sub(r'\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b', '', text_lower)
    
    has_time_or_date = bool(re.search(
        r'(\b\d{1,2}(:\d{2})?\s*(am|pm)\b|\b\d{1,2}:\d{2}\b|\btoday\b|\btomorrow\b)', text_lower
    )) or bool(re.search(r'\b\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\b', text_lower))
    
    time_match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b|\b(\d{1,2}):(\d{2})\b', cleaned_time_text)
    
    if time_match:
        if time_match.group(1):
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3)
            if ampm == 'pm' and hour < 12: hour += 12
            elif ampm == 'am' and hour == 12: hour = 0
        else:
            hour = int(time_match.group(4))
            minute = int(time_match.group(5))
            
        if hour > 20 or (hour == 20 and minute > 30):
            return {"valid": False, "msg": "⏰ **Operating Hours Notice**: Our last spa slot starts at **20:30 PM**. Please select a time between 09:00 AM and 20:30 PM."}
        elif hour < 9:
            return {"valid": False, "msg": "⏰ **Operating Hours Notice**: The Executive Spa opens at **09:00 AM** daily."}

    if not has_pax and not has_time_or_date:
        return {"valid": False, "msg": "⚠️ **Details Missing**: Please specify **both** your preferred time (e.g. *1/8/2026 11:30am*) and guest count (e.g. *1 pax*)."}
    elif not has_pax:
        return {"valid": False, "msg": "⚠️ **Missing Guests**: How many guests (pax) will be attending?"}
    elif not has_time_or_date:
        return {"valid": False, "msg": "⚠️ **Missing Time**: What date and time would you like to reserve?"}

    return {"valid": True, "msg": "OK"}


# ==========================================
# 3. PAGE 1: Welcome Hub Dashboard
# ==========================================
if st.session_state.page == "dashboard":
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(197, 160, 89, 0.3); padding-bottom: 15px; margin-bottom: 30px;">
        <div style="font-family: 'Cormorant Garamond', serif; font-size: 26px; font-weight: 700; color: #8C6B2D; letter-spacing: 3px;">THE GRAND APEX RESORT & SPA</div>
        <div style="font-size: 13px; color: #555555; letter-spacing: 1px; font-weight: 500;">SUITE 1808 &nbsp;|&nbsp; 10:42 AM &nbsp;|&nbsp; 28°C SUNNY</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin: 20px 0 40px 0;">
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
            <div style="font-size: 12px; color: #8C6B2D; margin-top: 6px; font-weight: 500;">Eligible for Complimentary Spa Service</div>
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
            st.session_state.page = "chat"
            st.rerun()


# ==========================================
# 4. PAGE 2: Concierge Suite with Left/Right Chat
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
            st.session_state.page = "dashboard"
            st.rerun()

    st.divider()

    left_col, main_chat_col = st.columns([1, 2.8], gap="large")

    # --- LEFT SIDEBAR: Suite Context ---
    with left_col:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #7A7570; margin-bottom: 12px; font-weight: 600;">BUTLER ASSIGNMENT</div>
            <div class="status-badge"><span class="pulse-dot"></span> Duty Butler: Online</div>
            <div style="font-size: 16px; font-weight: 700; color: #1A1A1A; margin-top: 14px;">Jean-Luc Moreau</div>
            <div style="font-size: 12px; color: #666666;">Private Butler Service (Ext. 801)</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #7A7570; margin-bottom: 12px; font-weight: 600;">SUITE DETAILS</div>
            <div style="margin-bottom: 10px;">
                <div style="font-size: 11px; color: #7A7570;">GUEST</div>
                <div style="font-weight: 700; font-size: 14px; color: #1A1A1A;">Mr. Alexander Vance</div>
            </div>
            <div style="margin-bottom: 10px;">
                <div style="font-size: 11px; color: #7A7570;">ACCOMMODATION</div>
                <div style="font-weight: 700; font-size: 14px; color: #1A1A1A;">Suite 1808 (Penthouse)</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #7A7570;">TIER STATUS</div>
                <div style="color: #8C6B2D; font-weight: 700; font-size: 13px;">⭐ Apex Platinum</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        booking_status = st.session_state.latest_spa_booking or "None"
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #7A7570; margin-bottom: 12px; font-weight: 600;">ACTIVE SUITE REQUESTS</div>
            <div style="font-size: 13px; color: #1A1A1A; margin-bottom: 6px;"><b>Spa Reservation:</b></div>
            <div class="info-tag">{booking_status}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- MAIN CHAT AREA ---
    with main_chat_col:
        st.markdown("##### ⚡ Direct Concierge Requests")
        q1, q2, q3, q4 = st.columns(4)
        
        prompt_input = None
        if q1.button("💆 Reserve Spa", use_container_width=True):
            prompt_input = "I would like to book a luxury facial treatment at the spa."
        if q2.button("🍳 In-Room Dining", use_container_width=True):
            prompt_input = "Please send the breakfast menu for in-room dining."
        if q3.button("📶 Suite WiFi Key", use_container_width=True):
            prompt_input = "What is the high-speed WiFi password for Suite 1808?"
        if q4.button("🧹 Housekeeping", use_container_width=True):
            prompt_input = "Please request fresh towels and evening turndown service."

        st.markdown("<br>", unsafe_allow_html=True)

        # 💬 CHAT CONTAINER WITH LEFT/RIGHT ALIGNMENT
        chat_box = st.container(height=450)
        with chat_box:
            for msg in st.session_state.messages:
                role = msg["role"]
                timestamp = msg.get("time", datetime.datetime.now().strftime("%I:%M %p"))

                if role == "user":
                    st.markdown(f"""
                    <div class="chat-row-user">
                        <div class="chat-bubble bubble-user">
                            {msg['content']}
                            <div class="msg-meta">{timestamp}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-row-assistant">
                        <div class="chat-bubble bubble-assistant">
                            {msg['content']}
                            <div class="msg-meta">{timestamp}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        user_text = st.chat_input("Message your Virtual Concierge...")
        if prompt_input:
            user_text = prompt_input

        if user_text:
            curr_time = datetime.datetime.now().strftime("%I:%M %p")
            st.session_state.messages.append({
                "role": "user",
                "content": user_text,
                "time": curr_time
            })
            
            if st.session_state.awaiting_spa_booking:
                check = validate_spa_booking(user_text)
                if not check["valid"]:
                    reply = check["msg"]
                else:
                    st.session_state.awaiting_spa_booking = False
                    st.session_state.latest_spa_booking = user_text.strip()
                    
                    # 🎟️ BRIGHT LUXURY SPA PASS CARD
                    reply = f"""
✨ <strong>Spa Reservation Confirmed</strong>

<div class="spa-pass-card">
    <div class="pass-header">
        <div class="pass-title">🧖 EXECUTIVE SPA VIP PASS</div>
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
            <div class="pass-val">{user_text.strip()}</div>
        </div>
        <div>
            <div class="pass-label">LOCATION</div>
            <div class="pass-val">Apex Spa (5th Floor)</div>
        </div>
    </div>
</div>
"""
            else:
                text_low = user_text.lower()
                if any(k in text_low for k in ["spa", "book", "facial", "massage", "reserve"]):
                    st.session_state.awaiting_spa_booking = True
                    reply = """
📅 <strong>Apex Executive Spa Reservation</strong><br><br>

I would be delighted to arrange your spa treatment, Mr. Vance! Please reply with:<br>
1. <strong>Preferred Date & Time</strong> (e.g., <i>1/8/2026 11:30am</i>)<br>
2. <strong>Number of Guests</strong> (e.g., <i>1 pax</i>)
"""
                elif "wifi" in text_low:
                    reply = """
📶 <strong>Executive WiFi Network Credentials</strong>

<div class="wifi-card">
    <div style="font-size: 10px; color: #7A7570; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">SUITE 1808 HIGH-SPEED NETWORK</div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
        <div>
            <div style="font-size: 11px; color: #7A7570;">NETWORK</div>
            <div style="font-size: 14px; font-weight: 700; color: #1A1A1A;">GrandApex_VIP_1808</div>
        </div>
        <div>
            <div style="font-size: 11px; color: #7A7570;">PASSWORD</div>
            <div style="font-size: 14px; font-weight: 700; color: #8C6B2D;">ApexVIP1808</div>
        </div>
    </div>
</div>
"""
                elif "breakfast" in text_low or "dining" in text_low:
                    reply = """
🍽️ <strong>In-Room Executive Dining</strong><br><br>

Featured breakfast sets for <strong>Suite 1808</strong>:<br>
• <strong>👑 Truffle Omelette</strong> — <i>$38</i><br>
• <strong>🥐 Parisian Bakery Basket</strong> — <i>$28</i><br>
• <strong>🥑 Avocado & Egg Tartine</strong> — <i>$32</i><br><br>
<i>Reply with your preferred items to place your order.</i>
"""
                else:
                    reply = f"Thank you, Mr. Vance. I have conveyed your request regarding <i>\"{user_text}\"</i> directly to your Duty Butler, <strong>Jean-Luc Moreau</strong>."

            st.session_state.messages.append({
                "role": "assistant",
                "content": reply,
                "time": datetime.datetime.now().strftime("%I:%M %p")
            })
            st.rerun()
