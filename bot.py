import re
import datetime
import streamlit as st

# ==========================================
# 1. Page Config & State Setup
# ==========================================
st.set_page_config(
    page_title="Grand Apex WhatsApp Concierge",
    page_icon="💬",
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

# Custom CSS for Executive WhatsApp Messenger Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,700;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Background - Warm Premium Wallpaper */
    .stApp {
        background: #E5DDD5 linear-gradient(180deg, #F4EFEA 0%, #E8E2D9 100%);
        color: #111B21;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Glassmorphism Luxury Container */
    .glass-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(197, 160, 89, 0.35);
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }

    /* ==========================================
       💬 WHATSAPP-STYLE CHAT LAYOUT & BUBBLES
       ========================================== */

    /* Hide Default Streamlit Avatar & Chat Wrappers */
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

    /* WhatsApp Header Bar */
    .wa-header {
        background: #FFFFFF;
        border: 1px solid rgba(197, 160, 89, 0.3);
        border-radius: 16px 16px 0 0;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    .wa-avatar {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #C5A059 0%, #8C6B2D 100%);
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 18px;
        box-shadow: 0 2px 8px rgba(197, 160, 89, 0.4);
    }

    /* WhatsApp Chat Body Frame */
    .wa-chat-container {
        background: #EFEAE2;
        border-left: 1px solid rgba(197, 160, 89, 0.3);
        border-right: 1px solid rgba(197, 160, 89, 0.3);
        border-bottom: 1px solid rgba(197, 160, 89, 0.3);
        border-radius: 0 0 16px 16px;
        padding: 20px;
        min-height: 480px;
    }

    /* Message Wrapper (Flex alignment) */
    .wa-msg-wrapper-user {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 12px;
    }
    .wa-msg-wrapper-assistant {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 12px;
    }

    /* Chat Bubble Tints */
    .wa-bubble {
        max-width: 82%;
        padding: 10px 14px;
        border-radius: 12px;
        font-size: 14px;
        line-height: 1.5;
        position: relative;
        box-shadow: 0 1px 2px rgba(0,0,0,0.12);
    }
    /* Assistant Bubble (Light White/Ivory) */
    .wa-bubble-assistant {
        background: #FFFFFF;
        color: #111B21;
        border-top-left-radius: 2px;
        border: 1px solid #E2E8F0;
    }
    /* User Bubble (Champagne Light Gold - Executive WhatsApp Green replacement) */
    .wa-bubble-user {
        background: #F4EAD3;
        color: #111B21;
        border-top-right-radius: 2px;
        border: 1px solid #E2D4B7;
    }

    /* Timestamp & Read Receipts */
    .wa-meta {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 4px;
        font-size: 10px;
        color: #667781;
        margin-top: 4px;
        text-align: right;
    }
    .wa-ticks {
        color: #53BDEB; /* WhatsApp Blue Checks */
        font-weight: 700;
        font-size: 12px;
    }

    /* 🎟️ VISUAL SPA TICKET PASS CARD */
    .spa-pass-card {
        background: #FFFFFF !important;
        border: 1px solid #C5A059 !important;
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0;
        box-shadow: 0 4px 12px rgba(197, 160, 89, 0.1) !important;
    }
    .pass-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px dashed #D4AF37;
        padding-bottom: 8px;
        margin-bottom: 10px;
    }
    .pass-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 18px;
        font-weight: 700;
        color: #8C6B2D !important;
    }
    .pass-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        font-size: 12px;
    }
    .pass-label {
        font-size: 9px;
        color: #667781 !important;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .pass-val {
        font-size: 13px;
        font-weight: 600;
        color: #111B21 !important;
    }

    /* 📶 VISUAL WIFI ACCESS CARD */
    .wifi-card {
        background: #FAF6F0 !important;
        border: 1px solid #C5A059 !important;
        border-radius: 10px;
        padding: 12px;
        margin: 8px 0;
    }

    /* Custom Input Bar Styling */
    [data-testid="stChatInput"] {
        background-color: #FFFFFF !important;
        border: 1px solid #C5A059 !important;
        border-radius: 24px !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
    }

    /* Executive Typography */
    .guest-name {
        font-family: 'Cormorant Garamond', serif;
        font-size: 58px;
        font-weight: 700;
        color: #111B21;
        margin: 5px 0;
    }

    /* Buttons */
    .stButton>button {
        border: 1px solid #C5A059 !important;
        background: #FFFFFF !important;
        color: #8C6B2D !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background: #C5A059 !important;
        color: #FFFFFF !important;
    }

    /* Hide Chrome */
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
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #667781; margin-bottom: 8px; font-weight: 600;">📅 Stay Duration</div>
            <div style="font-size: 20px; font-weight: 700; color: #111B21;">28 Jul – 03 Aug 2026</div>
            <div style="font-size: 12px; color: #8C6B2D; margin-top: 6px; font-weight: 500;">Express Check-out @ 12:00 PM</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #667781; margin-bottom: 8px; font-weight: 600;">👑 Apex Rewards</div>
            <div style="font-size: 20px; font-weight: 700; color: #111B21;">48,500 Points</div>
            <div style="font-size: 12px; color: #8C6B2D; margin-top: 6px; font-weight: 500;">Complimentary Spa Access Ready</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        booking_disp = st.session_state.latest_spa_booking or "No Active Bookings"
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #667781; margin-bottom: 8px; font-weight: 600;">🧖 Active Reservations</div>
            <div style="font-size: 18px; font-weight: 700; color: #111B21;">{booking_disp}</div>
            <div style="font-size: 12px; color: #8C6B2D; margin-top: 6px; font-weight: 500;">{"⏳ Pending Confirmation" if st.session_state.latest_spa_booking else "Ready for Request"}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        if st.button("💬 Open WhatsApp VIP Butler Chat", use_container_width=True):
            st.session_state.page = "chat"
            st.rerun()


# ==========================================
# 4. PAGE 2: WhatsApp VIP Concierge Suite
# ==========================================
elif st.session_state.page == "chat":
    top_c1, top_c2 = st.columns([4, 1])
    with top_c1:
        st.markdown("""
        <div>
            <div style="font-size: 12px; color: #8C6B2D; letter-spacing: 2px; text-transform: uppercase; font-weight: 600;">The Grand Apex Hospitality Network</div>
            <div style="font-family: 'Cormorant Garamond', serif; font-size: 32px; font-weight: 700; color: #111B21;">Executive VIP WhatsApp Chat</div>
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
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #667781; margin-bottom: 12px; font-weight: 600;">DUTY BUTLER</div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 10px; height: 10px; background: #25D366; border-radius: 50%;"></div>
                <div style="font-size: 15px; font-weight: 700; color: #111B21;">Jean-Luc Moreau</div>
            </div>
            <div style="font-size: 12px; color: #667781; margin-top: 4px;">Head Concierge • Ext. 801</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #667781; margin-bottom: 12px; font-weight: 600;">SUITE DETAILS</div>
            <div style="margin-bottom: 10px;">
                <div style="font-size: 11px; color: #667781;">GUEST NAME</div>
                <div style="font-weight: 700; font-size: 14px; color: #111B21;">Mr. Alexander Vance</div>
            </div>
            <div style="margin-bottom: 10px;">
                <div style="font-size: 11px; color: #667781;">ACCOMMODATION</div>
                <div style="font-weight: 700; font-size: 14px; color: #111B21;">Suite 1808 (Penthouse)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- MAIN CHAT AREA (WhatsApp Style) ---
    with main_chat_col:
        st.markdown("##### ⚡ Direct Quick Actions")
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

        # 📱 WHATSAPP HEADER BAR
        st.markdown("""
        <div class="wa-header">
            <div class="wa-avatar">GA</div>
            <div>
                <div style="font-weight: 700; font-size: 15px; color: #111B21;">Grand Apex Concierge</div>
                <div style="font-size: 11px; color: #25D366; font-weight: 600;">online • verified luxury business</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 💬 WHATSAPP CHAT CONTAINER
        chat_box = st.container(height=450)
        with chat_box:
            st.markdown('<div class="wa-chat-container">', unsafe_allow_html=True)
            for msg in st.session_state.messages:
                role = msg["role"]
                timestamp = msg.get("time", datetime.datetime.now().strftime("%I:%M %p"))
                ticks = '<span class="wa-ticks">✓✓</span>' if role == "user" else ""

                if role == "user":
                    st.markdown(f"""
                    <div class="wa-msg-wrapper-user">
                        <div class="wa-bubble wa-bubble-user">
                            {msg['content']}
                            <div class="wa-meta">{timestamp} {ticks}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="wa-msg-wrapper-assistant">
                        <div class="wa-bubble wa-bubble-assistant">
                            {msg['content']}
                            <div class="wa-meta">{timestamp}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        user_text = st.chat_input("Type a message...")
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
                    
                    # 🎟️ BRIGHT LUXURY SPA PASS CARD (WhatsApp Format)
                    reply = f"""
✨ **Spa Reservation Confirmed**

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
📅 **Apex Executive Spa Reservation**

I would be delighted to arrange your spa treatment, Mr. Vance! Please reply with:

1. **Preferred Date & Time** (e.g., `1/8/2026 11:30am`)
2. **Number of Guests** (e.g., `1 pax`)
"""
                elif "wifi" in text_low:
                    reply = """
📶 **Executive WiFi Network Credentials**

<div class="wifi-card">
    <div style="font-size: 10px; color: #667781; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">SUITE 1808 HIGH-SPEED NETWORK</div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
        <div>
            <div style="font-size: 11px; color: #667781;">NETWORK</div>
            <div style="font-size: 14px; font-weight: 700; color: #111B21;">GrandApex_VIP_1808</div>
        </div>
        <div>
            <div style="font-size: 11px; color: #667781;">PASSWORD</div>
            <div style="font-size: 14px; font-weight: 700; color: #8C6B2D;">ApexVIP1808</div>
        </div>
    </div>
</div>
"""
                elif "breakfast" in text_low or "dining" in text_low:
                    reply = """
🍽️ **In-Room Executive Dining**

Today's featured breakfast sets for **Suite 1808**:

* **👑 Truffle Omelette** — *$38*  
* **🥐 Parisian Bakery Basket** — *$28*  
* **🥑 Avocado & Egg Tartine** — *$32*  

---
💡 *Reply with your preferred items (e.g. "Order Truffle Omelette for 1 pax at 8:30am") to place your order.*
"""
                else:
                    reply = f"Thank you, Mr. Vance. I have conveyed your request regarding *\"{user_text}\"* directly to your Duty Butler, **Jean-Luc Moreau**."

            st.session_state.messages.append({
                "role": "assistant",
                "content": reply,
                "time": datetime.datetime.now().strftime("%I:%M %p")
            })
            st.rerun()
