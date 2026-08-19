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
from difflib import get_close_matches
from collections import Counter
from datetime import datetime, timedelta

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

# Chat History State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Greetings! It is my absolute pleasure to welcome you to The Grand Apex Resort & Spa. How may I assist your stay today?",
            "time": datetime.now().strftime("%I:%M %p")
        }
    ]

# Spa Reservation Context States
if "awaiting_spa_booking" not in st.session_state:
    st.session_state.awaiting_spa_booking = False

if "latest_spa_booking" not in st.session_state:
    st.session_state.latest_spa_booking = None

# Spa Booking Database (In-memory simulation)
if "spa_bookings" not in st.session_state:
    st.session_state.spa_bookings = {
        "2026-07-28 10:00": {"guest_name": "Mr. Johnson", "service": "Aromatherapy Massage", "duration": 60},
        "2026-07-28 11:00": {"guest_name": "Ms. Lee", "service": "Deep Tissue Massage", "duration": 60},
        "2026-07-28 14:00": {"guest_name": "Mr. Tan", "service": "Hot Stone Therapy", "duration": 90},
        "2026-07-29 09:00": {"guest_name": "Mrs. Wong", "service": "Hydrating Facial", "duration": 60},
        "2026-07-29 15:00": {"guest_name": "Mr. Smith", "service": "Aromatherapy Massage", "duration": 60},
    }

if "temp_booking_data" not in st.session_state:
    st.session_state.temp_booking_data = {}


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
            "time": datetime.now().strftime("%I:%M %p")
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

def correct_spelling(text):
    """Corrects common spelling mistakes using a dictionary of keywords."""
    if not text or len(text) < 2:
        return text
    
    common_typos = {
        'wheather': 'weather',
        'wether': 'weather',
        'weater': 'weather',
        'weathr': 'weather',
        'forcast': 'forecast',
        'temprature': 'temperature',
        'wify': 'wifi',
        'pasword': 'password',
        'conect': 'connect',
        'intenet': 'internet',
        'masage': 'massage',
        'massge': 'massage',
        'reservasion': 'reservation',
        'appontment': 'appointment',
        'breakfat': 'breakfast',
        'breakfirst': 'breakfast',
        'brakfast': 'breakfast',
        'chackin': 'check-in',
        'servises': 'services',
        'ameneties': 'amenities',
        'resturant': 'restaurant',
        'spa': 'spa',
    }
    
    words = text.split()
    corrected_words = []
    
    for word in words:
        if word.lower() in common_typos:
            corrected_words.append(common_typos[word.lower()])
        else:
            if len(word) > 3:
                close_matches = get_close_matches(word.lower(), common_typos.keys(), n=1, cutoff=0.8)
                if close_matches:
                    corrected_words.append(common_typos[close_matches[0]])
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
    
    return ' '.join(corrected_words)

def spell_check_and_correct(user_input):
    """Main function to check and correct spelling in user input."""
    original = user_input
    corrected = correct_spelling(original)
    
    if corrected != original:
        return corrected, True
    return original, False


# ==========================================
# 3. Spa Booking Validation System
# ==========================================
def parse_booking_datetime(date_str, time_str):
    """
    Parse user's date and time input into datetime object.
    Enhanced with better handling of ambiguous times.
    Returns (datetime_obj, error_message)
    """
    try:
        # Parse date
        date_obj = None
        date_formats = [
            "%Y-%m-%d",  # 2026-07-28
            "%d/%m/%Y",  # 28/07/2026
            "%d-%m-%Y",  # 28-07-2026
            "%d %B %Y",  # 28 July 2026
            "%B %d %Y",  # July 28 2026
            "%d-%b-%Y",  # 28-Jul-2026
            "%b %d %Y",  # Jul 28 2026
            "%Y%m%d",    # 20260728
        ]
        
        # Handle "today", "tomorrow", "next week" keywords
        date_lower = date_str.lower().strip()
        if date_lower in ["today", "todays"]:
            date_obj = datetime.now()
        elif date_lower in ["tomorrow", "tmr", "tomorow"]:
            date_obj = datetime.now() + timedelta(days=1)
        elif date_lower in ["day after tomorrow", "day after tmr"]:
            date_obj = datetime.now() + timedelta(days=2)
        elif "next week" in date_lower:
            date_obj = datetime.now() + timedelta(days=7)
        else:
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    break
                except ValueError:
                    continue
        
        if not date_obj:
            return None, "I couldn't understand the date format. Please use format like '2026-07-28', '28/07/2026', 'today', or 'tomorrow'."
        
        # Parse time with enhanced validation
        time_str_clean = time_str.strip().lower()
        
        # Handle special time cases
        if time_str_clean in ["now", "right now", "asap"]:
            time_obj = datetime.now()
        elif time_str_clean in ["noon", "midday", "12 noon"]:
            time_obj = datetime.strptime("12:00 PM", "%I:%M %p")
        elif time_str_clean in ["midnight", "12 midnight"]:
            time_obj = datetime.strptime("12:00 AM", "%I:%M %p")
        else:
            # Try to parse with various formats
            time_formats = [
                ("%I:%M %p", True),  # 2:30 PM - with AM/PM
                ("%I:%M%p", True),   # 2:30PM - no space
                ("%I %p", True),     # 2 PM
                ("%I%p", True),      # 2PM
                ("%H:%M", False),    # 14:30 - 24-hour
                ("%H%M", False),     # 1430 - 24-hour
                ("%I", True),        # 2 - AMBIGUOUS!
                ("%H", False),       # 14 - 24-hour
            ]
            
            time_obj = None
            has_am_pm = False
            
            for fmt, has_ampm_flag in time_formats:
                try:
                    time_obj = datetime.strptime(time_str_clean, fmt)
                    has_am_pm = has_ampm_flag
                    break
                except ValueError:
                    continue
            
            # If parsing failed, try with ":" variations
            if not time_obj and ":" in time_str_clean:
                try:
                    parts = time_str_clean.split(":")
                    if len(parts) == 2:
                        hour = int(parts[0])
                        minute = int(parts[1])
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            time_obj = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                except:
                    pass
            
            # If still no time_obj, try to parse digits only
            if not time_obj:
                digits = re.findall(r'\d+', time_str_clean)
                if digits:
                    hour = int(digits[0])
                    minute = int(digits[1]) if len(digits) > 1 else 0
                    
                    # Determine if it's AM or PM based on context
                    am_pm = None
                    
                    if "am" in time_str_clean:
                        am_pm = "AM"
                    elif "pm" in time_str_clean:
                        am_pm = "PM"
                    elif "morning" in time_str_clean:
                        am_pm = "AM"
                    elif "afternoon" in time_str_clean or "evening" in time_str_clean or "night" in time_str_clean:
                        am_pm = "PM"
                    elif hour < 6:
                        am_pm = "AM"
                    elif 6 <= hour < 12:
                        am_pm = "AM"
                    elif hour == 12:
                        if "night" in time_str_clean or "midnight" in time_str_clean:
                            am_pm = "AM"
                        else:
                            am_pm = "PM"
                    elif hour > 12:
                        am_pm = "PM"
                    
                    if not am_pm:
                        if "noon" in time_str_clean:
                            hour = 12
                            minute = 0
                            am_pm = "PM"
                        elif "midnight" in time_str_clean:
                            hour = 12
                            minute = 0
                            am_pm = "AM"
                        else:
                            if hour == 12:
                                am_pm = "PM"
                            elif hour < 6:
                                am_pm = "AM"
                            elif hour < 12:
                                am_pm = "AM" if hour < 9 else "PM"
                            else:
                                am_pm = "PM"
                    
                    if am_pm == "PM" and hour < 12:
                        hour += 12
                    elif am_pm == "AM" and hour == 12:
                        hour = 0
                    
                    if minute < 0 or minute > 59:
                        minute = 0
                    
                    time_obj = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if not time_obj:
            return None, "I couldn't understand the time format. Please use format like '14:30', '2:30 PM', '2 PM', or '2' (I'll assume 2:00 PM)."
        
        # Combine date and time
        booking_datetime = date_obj.replace(
            hour=time_obj.hour,
            minute=time_obj.minute,
            second=0,
            microsecond=0
        )
        
        # Validate the booking time is within operating hours
        if booking_datetime.hour < 9 or booking_datetime.hour >= 22:
            if booking_datetime.date() > datetime.now().date():
                if booking_datetime.hour < 9:
                    return None, f"⚠️ Our spa opens at 9:00 AM. Would you like me to book you for 9:00 AM instead? <br><br>💡 <i>Our operating hours are 9:00 AM to 10:00 PM.</i>"
                else:
                    return None, f"⚠️ Our spa closes at 10:00 PM. The latest appointment we can take is 9:30 PM. <br><br>💡 <i>Our operating hours are 9:00 AM to 10:00 PM.</i>"
        
        return booking_datetime, None
        
    except Exception as e:
        return None, f"I couldn't understand the date/time. Please try again with format like '2026-07-28 at 14:30' or 'tomorrow at 2 PM'."

def is_spa_slot_available(booking_datetime, duration_minutes=60, exclude_booking=None):
    """
    Check if a spa time slot is available.
    Returns (is_available, conflicting_bookings)
    """
    if booking_datetime < datetime.now():
        return False, "Past Booking"
    
    if booking_datetime.hour < 9 or booking_datetime.hour >= 22:
        return False, "Outside Operating Hours"
    
    booking_end = booking_datetime + timedelta(minutes=duration_minutes)
    conflicting_bookings = []
    
    for slot, booking in st.session_state.spa_bookings.items():
        if exclude_booking and slot == exclude_booking:
            continue
            
        existing_start = datetime.strptime(slot, "%Y-%m-%d %H:%M")
        existing_end = existing_start + timedelta(minutes=booking.get("duration", 60))
        
        if (booking_datetime < existing_end and booking_end > existing_start):
            conflicting_bookings.append({
                "time": slot,
                "guest": booking["guest_name"],
                "service": booking["service"]
            })
    
    if conflicting_bookings:
        return False, conflicting_bookings
    
    return True, None

def format_conflict_message(conflicting_bookings):
    """Format conflict message for display"""
    message = "❌ <strong>Unfortunately, that time slot is already booked:</strong><br><br>"
    for booking in conflicting_bookings:
        dt = datetime.strptime(booking["time"], "%Y-%m-%d %H:%M")
        message += f"• <strong>{dt.strftime('%I:%M %p')}</strong> - {booking['guest']} ({booking['service']})<br>"
    message += "<br>🕐 <i>Please choose a different time. I can help you find an available slot!</i>"
    return message

def get_available_spa_slots(date_obj=None, duration_minutes=60):
    """Get available spa slots for a given date (or today)"""
    if not date_obj:
        date_obj = datetime.now()
    
    available_slots = []
    start_hour = 9
    end_hour = 22
    
    current_time = date_obj.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end_time = date_obj.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    
    while current_time < end_time:
        if current_time > datetime.now() + timedelta(minutes=30):
            is_available, conflict = is_spa_slot_available(current_time, duration_minutes)
            if is_available:
                available_slots.append(current_time.strftime("%I:%M %p"))
        
        current_time += timedelta(minutes=30)
    
    return available_slots

def book_spa_slot(guest_name, service, booking_datetime, duration_minutes=60):
    """
    Book a spa slot
    Returns (success, message)
    """
    if booking_datetime < datetime.now():
        return False, "❌ Booking date and time cannot be in the past. Please select a future date and time."
    
    is_available, conflict = is_spa_slot_available(booking_datetime, duration_minutes)
    
    if not is_available:
        if conflict == "Past Booking":
            return False, "❌ Cannot book in the past. Please select a future date and time."
        elif conflict == "Outside Operating Hours":
            return False, "❌ Our spa operates from 9:00 AM to 10:00 PM. Please select a time within these hours."
        elif isinstance(conflict, list):
            return False, format_conflict_message(conflict)
        else:
            return False, "❌ This time slot is not available. Please choose another time."
    
    slot_key = booking_datetime.strftime("%Y-%m-%d %H:%M")
    st.session_state.spa_bookings[slot_key] = {
        "guest_name": guest_name,
        "service": service,
        "duration": duration_minutes
    }
    
    return True, f"✅ <strong>Booking Confirmed!</strong><br><br>📅 <strong>Date:</strong> {booking_datetime.strftime('%A, %B %d, %Y')}<br>🕐 <strong>Time:</strong> {booking_datetime.strftime('%I:%M %p')}<br>💆 <strong>Service:</strong> {service}<br>👤 <strong>Guest:</strong> {guest_name}<br><br>Please arrive 15 minutes early for your appointment."


# ==========================================
# 4. Real-Time Weather API Integration with Attractions
# ==========================================
def get_realtime_weather():
    """Fetches real-time weather using Open-Meteo API with WMO translation and attraction suggestions."""
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            "latitude=3.139&longitude=101.6869&"
            "current_weather=true&"
            "daily=weathercode,temperature_2m_max,temperature_2m_min&"
            "timezone=auto"
        )
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            def parse_wmo(code):
                if code in [0, 1]: 
                    return "☀️ Clear & Sunny", "sunny"
                elif code in [2, 3]: 
                    return "⛅ Light Clouds", "cloudy"
                elif code in [45, 48]: 
                    return "🌫️ Mist & Fog", "foggy"
                elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95]: 
                    return "🌧️ Gentle Rain", "rainy"
                elif code in [71, 73, 75, 77]: 
                    return "❄️ Snow", "snowy"
                elif code in [96, 99]: 
                    return "⛈️ Thunderstorm", "stormy"
                return "🌤️ Pleasant", "pleasant"

            current = data.get("current_weather", {})
            curr_temp = current.get("temperature", 28)
            curr_code = current.get("weathercode", 0)
            weather_condition, weather_type = parse_wmo(curr_code)
            
            daily = data.get("daily", {})
            dates = daily.get("time", ["Today", "Tomorrow", "Day After"])
            max_temps = daily.get("temperature_2m_max", [30, 31, 30])
            min_temps = daily.get("temperature_2m_min", [24, 24, 25])

            attraction_suggestions = get_attraction_suggestions(weather_type, curr_temp)

            return {
                "success": True,
                "temp": curr_temp,
                "condition": weather_condition,
                "weather_type": weather_type,
                "formatted_text": (
                    f"🌤️ <strong>Grand Apex Advisory Weather Service</strong><br><br>"
                    f"It is currently <strong>{curr_temp}°C</strong> with <strong>{weather_condition}</strong> over the resort grounds.<br><br>"
                    f"<strong>3-Day Horizon:</strong><br>"
                    f"• <strong>Today ({dates[0]})</strong>: {min_temps[0]}°C to {max_temps[0]}°C<br>"
                    f"• <strong>Tomorrow ({dates[1]})</strong>: {min_temps[1]}°C to {max_temps[1]}°C<br>"
                    f"• <strong>Day After ({dates[2]})</strong>: {min_temps[2]}°C to {max_temps[2]}°C<br><br>"
                    f"{attraction_suggestions}<br><br>"
                    f"🌂 <i>Should you wish to step out for sightseeing, luxury umbrellas and chauffeur-driven limousines are available at the Concierge Desk.</i>"
                )
            }
        else:
            return {
                "success": False,
                "temp": 28,
                "condition": "☀️ Sunny & Warm",
                "weather_type": "sunny",
                "formatted_text": (
                    "☀️ The weather around Grand Apex is delightfully warm (28°C). "
                    "Perfect day to explore the Petronas Twin Towers and KLCC Park! "
                    "Please let me know if you would like me to arrange a chauffeur for you."
                )
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "temp": 32,
            "condition": "☀️ Sunny & Warm",
            "weather_type": "sunny",
            "formatted_text": (
                "☀️ <strong>Kuala Lumpur Weather Update</strong><br><br>"
                "Kuala Lumpur is experiencing its typical warm tropical weather today.<br><br>"
                "🌡️ <strong>Current Weather:</strong><br>"
                "• Temperature: ~32°C (89°F)<br>"
                "• Conditions: Warm and humid<br><br>"
                "🏙️ <strong>Recommended Activities:</strong><br><br>"
                "🏗️ <strong>Petronas Twin Towers</strong> — Visit the Skybridge for panoramic views<br><br>"
                "🛍️ <strong>Suria KLCC</strong> — World-class shopping experience<br><br>"
                "🧖‍♀️ <strong>Apex Executive Spa</strong> — Perfect for relaxing indoors<br><br>"
                "💡 <strong>Pro Tip:</strong> Stay hydrated and enjoy the air-conditioned attractions!<br><br>"
                "🌂 <i>Our Concierge Desk can arrange transportation to any attraction you'd like to visit.</i>"
            )
        }
    except Exception:
        return {
            "success": False,
            "temp": 28,
            "condition": "☀️ Sunny & Clear",
            "weather_type": "sunny",
            "formatted_text": (
                "☀️ Weather forecast updated: Mild and suitable for local exploration. "
                "I recommend visiting the Batu Caves or taking a Kuala Lumpur city tour. "
                "May I reserve a table at our Sky Garden Lounge for you?"
            )
        }

def get_attraction_suggestions(weather_type, temperature):
    """Returns attraction suggestions based on weather conditions in Kuala Lumpur."""
    
    attractions = {
        "sunny": f"""
🏙️ <strong>Perfect Day for Sightseeing! ({temperature}°C)</strong><br><br>
✨ <strong>Top Attractions to Visit Today:</strong><br><br>
🏗️ <strong>Petronas Twin Towers</strong> — Iconic landmark with breathtaking views from the Skybridge (Open 10:00 AM - 6:00 PM)<br><br>
🌳 <strong>KLCC Park</strong> — Beautiful urban park with a 1.3km jogging trail and Lake Symphony (Light show at 8:00 PM)<br><br>
🛍️ <strong>Pavilion KL</strong> — Premier shopping mall with luxury brands and fine dining<br><br>
🏛️ <strong>Islamic Arts Museum Malaysia</strong> — World-class collection of Islamic decorative arts<br><br>
🕌 <strong>National Mosque of Malaysia</strong> — Stunning modern Islamic architecture (Visitors welcome 9:00 AM - 5:00 PM)<br><br>
💡 <strong>Pro Tip:</strong> Morning visits are recommended to avoid the midday heat!
""",
        "cloudy": f"""
⛅ <strong>Great Day for Exploring! ({temperature}°C)</strong><br><br>
✨ <strong>Top Attractions for Cloudy Weather:</strong><br><br>
🏛️ <strong>National Museum of Malaysia</strong> — Discover Malaysian history and culture (Open 9:00 AM - 5:00 PM)<br><br>
🐟 <strong>Aquaria KLCC</strong> — Stunning underwater world at the Petronas Twin Towers<br><br>
🕌 <strong>Sultan Abdul Samad Building</strong> — Beautiful Moorish-style architecture in Merdeka Square<br><br>
🎨 <strong>Bank Negara Malaysia Museum</strong> — Interactive museum featuring currency and art galleries<br><br>
🎭 <strong>Istana Budaya</strong> — The National Theatre offering cultural performances<br><br>
💡 <strong>Pro Tip:</strong> Perfect weather for both indoor and outdoor activities!
""",
        "rainy": f"""
🌧️ <strong>Indoor Adventures Recommended! ({temperature}°C)</strong><br><br>
✨ <strong>Top Indoor Attractions for Rainy Days:</strong><br><br>
🛍️ <strong>Pavilion KL & Suria KLCC</strong> — World-class shopping with covered walkways connecting malls<br><br>
🐟 <strong>Aquaria KLCC</strong> — Spectacular underwater tunnel and marine life exhibits<br><br>
🎨 <strong>KLCC Art Gallery</strong> — Contemporary Malaysian art exhibitions<br><br>
🖼️ <strong>National Art Gallery</strong> — Explore Malaysian artistic heritage<br><br>
🎭 <strong>Theatre & Cinema</strong> — Catch a movie or stage performance at Pavilion KL<br><br>
🍽️ <strong>Food Court Exploration</strong> — Enjoy Malaysian street food in air-conditioned comfort at Lot 10 Hutong<br><br>
💡 <strong>Pro Tip:</strong> All attractions are connected via covered walkways or underground tunnels!
""",
        "foggy": f"""
🌫️ <strong>Indoor & Low-Altitude Activities ({temperature}°C)</strong><br><br>
✨ <strong>Recommended Activities:</strong><br><br>
🛍️ <strong>KL Gateway Mall</strong> — Shopping with a view of the KL skyline<br><br>
🐟 <strong>Aquaria KLCC</strong> — Perfect indoor attraction for all ages<br><br>
📚 <strong>Rumah Penghulu</strong> — Traditional Malay house museum at KLCC<br><br>
🎨 <strong>Canvas Gallery</strong> — Contemporary art exhibitions<br><br>
💡 <strong>Pro Tip:</strong> Great day for spa treatments at our Apex Executive Wellness & Spa!
""",
        "pleasant": f"""
🌤️ <strong>Perfect Weather for Exploration! ({temperature}°C)</strong><br><br>
✨ <strong>Must-Visit Attractions:</strong><br><br>
🏙️ <strong>Petronas Twin Towers & Skybridge</strong> — Iconic views of the city<br><br>
🌸 <strong>Perdana Botanical Garden</strong> — Beautiful tropical gardens with orchid garden<br><br>
🛍️ <strong>Central Market</strong> — Arts and crafts paradise<br><br>
🏛️ <strong>Kuala Lumpur City Gallery</strong> — KL's history and culture<br><br>
🌳 <strong>FRIM Forest Reserve</strong> — Canopy walkway and nature trails<br><br>
💡 <strong>Pro Tip:</strong> Consider visiting both outdoor and indoor attractions!
"""
    }
    
    return attractions.get(weather_type, attractions["pleasant"])


# ==========================================
# 5. Internal Call & VIP Pass Card Generators
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
    """Generates the visual VIP Pass for spa bookings."""
    return f"""
✨ <strong>Spa Reservation Confirmed</strong>

<div class="spa-pass-card">
    <div class="pass-header">
        <div class="pass-title">GH EXECUTIVE SPA VIP PASS</div>
        <div style="background: #4CAF50; border: 1px solid #2E7D32; color: white; font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 700;">
            ✅ CONFIRMED
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
# 6. ML Classifier & Response Pipeline
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
1. <strong>Your preferred date & time</strong> (e.g., Today at 15:00 PM or 2026-07-28 at 14:30)<br>
2. <strong>Service type</strong> (e.g., Aromatherapy Massage, Deep Tissue, Hot Stone, Facial)<br><br>
<i>💡 I'll check availability and confirm your booking!</i><br><br>
Alternatively, you may dial <strong>Ext '802'</strong> to speak directly with our Spa Receptionist for immediate confirmation.
""",
    "ask_dining": "🍽️ <strong>Gastronomic Experiences</strong><br><br>The Grand Apex features three award-winning venues:<br>1. <strong>L'Aura (Floor 48)</strong> - Michelin French Fine Dining<br>2. <strong>Sakura Sky Lounge (Floor 49)</strong> - Contemporary Omakase<br>3. <strong>The Atrium (Floor 1)</strong> - All-Day International Buffet",
    "ask_attractions": """
🏙️ <strong>Top Attractions in Kuala Lumpur</strong><br><br>
✨ <strong>Must-Visit Places:</strong><br><br>
🏗️ <strong>Petronas Twin Towers</strong> — Iconic landmark with Skybridge and observation deck<br><br>
🌳 <strong>KLCC Park</strong> — Beautiful urban park with jogging trail and Lake Symphony<br><br>
🛍️ <strong>Pavilion KL & Suria KLCC</strong> — Premier shopping destinations<br><br>
🏛️ <strong>Islamic Arts Museum</strong> — World-class Islamic art collection<br><br>
🕌 <strong>National Mosque</strong> — Stunning modern Islamic architecture<br><br>
🐟 <strong>Aquaria KLCC</strong> — Spectacular underwater world experience<br><br>
🌸 <strong>Perdana Botanical Garden</strong> — Tropical gardens and orchid display<br><br>
🖼️ <strong>National Art Gallery</strong> — Malaysian artistic heritage<br><br>
📞 For transportation arrangements, please dial <strong>Ext '0'</strong> for our Concierge Desk!
"""
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

    # Internal Call Training Samples
    call_patterns = ["call front desk", "call butler", "internal call", "phone number", "contact housekeeping", "call hotel", "dial front desk", "phone front desk", "打电话", "联系前台", "呼叫管家", "打给前台", "内线电话"]
    for p in call_patterns:
        X.append(clean_text(p))
        y.append("internal_call")

    # Services Training Samples
    service_patterns = [
        "what services do you have", "what services", "hotel services", "services", 
        "what amenities are available", "amenities", "what can I do at this hotel", 
        "hotel facilities", "list your services", "what do you offer", "facilities",
        "有什么服务", "酒店有什么设施", "你们提供什么服务", "服务项目"
    ]
    for p in service_patterns:
        X.append(clean_text(p))
        y.append("ask_services")

    # Spa Menu & Pricing Samples
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
        "怎么预约spa", "帮我订spa", "我想做spa", "预约spa", "book spa treatment"
    ]
    for p in booking_patterns:
        X.append(clean_text(p))
        y.append("ask_spa_booking")

    # Weather patterns
    weather_patterns = [
        "weather", "weather forecast", "today weather", "tomorrow weather", 
        "what is the weather", "how is the weather", "weather today", 
        "天气预报", "今天天气", "明天天气", "weather in kuala lumpur",
        "what's the weather like", "is it raining", "will it rain", "温度",
        "temperature", "how hot is it", "is it sunny"
    ]
    for p in weather_patterns:
        X.append(clean_text(p))
        y.append("ask_weather")

    # Attractions patterns
    attractions_patterns = [
        "what to do in kuala lumpur", "tourist attractions", "places to visit",
        "sightseeing", "tourist spots", "things to do", "吉隆坡有什么好玩的",
        "旅游景点", "去哪里玩", "观光推荐"
    ]
    for p in attractions_patterns:
        X.append(clean_text(p))
        y.append("ask_attractions")

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

def process_spa_booking(user_input):
    """
    Process spa booking request with validation
    """
    input_lower = user_input.lower()
    
    # --- CHECK: If this is a weather query, handle it immediately ---
    weather_keywords = ["weather", "temperature", "forecast", "rain", "sunny", "cloudy", "degrees", "°c", "°f"]
    if any(keyword in input_lower for keyword in weather_keywords):
        weather_res = get_realtime_weather()
        return weather_res["formatted_text"]
    
    # Default values
    date_str = None
    time_str = None
    service = "Aromatherapy Massage"  # Default service
    duration = 60
    
    # Extract service type
    services = {
        "aromatherapy": "Aromatherapy Massage",
        "deep tissue": "Deep Tissue Massage",
        "hot stone": "Hot Stone Therapy",
        "facial": "Hydrating Facial",
        "swedish": "Swedish Massage",
        "reflexology": "Reflexology"
    }
    
    for key, value in services.items():
        if key in input_lower:
            service = value
            break
    
    # Extract time - improved to handle standalone numbers
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)?',  # 14:30 or 2:30pm
        r'(\d{1,2})\s*(am|pm)\s*(?:o\'clock)?',  # 2pm or 3am
        r'(\d{1,2})\s*o\'clock',  # 2 o'clock
        r'(\d{1,2})\s*(?:in the)?\s*(morning|afternoon|evening|night)',  # 2 in the afternoon
        r'^(\d{1,2})$',  # Standalone number like "12"
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, input_lower, re.IGNORECASE)
        if match:
            groups = match.groups()
            
            if len(groups) == 3 and groups[0] and groups[1]:  # HH:MM AM/PM
                hour = int(groups[0])
                minute = int(groups[1])
                ampm = groups[2].lower() if groups[2] else None
                
                if ampm:
                    if ampm == 'pm' and hour < 12:
                        hour += 12
                    elif ampm == 'am' and hour == 12:
                        hour = 0
                else:
                    if hour < 9:
                        pass
                    elif hour == 12:
                        hour = 12
                    else:
                        if hour < 9:
                            hour = hour
                        else:
                            hour = hour
                
                time_str = f"{hour:02d}:{minute:02d}"
                
            elif len(groups) == 2:  # HH AM/PM or HH o'clock
                hour = int(groups[0])
                if len(groups) > 1 and groups[1]:
                    ampm = groups[1].lower() if groups[1] else None
                    if ampm in ['am', 'pm']:
                        if ampm == 'pm' and hour < 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    else:
                        if hour < 9:
                            hour = hour
                        else:
                            hour = hour
                else:
                    if hour < 9:
                        hour = hour
                    else:
                        hour = hour
                
                time_str = f"{hour:02d}:00"
            
            elif len(groups) == 1 and groups[0]:  # Standalone number
                hour = int(groups[0])
                if "am" in input_lower:
                    if hour == 12:
                        hour = 0
                elif "pm" in input_lower:
                    if hour < 12:
                        hour += 12
                else:
                    if hour < 9:
                        pass
                    elif hour == 12:
                        hour = 12
                    else:
                        if hour < 6:
                            hour = hour
                        else:
                            hour = hour
                
                time_str = f"{hour:02d}:00"
            
            break
    
    # Extract date
    date_patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2026-07-28
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 28/07/2026
        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # 28-07-2026
        r'today',
        r'tomorrow',
        r'tmr',
        r'day after tomorrow',
        r'next week',
        r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})',  # 28 Jul 2026
    ]
    
    for pattern in date_patterns:
        if isinstance(pattern, str):
            if pattern in input_lower:
                if pattern == 'today':
                    date_str = datetime.now().strftime("%Y-%m-%d")
                elif pattern in ['tomorrow', 'tmr']:
                    date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                elif pattern == 'day after tomorrow':
                    date_str = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                elif pattern == 'next week':
                    date_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                break
        else:
            match = re.search(pattern, input_lower, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    if len(match.group(1)) == 4:
                        year, month, day = match.groups()
                    else:
                        day, month, year = match.groups()
                    if month.isalpha():
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        month = month_map.get(month.lower(), int(month))
                    else:
                        month = int(month)
                    date_str = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                break
    
    # If date and time are not provided, ask for more details
    if not date_str or not time_str:
        response = "📅 I need a bit more information to book your spa appointment:<br><br>"
        if not date_str:
            response += "• <strong>Date</strong>: Please tell me the date (e.g., 'today', 'tomorrow', or '2026-07-28')<br>"
        if not time_str:
            response += "• <strong>Time</strong>: Please tell me the time (e.g., '2:30 PM', '14:30', or '2' for 2:00 PM)<br>"
        response += "<br>💆 <strong>Service selected</strong>: " + service
        response += "<br><br>Please provide the missing information, and I'll check availability for you!"
        
        if not time_str:
            response += "<br><br>💡 <i>Tip: If you just say '2', I'll assume 2:00 PM. To book in the morning, say '9 AM'.</i>"
        return response
    
    # Check if time is a standalone number and give a friendly reminder
    if time_str and re.match(r'^\d{1,2}$', time_str.strip()):
        hour = int(time_str.strip())
        if hour < 9:
            response = f"💡 <i>I see you said '{hour}'. Since our spa opens at 9:00 AM, I've assumed <strong>{hour}:00 AM</strong>.</i><br><br>"
        else:
            response = f"💡 <i>I see you said '{hour}'. I've assumed <strong>{hour}:00 PM</strong> (afternoon).</i><br><br>"
    else:
        response = ""
    
    # Parse the booking datetime
    booking_datetime, error = parse_booking_datetime(date_str, time_str)
    
    if error:
        return response + f"❌ {error}"
    
    # Check if booking is in the past
    if booking_datetime < datetime.now():
        return response + f"❌ I'm sorry, but {booking_datetime.strftime('%A, %B %d at %I:%M %p')} is in the past. Please select a future date and time for your spa appointment."
    
    # Check if booking is within operating hours (9 AM - 10 PM)
    if booking_datetime.hour < 9:
        return response + f"❌ I'm sorry, but our spa opens at 9:00 AM. {booking_datetime.strftime('%I:%M %p')} is too early. <br><br>💡 <i>Would you like me to book you for 9:00 AM instead?</i>"
    elif booking_datetime.hour >= 22:
        return response + f"❌ I'm sorry, but our spa closes at 10:00 PM. {booking_datetime.strftime('%I:%M %p')} is too late. <br><br>💡 <i>The latest appointment we can take is 9:30 PM.</i>"
    
    # Check if the time slot is available
    is_available, conflict = is_spa_slot_available(booking_datetime, duration)
    
    if not is_available:
        if conflict == "Outside Operating Hours":
            return response + f"❌ I'm sorry, but our spa operates from 9:00 AM to 10:00 PM. Please select a time within these hours. {booking_datetime.strftime('%I:%M %p')} is not available."
        elif isinstance(conflict, list):
            return response + format_conflict_message(conflict)
        else:
            return response + f"❌ I'm sorry, but the time slot {booking_datetime.strftime('%A, %B %d at %I:%M %p')} is not available. Please choose a different time."
    
    # If available, confirm the booking
    success, message = book_spa_slot("Mr. Alexander Vance", service, booking_datetime, duration)
    
    if success:
        st.session_state.latest_spa_booking = f"{booking_datetime.strftime('%b %d at %I:%M %p')} - {service}"
        return response + render_spa_vip_pass(f"{booking_datetime.strftime('%A, %B %d at %I:%M %p')}<br>💆 {service}")
    else:
        return response + message

def get_bot_response(user_input):
    # Check and correct spelling
    corrected_input, was_corrected = spell_check_and_correct(user_input)
    
    if was_corrected and corrected_input != user_input:
        correction_note = f"✨ <small><i>(I understood you meant: \"{corrected_input}\")</i></small><br><br>"
    else:
        correction_note = ""
    
    cleaned_input = clean_text(corrected_input)
    
    if not cleaned_input or not cleaned_input.strip():
        return "Greetings! How may I assist your stay at The Grand Apex today?"

    # --- NEW: Check if this is a weather query FIRST ---
    weather_keywords = [
        "weather", "temperature", "forecast", "rain", "sunny", "cloudy", 
        "hot", "cold", "warm", "humid", "degrees", "°c", "°f",
        "今天天气", "天气预报", "温度", "下雨", "晴天", "气温",
        "weather today", "weather tomorrow", "how is the weather"
    ]
    
    # Check if user is asking about weather
    is_weather_query = any(keyword in cleaned_input.lower() for keyword in weather_keywords)
    
    # If it's a weather query, handle it immediately (don't go to spa booking)
    if is_weather_query:
        weather_res = get_realtime_weather()
        return correction_note + weather_res["formatted_text"]

    # Spa Booking context handling
    if st.session_state.awaiting_spa_booking:
        st.session_state.awaiting_spa_booking = False
        return process_spa_booking(user_input)
        
    try:
        probs = model.predict_proba([cleaned_input])[0]
        max_idx = np.argmax(probs)
        confidence = probs[max_idx]
        predicted_tag = model.classes_[max_idx]
        
        if confidence < 0.15:
            return (
                "I apologize, but I want to ensure you receive the most precise assistance. "
                "Could you please specify if you are asking about <strong>Wi-Fi</strong>, <strong>Breakfast</strong>, <strong>Services</strong>, or <strong>Check-in</strong>?<br><br>"
                "You may also dial <strong>'0'</strong> on your room phone to connect directly with the Front Desk."
            )
        
        if predicted_tag in ["ask_spa", "ask_spa_booking"]:
            # Double-check: Is this actually a weather query but misclassified?
            if is_weather_query:
                weather_res = get_realtime_weather()
                return correction_note + weather_res["formatted_text"]
            
            st.session_state.awaiting_spa_booking = True
            return correction_note + LUXURY_RESPONSES.get(predicted_tag)

        if predicted_tag == "ask_weather":
            weather_res = get_realtime_weather()
            return correction_note + weather_res["formatted_text"]

        if predicted_tag == "internal_call":
            return correction_note + render_internal_call_card()

        return correction_note + LUXURY_RESPONSES.get(predicted_tag, "Thank you. Our Concierge Desk is entirely at your service.")
        
    except Exception:
        return "I am at your service. Please feel free to ask about our room amenities, dining, or guest services."


# ==========================================
# 7. Styling Injection (Bright Luxury Theme)
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
# 8. PAGE 1: Luxury Dashboard & Banner Slider
# ==========================================
if st.session_state.page == "dashboard":
    weather_data = get_realtime_weather()
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(197, 160, 89, 0.3); padding-bottom: 15px; margin-bottom: 20px;">
        <div style="font-family: 'Cormorant Garamond', serif; font-size: 26px; font-weight: 700; color: #8C6B2D; letter-spacing: 3px;">THE GRAND APEX RESORT & SPA</div>
        <div style="font-size: 13px; color: #555555; letter-spacing: 1px; font-weight: 500;">SUITE 1808 &nbsp;|&nbsp; {datetime.now().strftime("%I:%M %p")} &nbsp;|&nbsp; {weather_data['temp']}°C {weather_data['condition'].split()[0]}</div>
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
            <div style="font-size: 12px; color: #8C6B2D; margin-top: 6px; font-weight: 500;">{"✅ Confirmed" if st.session_state.latest_spa_booking else "Ready for Booking"}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        if st.button("💬 Open Private Executive Concierge", use_container_width=True):
            navigate_to("chat")
            st.rerun()


# ==========================================
# 9. PAGE 2: Left/Right Chat Interface
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
        
        # Display current spa bookings (for demo)
        with st.expander("📋 View Spa Bookings (Demo)"):
            if st.session_state.spa_bookings:
                st.write("**Current Bookings:**")
                for slot, booking in sorted(st.session_state.spa_bookings.items()):
                    dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")
                    st.write(f"• {dt.strftime('%b %d, %I:%M %p')} - {booking['guest_name']} ({booking['service']})")
            else:
                st.write("No bookings yet.")

    # --- MAIN CHAT AREA ---
    with main_chat_col:
        # Chat Messages Box
        chat_box = st.container(height=450)
        with chat_box:
            for msg in st.session_state.messages:
                role = msg["role"]
                timestamp = msg.get("time", datetime.now().strftime("%I:%M %p"))

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
        user_prompt = st.chat_input("Type your request here (e.g., Wi-Fi, Spa, Weather, Breakfast)...")
        if user_prompt:
            current_time = datetime.now().strftime("%I:%M %p")
            
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
