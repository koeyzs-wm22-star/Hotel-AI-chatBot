import re
import streamlit as st

# ==========================================
# 1. Page Config & State Setup
# ==========================================
st.set_page_config(
    page_title="Grand Apex Concierge Suite",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session States
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Good morning, Mr. Vance. I am your Apex Virtual Concierge. How may I personalize your stay today?"}
    ]

if "awaiting_spa_booking" not in st.session_state:
    st.session_state.awaiting_spa_booking = False

if "latest_spa_booking" not in st.session_state:
    st.session_state.latest_spa_booking = None

# Custom CSS for Luxury TV / Executive Hub Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Dark Luxury Aesthetic */
    .stApp {
        background: radial-gradient(circle at top center, #1C1A17 0%, #0B0A09 100%);
        color: #FDFBF7;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Glassmorphism Luxury Container */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(184, 150, 92, 0.22);
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        margin-bottom: 20px;
    }

    /* Executive Concierge Header */
    .header-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 32px;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: 1px;
    }
    .header-sub {
        font-size: 13px;
        color: #B8965C;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* Status Pulse Pill */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(46, 125, 50, 0.15);
        border: 1px solid #4CAF50;
        color: #81C784;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #4CAF50;
        border-radius: 50%;
        box-shadow: 0 0 8px #4CAF50;
    }

    /* Info Pill Tags */
    .info-tag {
        background: rgba(184, 150, 92, 0.12);
        border: 1px solid rgba(184, 150, 92, 0.3);
        color: #E2C48C;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
    }

    /* Dashboard Typography */
    .guest-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 58px;
        font-weight: 700;
        color: #FFFFFF;
        margin: 5px 0;
    }

    /* Hide Default Elements */
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
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(184, 150, 92, 0.25); padding-bottom: 15px; margin-bottom: 30px;">
        <div style="font-family: 'Cormorant Garamond', serif; font-size: 24px; font-weight: 700; color: #B8965C; letter-spacing: 3px;">THE GRAND APEX RESORT & SPA</div>
        <div style="font-size: 13px; color: #A09D9A; letter-spacing: 1px;">SUITE 1808 &nbsp;|&nbsp; 10:42 AM &nbsp;|&nbsp; 28°C SUNNY</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin: 20px 0 40px 0;">
        <div style="font-size: 13px; letter-spacing: 4px; text-transform: uppercase; color: #B8965C;">Welcome to Your Suite</div>
        <div class="guest-name">Mr. Alexander Vance</div>
        <div style="display: inline-block; background: rgba(184, 150, 92, 0.15); border: 1px solid #B8965C; color: #E2C48C; padding: 6px 18px; border-radius: 20px; font-size: 13px; font-weight: 600;">⭐ Apex Platinum VIP Honor Guest</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #A09D9A; margin-bottom: 8px;">📅 Stay Duration</div>
            <div style="font-size: 20px; font-weight: 600; color: #FFF;">28 Jul – 03 Aug 2026</div>
            <div style="font-size: 12px; color: #B8965C; margin-top: 6px;">Express Check-out @ 12:00 PM</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #A09D9A; margin-bottom: 8px;">👑 Apex Rewards</div>
            <div style="font-size: 20px; font-weight: 600; color: #FFF;">48,500 Points</div>
            <div style="font-size: 12px; color: #B8965C; margin-top: 6px;">Eligible for Complimentary Spa Service</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        booking_disp = st.session_state.latest_spa_booking or "No Active Bookings"
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #A09D9A; margin-bottom: 8px;">🧖 Active Reservations</div>
            <div style="font-size: 18px; font-weight: 600; color: #FFF;">{booking_disp}</div>
            <div style="font-size: 12px; color: #B8965C; margin-top: 6px;">{"⏳ Request Under Review" if st.session_state.latest_spa_booking else "Ready for Booking"}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        if st.button("💬 Open Private Executive Concierge", use_container_width=True, type="primary"):
            st.session_state.page = "chat"
            st.rerun()


# ==========================================
# 4. PAGE 2: Ultra-Premium Concierge Suite
# ==========================================
elif st.session_state.page == "chat":
    # Top Navigation Row
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

    # Layout: Left Sidebar Context (1) + Main Chat (2.8)
    left_col, main_chat_col = st.columns([1, 2.8], gap="large")

    # --- LEFT SIDEBAR: Suite Context & Status ---
    with left_col:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #A09D9A; margin-bottom: 12px;">BUTLER ASSIGNMENT</div>
            <div class="status-badge"><span class="pulse-dot"></span> Duty Butler: Online</div>
            <div style="font-size: 15px; font-weight: 600; color: #FFF; margin-top: 14px;">Jean-Luc Moreau</div>
            <div style="font-size: 12px; color: #A09D9A;">Private Butler Service (Ext. 801)</div>
        </div>
        """, unsafe_allow_html=True)

        # Suite Info Panel
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #A09D9A; margin-bottom: 12px;">SUITE DETAILS</div>
            <div style="margin-bottom: 10px;">
                <div style="font-size: 11px; color: #A09D9A;">GUEST</div>
                <div style="font-weight: 600; font-size: 14px; color: #FFF;">Mr. Alexander Vance</div>
            </div>
            <div style="margin-bottom: 10px;">
                <div style="font-size: 11px; color: #A09D9A;">ACCOMMODATION</div>
                <div style="font-weight: 600; font-size: 14px; color: #FFF;">Suite 1808 (Penthouse)</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #A09D9A;">TIER STATUS</div>
                <div style="color: #B8965C; font-weight: 600; font-size: 13px;">⭐ Apex Platinum</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Active Requests Widget
        booking_status = st.session_state.latest_spa_booking or "None"
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #A09D9A; margin-bottom: 12px;">ACTIVE SUITE REQUESTS</div>
            <div style="font-size: 13px; color: #FFF; margin-bottom: 6px;"><b>Spa Booking:</b></div>
            <div class="info-tag">{booking_status}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- MAIN CHAT AREA ---
    with main_chat_col:
        # Quick Action Prompt Chips
        st.markdown("##### ⚡ Quick Service Request")
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

        # Message Stream Container
        chat_box = st.container(height=420)
        with chat_box:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Capture Chat Input (or Trigger from Quick Action Chips)
        user_text = st.chat_input("Message your Virtual Concierge...")
        
        if prompt_input:
            user_text = prompt_input

        if user_text:
            st.session_state.messages.append({"role": "user", "content": user_text})
            
            # Response Handler
            if st.session_state.awaiting_spa_booking:
                check = validate_spa_booking(user_text)
                if not check["valid"]:
                    reply = check["msg"]
                else:
                    st.session_state.awaiting_spa_booking = False
                    st.session_state.latest_spa_booking = user_text.strip()
                    reply = f"✨ **Spa Reservation Requested!**\n\nThank you, Mr. Vance. I have recorded your reservation request for **\"{user_text.strip()}\"**.\n\nYour active status has been synced to your **Executive Suite Dashboard**."
            else:
                if any(k in user_text.lower() for k in ["spa", "book", "facial", "massage", "reserve"]):
                    st.session_state.awaiting_spa_booking = True
                    reply = "📅 **Apex Spa Reservation Desk**\n\nI would be delighted to arrange your spa treatment, Mr. Vance. Please provide:\n\n1. **Preferred Date & Time** (e.g., *1/8/2026 11:30am*)\n2. **Number of Guests** (e.g., *1 pax*)"
                elif "wifi" in user_text.lower():
                    reply = "📶 **Suite 1808 Premium WiFi**\n\n• **Network:** `GrandApex_VIP_Suite`\n• **Password:** `ApexVIP1808`\n\nEnjoy complimentary high-speed access throughout the property."
                elif "breakfast" in user_text.lower() or "dining" in user_text.lower():
                    reply = "🍽️ **In-Room Executive Dining**\n\nBreakfast is served daily from **06:30 AM to 11:00 AM**. Would you like me to place an order for **Chef's Signature Breakfast** or send the full menu to your suite screen?"
                else:
                    reply = f"Thank you, Mr. Vance. I have conveyed your message regarding *\"{user_text}\"* to your Duty Butler, Jean-Luc Moreau."

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
