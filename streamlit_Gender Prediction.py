import re
import streamlit as st

# ==========================================
# 1. Page Config & State Initialization
# ==========================================
st.set_page_config(
    page_title="The Grand Apex | In-Room Smart Hub",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session States
if "page" not in st.session_state:
    st.session_state.page = "dashboard"  # Views: 'dashboard' or 'chat'

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Greetings Mr. Vance! I am your Grand Apex Virtual Concierge. How may I assist your stay today?"}
    ]

if "awaiting_spa_booking" not in st.session_state:
    st.session_state.awaiting_spa_booking = False

if "latest_spa_booking" not in st.session_state:
    st.session_state.latest_spa_booking = "None"

# Custom Luxury TV Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    .stApp {
        background: radial-gradient(circle at top center, #1F1D1B 0%, #0D0C0B 100%);
        color: #FDFBF7;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Top Bar */
    .tv-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0px 20px 0px;
        border-bottom: 1px solid rgba(184, 150, 92, 0.25);
        margin-bottom: 25px;
    }
    .tv-logo {
        font-family: 'Cormorant Garamond', serif;
        font-size: 24px;
        font-weight: 700;
        letter-spacing: 3px;
        color: #B8965C;
    }
    .tv-meta {
        font-size: 13px;
        color: #A09D9A;
        letter-spacing: 1px;
    }

    /* Welcome Section */
    .welcome-container {
        text-align: center;
        margin: 15px 0 35px 0;
    }
    .sub-welcome {
        font-size: 13px;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: #B8965C;
    }
    .guest-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 54px;
        font-weight: 700;
        color: #FFFFFF;
        margin: 5px 0;
    }
    .loyalty-badge {
        display: inline-block;
        background: rgba(184, 150, 92, 0.15);
        border: 1px solid #B8965C;
        color: #E2C48C;
        padding: 5px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }

    /* Info Cards */
    .info-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(184, 150, 92, 0.2);
        border-radius: 16px;
        padding: 20px;
    }
    .info-card-title {
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #A09D9A;
        margin-bottom: 10px;
    }
    .info-card-value {
        font-size: 18px;
        font-weight: 600;
        color: #FFFFFF;
    }
    .info-card-sub {
        font-size: 12px;
        color: #B8965C;
        margin-top: 4px;
    }

    /* Hide Streamlit Boilerplate */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Validation Logic
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
            return {"valid": False, "msg": "⏰ **Hours Exceeded**: Our last spa slot starts at **20:30 PM**. Please choose a time between 09:00 AM and 20:30 PM."}
        elif hour < 9:
            return {"valid": False, "msg": "⏰ **Hours Alert**: Spa opens at **09:00 AM** daily. Please select a time after 09:00 AM."}

    if not has_pax and not has_time_or_date:
        return {"valid": False, "msg": "⚠️ **Details Missing**: Please specify **both** preferred time (e.g. *1/8/2026 11:30am*) and guest count (e.g. *1 pax*)."}
    elif not has_pax:
        return {"valid": False, "msg": "⚠️ **Missing Guests**: How many guests (pax) will be attending?"}
    elif not has_time_or_date:
        return {"valid": False, "msg": "⚠️ **Missing Time**: What date and time would you like to reserve?"}

    return {"valid": True, "msg": "OK"}


# ==========================================
# 3. PAGE 1: Welcome Hub Dashboard
# ==========================================
if st.session_state.page == "dashboard":
    # Header
    st.markdown("""
    <div class="tv-header">
        <div class="tv-logo">THE GRAND APEX RESORT & SPA</div>
        <div class="tv-meta">SUITE 1808 &nbsp;|&nbsp; 10:42 AM &nbsp;|&nbsp; 28°C SUNNY</div>
    </div>
    """, unsafe_allow_html=True)

    # Welcome Banner
    st.markdown("""
    <div class="welcome-container">
        <div class="sub-welcome">Welcome to Your Suite</div>
        <div class="guest-name">Mr. Alexander Vance</div>
        <div class="loyalty-badge">⭐ Apex Platinum Honor Guest</div>
    </div>
    """, unsafe_allow_html=True)

    # Info Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">📅 Stay Duration</div>
            <div class="info-card-value">28 Jul – 03 Aug 2026</div>
            <div class="info-card-sub">Express Check-out @ 12:00 PM</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">👑 Apex Rewards</div>
            <div class="info-card-value">48,500 Points</div>
            <div class="info-card-sub">Eligible for Complimentary Dining Voucher</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        booking_disp = st.session_state.latest_spa_booking
        st.markdown(f"""
        <div class="info-card">
            <div class="info-card-title">🧖 Active Spa Booking</div>
            <div class="info-card-value">{booking_disp}</div>
            <div class="info-card-sub">{"⏳ Pending Confirmation" if booking_disp != "None" else "No Active Bookings"}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Big Launcher Button to Go to Concierge Chat
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        if st.button("💬 Launch Virtual Concierge Assistant", use_container_width=True, type="primary"):
            st.session_state.page = "chat"
            st.rerun()


# ==========================================
# 4. PAGE 2: Full-Screen Virtual Concierge Chat
# ==========================================
elif st.session_state.page == "chat":
    # Navigation Header
    h_col1, h_col2 = st.columns([4, 1])
    with h_col1:
        st.markdown("## 🛎️ Grand Apex Virtual Concierge")
        st.caption("Suite 1808 • Mr. Alexander Vance")
    with h_col2:
        if st.button("⬅️ Back to TV Home", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    st.divider()

    # Chat Container
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask about Spa booking, Dining, WiFi, or Housekeeping..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        if st.session_state.awaiting_spa_booking:
            check = validate_spa_booking(prompt)
            if not check["valid"]:
                reply = check["msg"]
            else:
                st.session_state.awaiting_spa_booking = False
                st.session_state.latest_spa_booking = prompt.strip()
                reply = f"✨ **Spa Booking Requested!**\n\nThank you, Mr. Vance. We have registered **\"{prompt.strip()}\"**.\n\nYour active reservation status has been updated on your **Room Display Dashboard**."
        else:
            if any(k in prompt.lower() for k in ["spa", "book", "facial", "massage"]):
                st.session_state.awaiting_spa_booking = True
                reply = "📅 **Apex Spa Reservation Desk**\n\nI would be delighted to assist! Please provide:\n1. **Preferred Date & Time** (e.g., *1/8/2026 11:30am*)\n2. **Number of Guests** (e.g., *1 pax*)"
            else:
                reply = "Thank you, Mr. Vance. Our Virtual Concierge Desk is entirely at your service."
                
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
