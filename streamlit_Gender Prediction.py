import re
import streamlit as st

# ==========================================
# 1. Page Configuration (Wide Layout)
# ==========================================
st.set_page_config(
    page_title="In-Room Smart Screen | The Grand Apex",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session States
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Greetings Mr. Vance! I am your Apex Virtual Assistant. How may I assist your stay today?"}
    ]

if "awaiting_spa_booking" not in st.session_state:
    st.session_state.awaiting_spa_booking = False

if "latest_spa_booking" not in st.session_state:
    st.session_state.latest_spa_booking = "None"

# ==========================================
# 2. Luxury Full-Screen TV Styling (CSS)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Screen Background */
    .stApp {
        background: radial-gradient(circle at top center, #1F1D1B 0%, #0D0C0B 100%);
        color: #FDFBF7;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Top Navigation Bar */
    .tv-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0px 20px 0px;
        border-bottom: 1px solid rgba(184, 150, 92, 0.25);
        margin-bottom: 30px;
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

    /* Main Welcome Section */
    .welcome-container {
        text-align: center;
        margin: 20px 0 40px 0;
    }
    .sub-welcome {
        font-size: 14px;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: #B8965C;
        margin-bottom: 5px;
    }
    .guest-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 56px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #FFFFFF;
        margin: 0;
    }
    .loyalty-badge {
        display: inline-block;
        background: rgba(184, 150, 92, 0.15);
        border: 1px solid #B8965C;
        color: #E2C48C;
        padding: 6px 18px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        margin-top: 10px;
        letter-spacing: 1px;
    }

    /* Information Cards Grid */
    .info-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(184, 150, 92, 0.2);
        border-radius: 16px;
        padding: 22px;
        transition: all 0.3s ease;
    }
    .info-card-title {
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #A09D9A;
        margin-bottom: 12px;
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

    /* Hide Streamlit default components */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. Validation Logic
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
            return {"valid": False, "msg": "⏰ **Hours Exceeded**: Our last spa slot starts at **20:30 PM**. Please select an earlier time."}
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
# 4. Render Main TV Welcome Screen
# ==========================================

# Top Header Bar
st.markdown("""
<div class="tv-header">
    <div class="tv-logo">THE GRAND APEX RESORT & SPA</div>
    <div class="tv-meta">SUITE 1808 &nbsp;|&nbsp; 10:42 AM &nbsp;|&nbsp; 28°C SUNNY</div>
</div>
""", unsafe_allow_html=True)

# Main Welcome Banner
st.markdown("""
<div class="welcome-container">
    <div class="sub-welcome">Welcome to Your Suite</div>
    <div class="guest-name">Mr. Alexander Vance</div>
    <div class="loyalty-badge">⭐ Apex Platinum Honor Guest</div>
</div>
""", unsafe_allow_html=True)

# 3 Column Dashboard Cards
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
        <div class="info-card-title">🧖 Active Reservations</div>
        <div class="info-card-value">{booking_disp}</div>
        <div class="info-card-sub">{"⏳ Processing Request" if booking_disp != "None" else "No Active Bookings"}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# 5. Expandable Floating Concierge Assistant
# ==========================================
with st.expander("💬 **Open Virtual Concierge Assistant**", expanded=False):
    st.markdown("##### 🛎️ Grand Apex Concierge Service")
    
    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle Chat Input
    if prompt := st.chat_input("Ask about Spa, Dining, WiFi, or Requests..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Bot Processing
        if st.session_state.awaiting_spa_booking:
            check = validate_spa_booking(prompt)
            if not check["valid"]:
                reply = check["msg"]
            else:
                st.session_state.awaiting_spa_booking = False
                st.session_state.latest_spa_booking = prompt.strip()
                reply = f"✨ **Spa Booking Requested!**\n\nThank you Mr. Vance. We have registered **\"{prompt.strip()}\"**. Your reservation status has been updated on your room dashboard above!"
        else:
            if "spa" in prompt.lower() or "book" in prompt.lower() or "facial" in prompt.lower():
                st.session_state.awaiting_spa_booking = True
                reply = "📅 **Apex Spa Reservation Desk**\n\nI would be delighted to assist! Please provide:\n1. **Preferred Date & Time** (e.g., *1/8/2026 11:30am*)\n2. **Number of Guests** (e.g., *1 pax*)"
            else:
                reply = "Thank you Mr. Vance. Our Concierge Desk is entirely at your service."
                
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
