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
# EMAIL FUNCTIONALITY (No Login Required)
# ==========================================
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- EMAIL CONFIGURATION ---
# To get App Password: Google Account → Security → 2-Step Verification → App Passwords
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "koeyzs-wm22@student.tarc.edu.my",  # Your Gmail
    "sender_password": "qxis rtkl cokw hndy",   # Your App Password
    "sender_name": "The Grand Apex Resort & Spa",
    "use_smtp": True
}
import streamlit as st
from datetime import datetime

# Page Config must be the first Streamlit command
st.set_page_config(
    page_title="The Grand Apex Resort & Spa | Executive Concierge",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# Session State Initialization (MUST BE BEFORE UI COMPONENTS)
# ==========================================
if "guest_email" not in st.session_state:
    st.session_state.guest_email = ""  # Default empty string

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Greetings! It is my absolute pleasure to welcome you to The Grand Apex Resort & Spa. How may I assist your stay today?",
            "time": datetime.now().strftime("%I:%M %p")
        }
    ]

def get_email_html(booking_details, guest_name):
    """
    Generate HTML email content for booking confirmation
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Booking Confirmation</title>
        <style>
            body {{
                font-family: 'Georgia', 'Times New Roman', serif;
                background-color: #FAF8F5;
                margin: 0;
                padding: 20px;
                color: #1A1A1A;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #C5A059;
                box-shadow: 0 8px 30px rgba(197, 160, 89, 0.15);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #8C6B2D 0%, #C5A059 100%);
                padding: 30px 20px;
                text-align: center;
                color: white;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
                letter-spacing: 2px;
                font-family: 'Georgia', serif;
            }}
            .header p {{
                margin: 8px 0 0 0;
                font-size: 14px;
                opacity: 0.9;
                letter-spacing: 1px;
            }}
            .content {{
                padding: 30px 25px;
            }}
            .booking-box {{
                background: #FAF8F5;
                padding: 20px;
                border-radius: 12px;
                margin: 20px 0;
                border-left: 4px solid #C5A059;
            }}
            .booking-box p {{
                margin: 8px 0;
                font-size: 15px;
            }}
            .booking-box strong {{
                color: #8C6B2D;
            }}
            .icon {{
                font-size: 18px;
            }}
            .divider {{
                border: none;
                border-top: 2px dashed #E8E0D8;
                margin: 25px 0;
            }}
            .footer {{
                background: #FAF8F5;
                padding: 20px 25px;
                text-align: center;
                font-size: 12px;
                color: #7A7570;
                border-top: 1px solid #E8E0D8;
            }}
            .footer a {{
                color: #8C6B2D;
                text-decoration: none;
            }}
            .badge {{
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                margin-left: 8px;
            }}
            .important {{
                background: #FFF8E1;
                padding: 15px 20px;
                border-radius: 8px;
                border-left: 4px solid #FFB300;
                margin: 20px 0;
            }}
            .important ul {{
                margin: 8px 0;
                padding-left: 20px;
            }}
            .important li {{
                margin: 5px 0;
            }}
            @media only screen and (max-width: 480px) {{
                .container {{
                    border-radius: 0;
                }}
                .content {{
                    padding: 20px 15px;
                }}
                .header h1 {{
                    font-size: 22px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏨 The Grand Apex</h1>
                <p>Executive VIP Concierge</p>
            </div>
            
            <div class="content">
                <h2 style="color: #8C6B2D; margin-top: 0;">✅ Booking Confirmed!</h2>
                
                <p>Dear <strong>{guest_name}</strong>,</p>
                
                <p>We are delighted to confirm your spa booking at <strong>The Grand Apex Resort & Spa</strong>. 
                Your appointment has been successfully secured.</p>
                
                <div class="booking-box">
                    <h3 style="margin-top: 0; color: #8C6B2D;">📋 Booking Details</h3>
                    <p><span class="icon">📅</span> <strong>Date:</strong> {booking_details['date']}</p>
                    <p><span class="icon">🕐</span> <strong>Time:</strong> {booking_details['time']}</p>
                    <p><span class="icon">💆</span> <strong>Service:</strong> {booking_details['service']}</p>
                    <p><span class="icon">⏱️</span> <strong>Duration:</strong> {booking_details['duration']} minutes</p>
                    <p><span class="icon">📍</span> <strong>Location:</strong> Apex Executive Spa, 5th Floor</p>
                    <p><span class="icon">👤</span> <strong>Guest:</strong> {guest_name}</p>
                </div>
                
                <div class="important">
                    <p style="font-weight: 600; margin-top: 0; color: #E65100;">⚠️ Important Reminders</p>
                    <ul>
                        <li>Please arrive <strong>15 minutes early</strong> for your appointment</li>
                        <li>Bring your room key for verification</li>
                        <li>Complimentary robes and slippers will be provided</li>
                        <li>Please inform us of any medical conditions or allergies</li>
                    </ul>
                </div>
                
                <hr class="divider">
                
                <div style="background: #E8F5E9; padding: 12px 16px; border-radius: 8px; margin: 15px 0;">
                    <p style="margin: 0; font-size: 14px;">
                        💡 <strong>Need to make changes?</strong> 
                        Dial <strong>Ext '802'</strong> or contact our Concierge Desk at <strong>Ext '0'</strong>
                    </p>
                </div>
                
                <p style="margin-top: 20px; font-style: italic; color: #555;">
                    "We look forward to providing you with an exceptional wellness experience."
                </p>
                
                <p style="margin-top: 25px;">
                    Warm regards,<br>
                    <strong style="color: #8C6B2D; font-size: 16px;">The Grand Apex Concierge Team</strong>
                </p>
            </div>
            
            <div class="footer">
                <p>
                    <strong>The Grand Apex Resort & Spa</strong><br>
                    Suite 1808 | Kuala Lumpur | Malaysia<br>
                    <a href="tel:0">📞 Extension '0'</a> | 
                    <a href="#">🌐 www.grandapex.com</a>
                </p>
                <p style="margin-top: 10px; font-size: 11px;">
                    This is an automated confirmation. Please do not reply to this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

def get_cancellation_email_html(booking_details, guest_name):
    """
    Generate HTML email content for booking cancellation
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Booking Cancellation</title>
        <style>
            body {{
                font-family: 'Georgia', 'Times New Roman', serif;
                background-color: #FAF8F5;
                margin: 0;
                padding: 20px;
                color: #1A1A1A;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #C5A059;
                box-shadow: 0 8px 30px rgba(197, 160, 89, 0.15);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #8C6B2D 0%, #C5A059 100%);
                padding: 30px 20px;
                text-align: center;
                color: white;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
                letter-spacing: 2px;
                font-family: 'Georgia', serif;
            }}
            .header p {{
                margin: 8px 0 0 0;
                font-size: 14px;
                opacity: 0.9;
                letter-spacing: 1px;
            }}
            .content {{
                padding: 30px 25px;
            }}
            .cancellation-box {{
                background: #FFF3E0;
                padding: 20px;
                border-radius: 12px;
                margin: 20px 0;
                border-left: 4px solid #E65100;
            }}
            .cancellation-box p {{
                margin: 8px 0;
                font-size: 15px;
            }}
            .cancellation-box strong {{
                color: #BF360C;
            }}
            .icon {{
                font-size: 18px;
            }}
            .divider {{
                border: none;
                border-top: 2px dashed #E8E0D8;
                margin: 25px 0;
            }}
            .footer {{
                background: #FAF8F5;
                padding: 20px 25px;
                text-align: center;
                font-size: 12px;
                color: #7A7570;
                border-top: 1px solid #E8E0D8;
            }}
            .footer a {{
                color: #8C6B2D;
                text-decoration: none;
            }}
            .badge-cancel {{
                display: inline-block;
                background: #E65100;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                margin-left: 8px;
            }}
            .info-box {{
                background: #E3F2FD;
                padding: 15px 20px;
                border-radius: 8px;
                border-left: 4px solid #1565C0;
                margin: 20px 0;
            }}
            .info-box ul {{
                margin: 8px 0;
                padding-left: 20px;
            }}
            .info-box li {{
                margin: 5px 0;
            }}
            @media only screen and (max-width: 480px) {{
                .container {{
                    border-radius: 0;
                }}
                .content {{
                    padding: 20px 15px;
                }}
                .header h1 {{
                    font-size: 22px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏨 The Grand Apex</h1>
                <p>Executive VIP Concierge</p>
            </div>
            
            <div class="content">
                <h2 style="color: #E65100; margin-top: 0;">❌ Booking Cancelled</h2>
                
                <p>Dear <strong>{guest_name}</strong>,</p>
                
                <p>Your spa booking at <strong>The Grand Apex Resort & Spa</strong> has been successfully cancelled.</p>
                
                <div class="cancellation-box">
                    <h3 style="margin-top: 0; color: #BF360C;">📋 Cancelled Booking Details</h3>
                    <p><span class="icon">📅</span> <strong>Date:</strong> {booking_details['date']}</p>
                    <p><span class="icon">🕐</span> <strong>Time:</strong> {booking_details['time']}</p>
                    <p><span class="icon">💆</span> <strong>Service:</strong> {booking_details['service']}</p>
                    <p><span class="icon">⏱️</span> <strong>Duration:</strong> {booking_details['duration']} minutes</p>
                    <p><span class="icon">📍</span> <strong>Location:</strong> Apex Executive Spa, 5th Floor</p>
                    <p><span class="icon">👤</span> <strong>Guest:</strong> {guest_name}</p>
                    <p style="margin-top: 10px; color: #E65100; font-weight: 600;">Status: <span style="color: #E65100;">❌ CANCELLED</span></p>
                </div>
                
                <div class="info-box">
                    <p style="font-weight: 600; margin-top: 0; color: #1565C0;">💡 What would you like to do next?</p>
                    <ul>
                        <li>Make a new booking at a different time</li>
                        <li>Check your other bookings</li>
                        <li>Contact our Concierge Desk at <strong>Ext '0'</strong> for assistance</li>
                    </ul>
                </div>
                
                <hr class="divider">
                
                <p style="margin-top: 20px; font-style: italic; color: #555;">
                    "We hope to serve you again soon."
                </p>
                
                <p style="margin-top: 25px;">
                    Warm regards,<br>
                    <strong style="color: #8C6B2D; font-size: 16px;">The Grand Apex Concierge Team</strong>
                </p>
            </div>
            
            <div class="footer">
                <p>
                    <strong>The Grand Apex Resort & Spa</strong><br>
                    Suite 1808 | Kuala Lumpur | Malaysia<br>
                    <a href="tel:0">📞 Extension '0'</a> | 
                    <a href="#">🌐 www.grandapex.com</a>
                </p>
                <p style="margin-top: 10px; font-size: 11px;">
                    This is an automated cancellation confirmation. Please do not reply to this email.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    
def get_room_email_html(booking_details, guest_name):
    """HTML content for room stay confirmation."""
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #8C6B2D;">The Grand Apex Resort & Spa</h2>
        <h3>Room Booking Confirmation</h3>
        <p>Dear {guest_name},</p>
        <p>Your room reservation has been successfully updated or confirmed.</p>
        <ul>
          <li><strong>Room:</strong> {booking_details.get('room', 'Penthouse')}</li>
          <li><strong>Check-In Date:</strong> {booking_details['check_in']}</li>
          <li><strong>Check-Out Date:</strong> {booking_details['check_out']}</li>
        </ul>
        <p>We look forward to welcoming you!</p>
      </body>
    </html>
    """


def get_room_cancellation_email_html(booking_details, guest_name):
    """HTML content for room stay cancellation."""
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #8C6B2D;">The Grand Apex Resort & Spa</h2>
        <h3>Room Booking Cancellation</h3>
        <p>Dear {guest_name},</p>
        <p>Your room reservation for <strong>{booking_details.get('room', 'Penthouse')}</strong> starting on <strong>{booking_details['check_in']}</strong> has been cancelled.</p>
        <p>If this was done in error, please contact our front desk immediately.</p>
      </body>
    </html>
    """


def send_room_confirmation_email(booking_details, guest_name="Mr. Alexander Vance", guest_email=None):
    """Send room booking confirmation email using SMTP."""
    if not guest_email:
        guest_email = st.session_state.get("guest_email", "")

    if not guest_email:
        return False, "⚠️ No valid email address provided."

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = guest_email
        msg['Subject'] = f"✅ The Grand Apex - Room Booking Confirmation - {booking_details['check_in']}"
        
        html_content = get_room_email_html(booking_details, guest_name)
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        return True, f"📧 Room confirmation email sent to {guest_email}!"
    except Exception as e:
        return False, f"⚠️ Room email could not be sent: {str(e)}"


def send_room_cancellation_email(booking_details, guest_name="Mr. Alexander Vance", guest_email=None):
    """Send room booking cancellation email using SMTP."""
    if not guest_email:
        guest_email = st.session_state.get("guest_email", "")

    if not guest_email:
        return False, "⚠️ No valid email address provided."

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = guest_email
        msg['Subject'] = f"❌ The Grand Apex - Room Booking Cancelled - {booking_details['check_in']}"
        
        html_content = get_room_cancellation_email_html(booking_details, guest_name)
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        return True, f"📧 Room cancellation email sent to {guest_email}!"
    except Exception as e:
        return False, f"⚠️ Room cancellation email could not be sent: {str(e)}"

def send_booking_confirmation_email(booking_details, guest_name="Mr. Alexander Vance", guest_email=None):
    """
    Send booking confirmation email using SMTP
    """
    # Use session_state email if none is passed explicitly
    if not guest_email:
        guest_email = st.session_state.get("guest_email", "")

    if not guest_email:
        return False, "⚠️ No valid email address provided."

    try:
        # Create email
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = guest_email
        msg['Subject'] = f"✅ The Grand Apex - Spa Booking Confirmation - {booking_details['date']}"
        
        # HTML content
        html_content = get_email_html(booking_details, guest_name)
        
        # Attach HTML
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        return True, f"📧 Booking confirmation email sent to {guest_email}!"
    
    except Exception as e:
        return False, f"⚠️ Email could not be sent: {str(e)}"


def send_cancellation_email(booking_details, guest_name="Mr. Alexander Vance", guest_email=None):
    """
    Send booking cancellation email to customer
    """
    if not guest_email:
        guest_email = st.session_state.get("guest_email", "")

    if not guest_email:
        return False, "⚠️ No valid email address provided."

    try:
        # Create email
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = guest_email
        msg['Subject'] = f"❌ The Grand Apex - Spa Booking Cancelled - {booking_details['date']}"
        
        # HTML content for cancellation
        html_content = get_cancellation_email_html(booking_details, guest_name)
        
        # Attach HTML
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        return True, f"📧 Cancellation confirmation email sent to {guest_email}!"
    
    except Exception as e:
        return False, f"⚠️ Cancellation email could not be sent: {str(e)}"

# 1. Initialize lock flag at top of bot.py (run once)
if "room_email_sent" not in st.session_state:
    st.session_state.room_email_sent = False

# 2. Define callback to unlock email sending when the email input changes
def reset_email_flag():
    st.session_state.room_email_sent = False

# 3. Render Text Input ONLY ONCE with key and on_change callback
st.text_input(
    "📧 Preferred Email for Confirmations:",
    key="guest_email",  # Automatically syncs typed text to st.session_state.guest_email
    placeholder="enter.your.email@domain.com",
    on_change=reset_email_flag  # Resets the lock flag when user updates their email
)

# 4. Fetch details & format room stay data dynamically
current_stay = st.session_state.get("current_stay", {})
default_check_in = datetime(2026, 7, 28)
default_check_out = datetime(2026, 8, 3)

check_in_val = current_stay.get("check_in") or default_check_in
check_out_val = current_stay.get("check_out") or default_check_out

check_in_str = check_in_val.strftime("%Y-%m-%d") if hasattr(check_in_val, "strftime") else str(check_in_val)
check_out_str = check_out_val.strftime("%Y-%m-%d") if hasattr(check_out_val, "strftime") else str(check_out_val)

room_details = {
    "check_in": check_in_str,
    "check_out": check_out_str,
    "room": current_stay.get("room", "Penthouse 1808")
}

guest_name = current_stay.get("guest", "Mr. Alexander Vance")
guest_email = st.session_state.get("guest_email", "").strip()

# 5. Trigger room confirmation email sending via action button
if st.button("📧 Send / Resend Extension Confirmation"):
    if guest_email and not st.session_state.room_email_sent:
        success, message = send_room_confirmation_email(
            booking_details=room_details,
            guest_name=guest_name,
            guest_email=guest_email
        )
        if success:
            st.session_state.room_email_sent = True  # Locks duplicate runs for this email address
            st.success(message)
        else:
            st.error(message)
    elif st.session_state.room_email_sent:
        st.info("ℹ️ Confirmation email has already been sent to this address.")
    elif not guest_email:
        st.warning("⚠️ Please enter a valid email address.")
    
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

if "awaiting_cancel_booking" not in st.session_state:
    st.session_state.awaiting_cancel_booking = False

if "awaiting_extend_booking" not in st.session_state:
    st.session_state.awaiting_extend_booking = False

if "latest_spa_booking" not in st.session_state:
    st.session_state.latest_spa_booking = None

# Guest Email (Defaults to empty string for user input)
if "guest_email" not in st.session_state:
    st.session_state.guest_email = ""

# Room Stay Information
if "current_stay" not in st.session_state:
    st.session_state.current_stay = {
        "check_in": datetime(2026, 7, 28),
        "check_out": datetime(2026, 8, 3),
        "room": "Penthouse 1808",
        "guest": "Mr. Alexander Vance"
    }

# Spa Booking Database (In-memory simulation)
if "spa_bookings" not in st.session_state:
    st.session_state.spa_bookings = {
        "2026-07-28 10:00": {"guest_name": "Mr. Alexander Vance", "service": "Aromatherapy Massage", "duration": 60},
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
    st.session_state.awaiting_cancel_booking = False
    st.session_state.awaiting_extend_booking = False
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
        'yest': 'yesterday',
        'tmr': 'tomorrow',
        'cancle': 'cancel',
        'cancell': 'cancel',
        'extend': 'extend',
        'extand': 'extend',
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
# 3. Enhanced Date/Time Parsing & Validation
# ==========================================
def parse_date_from_string(date_str):
    """
    Parse date from various formats including:
    - 20/8/2026
    - 20-8-2026
    - 31/8/2026
    - 20 August 2026
    - today
    - tomorrow
    - yesterday
    - day after tomorrow
    Returns (datetime_obj, error_message)
    """
    date_str = date_str.strip().lower()
    
    # Handle special keywords
    if date_str in ["today", "todays"]:
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0), None
    elif date_str in ["tomorrow", "tmr", "tomorow"]:
        return (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0), None
    elif date_str in ["yesterday", "yest", "yday"]:
        return (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0), None
    elif date_str in ["day after tomorrow", "day after tmr"]:
        return (datetime.now() + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0), None
    elif "next week" in date_str:
        return (datetime.now() + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0), None
    
    # Try different date formats
    date_formats = [
        ("%Y-%m-%d", False),      # 2026-07-28
        ("%d/%m/%Y", False),      # 28/07/2026 or 31/08/2026
        ("%d-%m-%Y", False),      # 28-07-2026
        ("%d.%m.%Y", False),      # 28.07.2026
        ("%d %B %Y", False),      # 28 July 2026
        ("%B %d %Y", False),      # July 28 2026
        ("%d-%b-%Y", False),      # 28-Jul-2026
        ("%b %d %Y", False),      # Jul 28 2026
        ("%Y%m%d", False),        # 20260728
        ("%d/%m/%y", False),      # 28/07/26
        ("%d-%m-%y", False),      # 28-07-26
        ("%d.%m.%y", False),      # 28.07.26
        ("%d-%b-%y", False),      # 28-Jul-26
    ]
    
    # Remove ordinal indicators (st, nd, rd, th)
    cleaned_date = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
    
    for fmt, _ in date_formats:
        try:
            date_obj = datetime.strptime(cleaned_date, fmt)
            return date_obj, None
        except ValueError:
            continue
    
    # Try with abbreviated month names
    month_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    # Try pattern like "20 Aug 2026"
    match = re.match(r'(\d{1,2})\s+([a-zA-Z]{3,})\s+(\d{4})', date_str)
    if match:
        day = int(match.group(1))
        month_name = match.group(2).lower()[:3]
        year = int(match.group(3))
        if month_name in month_map:
            month = month_map[month_name]
            try:
                date_obj = datetime(year, month, day)
                return date_obj, None
            except ValueError:
                pass
    
    return None, "I couldn't understand the date format. Please use formats like '31/8/2026', '20-8-2026', 'today', 'tomorrow', or 'yesterday'."

def parse_time_from_string(time_str):
    """
    Parse time from various formats including:
    - 2:30 PM
    - 14:30
    - 2 PM
    - 2
    - 2:30pm
    - 1430
    - 9pm
    - 9 PM
    Returns (hour, minute, error_message)
    """
    time_str = time_str.strip().lower()
    
    # Handle special cases
    if time_str in ["now", "right now", "asap"]:
        now = datetime.now()
        return now.hour, now.minute, None
    elif time_str in ["noon", "midday", "12 noon"]:
        return 12, 0, None
    elif time_str in ["midnight", "12 midnight"]:
        return 0, 0, None
    
    # Check if it's a standalone number with AM/PM (like "9pm" or "9 am")
    match = re.match(r'^(\d{1,2})\s*(am|pm)$', time_str)
    if match:
        hour = int(match.group(1))
        ampm = match.group(2)
        if ampm == 'pm' and hour < 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0
        if 0 <= hour <= 23:
            return hour, 0, None
        else:
            return None, None, f"Invalid hour: {hour}. Please use a number between 1 and 12."
    
    # Check if it's a standalone number (like "2")
    if re.match(r'^\d{1,2}$', time_str):
        hour = int(time_str)
        if hour < 0 or hour > 23:
            return None, None, f"Invalid hour: {hour}. Please use a number between 0 and 23."
        if hour < 9:
            return hour, 0, None
        elif hour == 12:
            return 12, 0, None
        else:
            return hour, 0, None
    
    # Try different time formats
    time_formats = [
        ("%I:%M %p", True),   # 2:30 PM
        ("%I:%M%p", True),    # 2:30PM
        ("%I %p", True),      # 2 PM
        ("%I%p", True),       # 2PM
        ("%H:%M", False),     # 14:30
        ("%H%M", False),      # 1430
        ("%H", False),        # 14
    ]
    
    for fmt, has_ampm in time_formats:
        try:
            time_obj = datetime.strptime(time_str, fmt)
            hour = time_obj.hour
            minute = time_obj.minute
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return hour, minute, None
        except ValueError:
            continue
    
    # Try with ":" but no AM/PM
    if ":" in time_str:
        parts = time_str.split(":")
        if len(parts) == 2:
            try:
                hour = int(parts[0])
                minute = int(parts[1])
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    if hour > 12:
                        return hour, minute, None
                    elif hour == 12:
                        return 12, minute, None
                    elif hour < 9:
                        return hour, minute, None
                    else:
                        return hour, minute, None
            except ValueError:
                pass
    
    return None, None, "I couldn't understand the time format. Please use formats like '2:30 PM', '14:30', '9pm', or '2 PM'."

def extract_date_time_from_text(text):
    """
    Extract date and time from natural language text.
    Returns (date_str, time_str, service, error_message)
    """
    text_lower = text.lower()
    
    # Default values
    date_str = None
    time_str = None
    service = "Aromatherapy Massage"
    
    # Extract service type
    services = {
        "aromatherapy": "Aromatherapy Massage",
        "deep tissue": "Deep Tissue Massage",
        "hot stone": "Hot Stone Therapy",
        "facial": "Hydrating Facial",
        "swedish": "Swedish Massage",
        "reflexology": "Reflexology",
        "massage": "Aromatherapy Massage"
    }
    
    for key, value in services.items():
        if key in text_lower:
            service = value
            break
    
    # Extract date - SUPPORT 31/8/2026 format
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # 20/8/2026 or 20-8-2026 or 31/8/2026
        r'(\d{1,2}\s+[a-zA-Z]{3,}\s+\d{4})',  # 20 Aug 2026
        r'(\d{1,2}\s+[a-zA-Z]+\s+\d{4})',     # 20 August 2026
        r'\b(today|todays|tomorrow|tmr|tomorow|yesterday|yest|yday|day after tomorrow|next week)\b',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            date_str = match.group(1) if match.groups() else match.group(0)
            break
    
    # If no date found, check for keywords
    if not date_str:
        if "today" in text_lower or "todays" in text_lower:
            date_str = "today"
        elif "tomorrow" in text_lower or "tmr" in text_lower or "tomorow" in text_lower:
            date_str = "tomorrow"
        elif "yesterday" in text_lower or "yest" in text_lower or "yday" in text_lower:
            date_str = "yesterday"
        elif "day after tomorrow" in text_lower:
            date_str = "day after tomorrow"
        elif "next week" in text_lower:
            date_str = "next week"
    
    # Extract time - SUPPORT 9pm format
    time_patterns = [
        r'(\d{1,2}:\d{2}\s*(?:am|pm)?)',  # 2:30 PM or 14:30
        r'(\d{1,2}\s*(?:am|pm)\s*(?:o\'clock)?)',  # 2 PM or 2pm or 9pm
        r'(\d{1,2}\s*o\'clock)',  # 2 o'clock
        r'\b(noon|midday|midnight)\b',
        r'(\d{1,2})\s*(?:in the)?\s*(morning|afternoon|evening|night)',
        r'(\d{1,2})(am|pm)',  # 9pm or 10am
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            time_str = match.group(1) if match.groups() else match.group(0)
            # If we captured "9pm" with the pattern, make sure it's preserved
            if match.groups() and len(match.groups()) > 1:
                time_str = match.group(1) + match.group(2)
            break
    
    # If no time found, look for a standalone number (like "2")
    if not time_str:
        numbers = re.findall(r'\b(\d{1,2})\b', text_lower)
        for num in numbers:
            hour = int(num)
            if 1 <= hour <= 12:
                if "am" in text_lower:
                    time_str = f"{hour} AM"
                elif "pm" in text_lower:
                    time_str = f"{hour} PM"
                elif "morning" in text_lower:
                    time_str = f"{hour} AM"
                elif "afternoon" in text_lower or "evening" in text_lower or "night" in text_lower:
                    time_str = f"{hour} PM"
                elif hour < 9:
                    time_str = f"{hour} AM"
                else:
                    time_str = f"{hour} PM"
                break
    
    return date_str, time_str, service, None

def validate_booking_datetime(booking_datetime, duration_minutes=60):
    """
    Validate booking datetime with comprehensive checks.
    Returns (is_valid, error_message)
    """
    now = datetime.now()
    today_date = now.date()
    booking_date = booking_datetime.date()
    
    # Check if date is in the past
    if booking_date < today_date:
        return False, f"❌ I'm sorry, but {booking_datetime.strftime('%A, %B %d, %Y')} is in the past. Please select a future date for your spa appointment."
    
    # Check if date is today but time is in the past
    if booking_date == today_date and booking_datetime < now:
        return False, f"❌ I'm sorry, but {booking_datetime.strftime('%I:%M %p')} has already passed today. Please select a later time."
    
    # Check if booking is within operating hours (9 AM - 10 PM)
    if booking_datetime.hour < 9:
        return False, f"❌ I'm sorry, but our spa opens at 9:00 AM. {booking_datetime.strftime('%I:%M %p')} is too early. <br><br>💡 <i>Would you like me to book you for 9:00 AM instead?</i>"
    elif booking_datetime.hour >= 22:
        return False, f"❌ I'm sorry, but our spa closes at 10:00 PM. {booking_datetime.strftime('%I:%M %p')} is too late. <br><br>💡 <i>The latest appointment we can take is 9:30 PM.</i>"
    elif booking_datetime.hour == 22 and booking_datetime.minute > 0:
        return False, f"❌ I'm sorry, but our spa closes at 10:00 PM. {booking_datetime.strftime('%I:%M %p')} is too late. <br><br>💡 <i>The latest appointment we can take is 9:30 PM.</i>"
    
    return True, None


# ==========================================
# 4. Spa Booking & Cancellation System
# ==========================================
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
    Book a spa slot with email confirmation
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
    
    # --- SEND EMAIL CONFIRMATION ---
    booking_details = {
        'date': booking_datetime.strftime('%A, %B %d, %Y'),
        'time': booking_datetime.strftime('%I:%M %p'),
        'service': service,
        'duration': duration_minutes
    }
    
    # Send email
    try:
        email_sent, email_message = send_booking_confirmation_email(
            booking_details, 
            guest_name, 
            st.session_state.guest_email
        )
        email_status = email_message
    except Exception as e:
        email_status = "ℹ️ Email notification: Please provide your email address for future confirmations."
    
    confirmation_message = f"""
✅ <strong>Booking Confirmed!</strong><br><br>
📅 <strong>Date:</strong> {booking_datetime.strftime('%A, %B %d, %Y')}<br>
🕐 <strong>Time:</strong> {booking_datetime.strftime('%I:%M %p')}<br>
💆 <strong>Service:</strong> {service}<br>
👤 <strong>Guest:</strong> {guest_name}<br><br>
Please arrive 15 minutes early for your appointment.<br><br>
{email_status}
"""
    
    return True, confirmation_message


# ==========================================
# 4.5. Cancel Booking Function
# ==========================================
def view_my_bookings(guest_name="Mr. Alexander Vance"):
    """
    View all bookings for a specific guest
    Returns formatted string with all bookings
    """
    my_bookings = {}
    for slot, booking in st.session_state.spa_bookings.items():
        if booking["guest_name"] == guest_name:
            my_bookings[slot] = booking
    
    if not my_bookings:
        return "📋 <strong>No Bookings Found</strong><br><br>You don't have any active spa bookings at the moment. Would you like to make a new booking?"
    
    message = "📋 <strong>Your Active Spa Bookings</strong><br><br>"
    for slot, booking in sorted(my_bookings.items()):
        dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")
        message += f"• <strong>{dt.strftime('%A, %B %d at %I:%M %p')}</strong> - {booking['service']}<br>"
    
    message += "<br>💡 <i>To cancel a booking, tell me the time (e.g., 'Cancel my 10 AM booking' or 'Cancel my booking at 2:30 PM')</i>"
    return message

def cancel_spa_booking(time_str, guest_name="Mr. Alexander Vance"):
    """
    Cancel a spa booking by time with email confirmation
    """
    # Parse the time
    hour, minute, error = parse_time_from_string(time_str)
    if error:
        return False, f"❌ {error}"
    
    # Find the booking
    booking_to_cancel = None
    booking_key = None
    
    for slot, booking in st.session_state.spa_bookings.items():
        if booking["guest_name"] != guest_name:
            continue
        
        dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")
        if dt.hour == hour and dt.minute == minute:
            booking_to_cancel = booking
            booking_key = slot
            break
    
    # If booking not found, try to find by time string match
    if not booking_key:
        # Try to match by time string in the booking
        time_str_lower = time_str.lower()
        for slot, booking in st.session_state.spa_bookings.items():
            if booking["guest_name"] != guest_name:
                continue
            
            dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")
            time_str_formatted = dt.strftime("%I:%M %p").lower()
            time_str_formatted_24 = dt.strftime("%H:%M")
            
            if time_str_lower in time_str_formatted or time_str_lower in time_str_formatted_24:
                booking_to_cancel = booking
                booking_key = slot
                break
    
    if not booking_key:
        return False, f"❌ I couldn't find a booking at '{time_str}'. Please check your bookings by saying 'view my bookings'."
    
    # Store booking details for email
    dt = datetime.strptime(booking_key, "%Y-%m-%d %H:%M")
    booking_details = {
        'date': dt.strftime('%A, %B %d, %Y'),
        'time': dt.strftime('%I:%M %p'),
        'service': booking_to_cancel['service'],
        'duration': booking_to_cancel['duration']
    }
    
    # Cancel the booking
    del st.session_state.spa_bookings[booking_key]
    
    # --- SEND CANCELLATION EMAIL ---
    try:
        email_sent, email_message = send_cancellation_email(
            booking_details, 
            guest_name, 
            st.session_state.guest_email
        )
        email_status = email_message
    except Exception as e:
        email_status = "ℹ️ Cancellation email could not be sent. Please contact the front desk for confirmation."
    
    return True, f"""
✅ <strong>Booking Cancelled Successfully!</strong><br><br>
📅 <strong>Date:</strong> {dt.strftime('%A, %B %d, %Y')}<br>
🕐 <strong>Time:</strong> {dt.strftime('%I:%M %p')}<br>
💆 <strong>Service:</strong> {booking_to_cancel['service']}<br><br>
Your booking has been cancelled.<br><br>
{email_status}
"""


# ==========================================
# 4.6. Extend Booking Function
# ==========================================
def extend_room_stay(extra_days, guest_name="Mr. Alexander Vance"):
    """
    Extend room stay by a number of days
    Returns (success, message)
    """
    current_check_out = st.session_state.current_stay["check_out"]
    new_check_out = current_check_out + timedelta(days=extra_days)
    st.session_state.current_stay["check_out"] = new_check_out
    
    return True, f"""
🏨 <strong>🏠 Room Stay Extended Successfully!</strong><br><br>
<div style="background: #E3F2FD; padding: 15px; border-radius: 10px; border-left: 4px solid #1565C0;">
    🛏️ <strong>Guest:</strong> {guest_name}<br>
    🏠 <strong>Room:</strong> {st.session_state.current_stay['room']}<br>
    📅 <strong>Original Check-out:</strong> {current_check_out.strftime('%A, %B %d, %Y')}<br>
    📅 <strong>New Check-out Date:</strong> <strong style="color: #1565C0;">{new_check_out.strftime('%A, %B %d, %Y')}</strong><br>
    📆 <strong>Extended by:</strong> {extra_days} day{'s' if extra_days > 1 else ''}<br>
    💵 <strong>Total Nights:</strong> {(new_check_out - st.session_state.current_stay['check_in']).days} nights<br>
</div>
<br>💡 <i>Your room extension has been confirmed. Housekeeping has been notified of your new check-out date.</i>
"""

def extend_spa_booking(time_str, new_date_str, guest_name="Mr. Alexander Vance"):
    """
    Extend a spa booking to a new date
    Returns (success, message)
    """
    # Parse the current booking time
    hour, minute, error = parse_time_from_string(time_str)
    if error:
        return False, f"❌ {error}"
    
    # Find the booking
    booking_to_extend = None
    booking_key = None
    
    for slot, booking in st.session_state.spa_bookings.items():
        if booking["guest_name"] != guest_name:
            continue
        
        dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")
        if dt.hour == hour and dt.minute == minute:
            booking_to_extend = booking
            booking_key = slot
            break
    
    if not booking_key:
        return False, f"❌ I couldn't find a booking at '{time_str}'. Please check your bookings by saying 'view my bookings'."
    
    # Parse the new date
    date_obj, date_error = parse_date_from_string(new_date_str)
    if date_error:
        return False, f"❌ {date_error}"
    
    # Create new datetime
    new_datetime = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # Validate new date is in the future
    if new_datetime < datetime.now():
        return False, "❌ The new date must be in the future. Please select a future date."
    
    # Check if the new slot is available
    is_available, conflict = is_spa_slot_available(new_datetime, booking_to_extend["duration"], exclude_booking=booking_key)
    
    if not is_available:
        if isinstance(conflict, list):
            return False, format_conflict_message(conflict)
        else:
            return False, "❌ The new time slot is not available. Please choose a different date or time."
    
    # Cancel the old booking and create a new one
    del st.session_state.spa_bookings[booking_key]
    
    new_slot_key = new_datetime.strftime("%Y-%m-%d %H:%M")
    st.session_state.spa_bookings[new_slot_key] = booking_to_extend
    
    old_dt = datetime.strptime(booking_key, "%Y-%m-%d %H:%M")
    
    return True, f"""
🧖‍♀️ <strong>💆 Spa Booking Extended Successfully!</strong><br><br>
<div style="background: #F3E5F5; padding: 15px; border-radius: 10px; border-left: 4px solid #7B1FA2;">
    📅 <strong>Old Date:</strong> {old_dt.strftime('%A, %B %d, %Y')}<br>
    🕐 <strong>Old Time:</strong> {old_dt.strftime('%I:%M %p')}<br>
    📅 <strong>New Date:</strong> <strong style="color: #7B1FA2;">{new_datetime.strftime('%A, %B %d, %Y')}</strong><br>
    🕐 <strong>New Time:</strong> {new_datetime.strftime('%I:%M %p')}<br>
    💆 <strong>Service:</strong> {booking_to_extend['service']}<br>
    ⏱️ <strong>Duration:</strong> {booking_to_extend['duration']} minutes<br>
</div>
<br>💡 <i>Your spa booking has been successfully moved to the new date. Please arrive 15 minutes early for your appointment!</i>
"""

def process_extend_booking(user_input):
    """
    Process booking extension request
    """
    # --- Check if it's a room extension ---
    room_keywords = [
        "room", "stay", "check-out", "checkout", "住宿", "房间", "退房", 
        "hotel", "suite", "penthouse", "room booking", "stay booking"
    ]
    is_room_extend = any(keyword in user_input.lower() for keyword in room_keywords)
    
    # --- Check if it's a spa extension ---
    spa_keywords = ["spa", "massage", "facial", "appointment", "预约", "spa"]
    is_spa_extend = any(keyword in user_input.lower() for keyword in spa_keywords)
    
    # --- Check for days in the input ---
    days_match = re.search(r'(\d+)\s*(day|days|night|nights)', user_input.lower())
    if days_match:
        extra_days = int(days_match.group(1))
    else:
        # If user explicitly said "extend room booking" without days
        if is_room_extend:
            return "📅 How many additional days would you like to extend your room stay? (e.g., '2 days' or '3 nights')"
        elif is_spa_extend:
            # For spa, we need time and new date
            time_patterns = [
                r'(\d{1,2}):(\d{2})\s*(?:am|pm)?',
                r'(\d{1,2})\s*(?:am|pm)',
                r'at\s+(\d{1,2})\s*(?:am|pm)?',
            ]
            
            time_str = None
            for pattern in time_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 2:
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        if "pm" in user_input.lower() and hour < 12:
                            hour += 12
                        elif "am" in user_input.lower() and hour == 12:
                            hour = 0
                        time_str = f"{hour:02d}:{minute:02d}"
                    else:
                        hour = int(match.group(1))
                        if "pm" in user_input.lower() and hour < 12:
                            hour += 12
                        elif "am" in user_input.lower() and hour == 12:
                            hour = 0
                        time_str = f"{hour:02d}:00"
                    break
            
            if not time_str:
                return "🕐 Please tell me the time of the spa booking you'd like to extend (e.g., '2 PM' or '10:30 AM')"
            
            # Also need the new date
            date_str, _, _, _ = extract_date_time_from_text(user_input)
            if not date_str:
                return "📅 Please tell me the new date for your spa booking (e.g., 'tomorrow' or '20/8/2026')"
            
            success, message = extend_spa_booking(time_str, date_str)
            return message
        else:
            # Generic extend without specifying room or spa
            return """📋 I can help you extend either your <strong>room stay</strong> or your <strong>spa booking</strong>.

Please specify what you'd like to extend:
• <strong>Room:</strong> "Extend my room by 2 days"
• <strong>Spa:</strong> "Extend my 2 PM spa to tomorrow"

💡 <i>For room extensions, I'll update your check-out date. For spa extensions, I'll move your booking to a new date.</i>"""
    
    # Validate days
    if extra_days < 1:
        return "❌ Please specify a valid number of days to extend (at least 1 day)."
    if extra_days > 30:
        return "❌ I'm sorry, but we can only extend bookings by up to 30 days at a time. Please contact the front desk for longer extensions."
    
    # --- If it's a room extension with days, do it immediately ---
    if is_room_extend:
        success, message = extend_room_stay(extra_days)
        return message
    
    # --- If it's a spa extension with days, process it ---
    elif is_spa_extend:
        # Need the time and new date
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(?:am|pm)?',
            r'(\d{1,2})\s*(?:am|pm)',
            r'at\s+(\d{1,2})\s*(?:am|pm)?',
        ]
        
        time_str = None
        for pattern in time_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    if "pm" in user_input.lower() and hour < 12:
                        hour += 12
                    elif "am" in user_input.lower() and hour == 12:
                        hour = 0
                    time_str = f"{hour:02d}:{minute:02d}"
                else:
                    hour = int(match.group(1))
                    if "pm" in user_input.lower() and hour < 12:
                        hour += 12
                    elif "am" in user_input.lower() and hour == 12:
                        hour = 0
                    time_str = f"{hour:02d}:00"
                break
        
        if not time_str:
            return "🕐 Please tell me the time of the spa booking you'd like to extend (e.g., '2 PM' or '10:30 AM')"
        
        # Get new date
        date_str, _, _, _ = extract_date_time_from_text(user_input)
        if not date_str:
            return "📅 Please tell me the new date for your spa booking (e.g., 'tomorrow' or '20/8/2026')"
        
        success, message = extend_spa_booking(time_str, date_str)
        return message
    else:
        return """📋 I can help you extend either your <strong>room stay</strong> or your <strong>spa booking</strong>.

Please specify what you'd like to extend:
• <strong>Room:</strong> "Extend my room by 2 days"
• <strong>Spa:</strong> "Extend my 2 PM spa to tomorrow"

💡 <i>For room extensions, I'll update your check-out date. For spa extensions, I'll move your booking to a new date.</i>"""


# ==========================================
# 5. Real-Time Weather API Integration with Attractions
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

            attraction_suggestions = get_attraction_suggestions_with_links(weather_type, curr_temp)

            weather_response = (
                f"🌤️ <strong>Grand Apex Advisory Weather Service</strong><br><br>"
                f"It is currently <strong>{curr_temp}°C</strong> with <strong>{weather_condition}</strong> over the resort grounds.<br><br>"
                f"<strong>3-Day Horizon:</strong><br>"
                f"• <strong>Today ({dates[0]})</strong>: {min_temps[0]}°C to {max_temps[0]}°C<br>"
                f"• <strong>Tomorrow ({dates[1]})</strong>: {min_temps[1]}°C to {max_temps[1]}°C<br>"
                f"• <strong>Day After ({dates[2]})</strong>: {min_temps[2]}°C to {max_temps[2]}°C"
            )

            attraction_response = f"""
<strong>🏙️ Based on today's weather, here are my recommendations:</strong><br><br>
{attraction_suggestions}<br>
🌂 <i>Should you wish to step out for sightseeing, luxury umbrellas and chauffeur-driven limousines are available at the Concierge Desk.</i>
"""

            return {
                "success": True,
                "temp": curr_temp,
                "condition": weather_condition,
                "weather_type": weather_type,
                "weather_response": weather_response,
                "attraction_response": attraction_response
            }
        else:
            return {
                "success": False,
                "temp": 28,
                "condition": "☀️ Sunny & Warm",
                "weather_type": "sunny",
                "weather_response": "☀️ The weather around Grand Apex is delightfully warm (28°C). Perfect day to explore the city!",
                "attraction_response": get_attraction_suggestions_with_links("sunny", 28)
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "temp": 32,
            "condition": "☀️ Sunny & Warm",
            "weather_type": "sunny",
            "weather_response": (
                "☀️ <strong>Kuala Lumpur Weather Update</strong><br><br>"
                "Kuala Lumpur is experiencing its typical warm tropical weather today.<br><br>"
                "🌡️ <strong>Current Weather:</strong><br>"
                "• Temperature: ~32°C (89°F)<br>"
                "• Conditions: Warm and humid"
            ),
            "attraction_response": get_attraction_suggestions_with_links("sunny", 32)
        }
    except Exception:
        return {
            "success": False,
            "temp": 28,
            "condition": "☀️ Sunny & Clear",
            "weather_type": "sunny",
            "weather_response": "☀️ Weather forecast updated: Mild and suitable for local exploration.",
            "attraction_response": get_attraction_suggestions_with_links("sunny", 28)
        }

def get_attraction_suggestions_with_links(weather_type, temperature):
    """Returns attraction suggestions with website links based on weather conditions in Kuala Lumpur."""
    
    attractions = {
        "sunny": f"""
🏗️ <strong>Petronas Twin Towers</strong> — Iconic landmark with breathtaking views from the Skybridge<br>
🔗 <a href="https://www.petronastwintowers.com.my/" target="_blank">Visit Website</a> | Open 10:00 AM - 6:00 PM<br><br>

🌳 <strong>KLCC Park</strong> — Beautiful urban park with a 1.3km jogging trail and Lake Symphony<br>
🔗 <a href="https://www.klccpark.com.my/" target="_blank">Visit Website</a> | Light show at 8:00 PM<br><br>

🛍️ <strong>Pavilion KL</strong> — Premier shopping mall with luxury brands and fine dining<br>
🔗 <a href="https://www.pavilion-kl.com/" target="_blank">Visit Website</a> | Open 10:00 AM - 10:00 PM<br><br>

🏛️ <strong>Islamic Arts Museum Malaysia</strong> — World-class collection of Islamic decorative arts<br>
🔗 <a href="https://www.iamm.org.my/" target="_blank">Visit Website</a> | Open 9:00 AM - 6:00 PM<br><br>

🕌 <strong>National Mosque of Malaysia</strong> — Stunning modern Islamic architecture<br>
🔗 <a href="https://www.masjidnegara.gov.my/" target="_blank">Visit Website</a> | Visitors welcome 9:00 AM - 5:00 PM<br><br>

💡 <strong>Pro Tip:</strong> Morning visits are recommended to avoid the midday heat!
""",
        "cloudy": f"""
🏛️ <strong>National Museum of Malaysia</strong> — Discover Malaysian history and culture<br>
🔗 <a href="https://www.muziumnegara.gov.my/" target="_blank">Visit Website</a> | Open 9:00 AM - 5:00 PM<br><br>

🐟 <strong>Aquaria KLCC</strong> — Stunning underwater world at the Petronas Twin Towers<br>
🔗 <a href="https://www.aquariaklcc.com/" target="_blank">Visit Website</a> | Open 10:00 AM - 7:00 PM<br><br>

🕌 <strong>Sultan Abdul Samad Building</strong> — Beautiful Moorish-style architecture in Merdeka Square<br>
🔗 <a href="https://www.dbkl.gov.my/" target="_blank">Visit Website</a> | Open for public viewing<br><br>

🎨 <strong>Bank Negara Malaysia Museum</strong> — Interactive museum featuring currency and art galleries<br>
🔗 <a href="https://www.bnm.gov.my/museum" target="_blank">Visit Website</a> | Open 10:00 AM - 6:00 PM<br><br>

🎭 <strong>Istana Budaya</strong> — The National Theatre offering cultural performances<br>
🔗 <a href="https://www.istanabudaya.gov.my/" target="_blank">Visit Website</a> | Check showtimes online<br><br>

💡 <strong>Pro Tip:</strong> Perfect weather for both indoor and outdoor activities!
""",
        "rainy": f"""
🛍️ <strong>Pavilion KL & Suria KLCC</strong> — World-class shopping with covered walkways connecting malls<br>
🔗 <a href="https://www.pavilion-kl.com/" target="_blank">Visit Website</a> | Open 10:00 AM - 10:00 PM<br><br>

🐟 <strong>Aquaria KLCC</strong> — Spectacular underwater tunnel and marine life exhibits<br>
🔗 <a href="https://www.aquariaklcc.com/" target="_blank">Visit Website</a> | Open 10:00 AM - 7:00 PM<br><br>

🎨 <strong>KLCC Art Gallery</strong> — Contemporary Malaysian art exhibitions<br>
🔗 <a href="https://www.klccgallery.com/" target="_blank">Visit Website</a> | Open 10:00 AM - 8:00 PM<br><br>

🖼️ <strong>National Art Gallery</strong> — Explore Malaysian artistic heritage<br>
🔗 <a href="https://www.artgallery.gov.my/" target="_blank">Visit Website</a> | Open 9:00 AM - 5:00 PM<br><br>

🎭 <strong>Theatre & Cinema</strong> — Catch a movie or stage performance at Pavilion KL<br>
🔗 <a href="https://www.gsc.com.my/" target="_blank">Visit Website</a> | Check showtimes online<br><br>

🍽️ <strong>Food Court Exploration</strong> — Enjoy Malaysian street food in air-conditioned comfort at Lot 10 Hutong<br>
🔗 <a href="https://www.lot10hutong.com/" target="_blank">Visit Website</a> | Open 10:00 AM - 10:00 PM<br><br>

💡 <strong>Pro Tip:</strong> All attractions are connected via covered walkways or underground tunnels!
""",
        "foggy": f"""
🛍️ <strong>KL Gateway Mall</strong> — Shopping with a view of the KL skyline<br>
🔗 <a href="https://www.klgateway.com/" target="_blank">Visit Website</a> | Open 10:00 AM - 10:00 PM<br><br>

🐟 <strong>Aquaria KLCC</strong> — Perfect indoor attraction for all ages<br>
🔗 <a href="https://www.aquariaklcc.com/" target="_blank">Visit Website</a> | Open 10:00 AM - 7:00 PM<br><br>

📚 <strong>Rumah Penghulu</strong> — Traditional Malay house museum at KLCC<br>
🔗 <a href="https://www.klcc.com.my/" target="_blank">Visit Website</a> | Open 10:00 AM - 6:00 PM<br><br>

🎨 <strong>Canvas Gallery</strong> — Contemporary art exhibitions<br>
🔗 <a href="https://www.canvasgallerykl.com/" target="_blank">Visit Website</a> | Open 11:00 AM - 7:00 PM<br><br>

💡 <strong>Pro Tip:</strong> Great day for spa treatments at our Apex Executive Wellness & Spa!
""",
        "pleasant": f"""
🏙️ <strong>Petronas Twin Towers & Skybridge</strong> — Iconic views of the city<br>
🔗 <a href="https://www.petronastwintowers.com.my/" target="_blank">Visit Website</a> | Open 10:00 AM - 6:00 PM<br><br>

🌸 <strong>Perdana Botanical Garden</strong> — Beautiful tropical gardens with orchid garden<br>
🔗 <a href="https://www.klbotanicalgarden.gov.my/" target="_blank">Visit Website</a> | Open 7:00 AM - 8:00 PM<br><br>

🛍️ <strong>Central Market</strong> — Arts and crafts paradise<br>
🔗 <a href="https://www.centralmarket.com.my/" target="_blank">Visit Website</a> | Open 10:00 AM - 10:00 PM<br><br>

🏛️ <strong>Kuala Lumpur City Gallery</strong> — KL's history and culture<br>
🔗 <a href="https://www.klcitygallery.com/" target="_blank">Visit Website</a> | Open 9:00 AM - 6:00 PM<br><br>

🌳 <strong>FRIM Forest Reserve</strong> — Canopy walkway and nature trails<br>
🔗 <a href="https://www.frim.gov.my/" target="_blank">Visit Website</a> | Open 8:00 AM - 6:00 PM<br><br>

💡 <strong>Pro Tip:</strong> Consider visiting both outdoor and indoor attractions!
"""
    }
    
    return attractions.get(weather_type, attractions["pleasant"])


# ==========================================
# 6. Internal Call & VIP Pass Card Generators
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
# 7. ML Classifier & Response Pipeline
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
📞 <strong>Reservation:</strong> Dial <strong>Ext '802'</strong> from your room phone, or tell me your preferred date and time to book!
""",
    "ask_spa_booking": """
📅 <strong>Spa Reservation Request</strong><br><br>
I would be delighted to arrange this for you, Mr. Vance! To secure your preferred time, please specify:<br>
1. <strong>Your preferred date & time</strong> (e.g., Today at 15:00 PM or 31/8/2026 at 9pm)<br>
2. <strong>Service type</strong> (e.g., Aromatherapy Massage, Deep Tissue, Hot Stone, Facial)<br><br>
<i>💡 I'll check availability and confirm your booking!</i><br><br>
Alternatively, you may dial <strong>Ext '802'</strong> to speak directly with our Spa Receptionist for immediate confirmation.
""",
    "ask_dining": "🍽️ <strong>Gastronomic Experiences</strong><br><br>The Grand Apex features three award-winning venues:<br>1. <strong>L'Aura (Floor 48)</strong> - Michelin French Fine Dining<br>2. <strong>Sakura Sky Lounge (Floor 49)</strong> - Contemporary Omakase<br>3. <strong>The Atrium (Floor 1)</strong> - All-Day International Buffet",
    "ask_attractions": """
🏙️ <strong>Top Attractions in Kuala Lumpur</strong><br><br>
✨ <strong>Must-Visit Places:</strong><br><br>
🏗️ <strong>Petronas Twin Towers</strong> — Iconic landmark with Skybridge and observation deck<br>
🔗 <a href="https://www.petronastwintowers.com.my/" target="_blank">Visit Website</a><br><br>
🌳 <strong>KLCC Park</strong> — Beautiful urban park with jogging trail and Lake Symphony<br>
🔗 <a href="https://www.klccpark.com.my/" target="_blank">Visit Website</a><br><br>
🛍️ <strong>Pavilion KL & Suria KLCC</strong> — Premier shopping destinations<br>
🔗 <a href="https://www.pavilion-kl.com/" target="_blank">Visit Website</a><br><br>
🏛️ <strong>Islamic Arts Museum</strong> — World-class Islamic art collection<br>
🔗 <a href="https://www.iamm.org.my/" target="_blank">Visit Website</a><br><br>
🕌 <strong>National Mosque</strong> — Stunning modern Islamic architecture<br>
🔗 <a href="https://www.masjidnegara.gov.my/" target="_blank">Visit Website</a><br><br>
🐟 <strong>Aquaria KLCC</strong> — Spectacular underwater world experience<br>
🔗 <a href="https://www.aquariaklcc.com/" target="_blank">Visit Website</a><br><br>
🌸 <strong>Perdana Botanical Garden</strong> — Tropical gardens and orchid display<br>
🔗 <a href="https://www.klbotanicalgarden.gov.my/" target="_blank">Visit Website</a><br><br>
🖼️ <strong>National Art Gallery</strong> — Malaysian artistic heritage<br>
🔗 <a href="https://www.artgallery.gov.my/" target="_blank">Visit Website</a><br><br>
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
        "spa价格", "spa多少钱", "按摩多少钱", "spa营业时间", "spa booking"
    ]
    for p in spa_patterns:
        X.append(clean_text(p))
        y.append("ask_spa")

    booking_patterns = [
        "how to book spa", "I want to book spa", "book a massage", "make spa appointment", "reserve spa", "book spa",
        "怎么预约spa", "帮我订spa", "我想做spa", "预约spa", "book spa treatment", "spa booking", "booking spa"
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

    # Cancel booking patterns
    cancel_patterns = [
        "cancel booking", "cancel my booking", "cancel spa", "cancel appointment",
        "我要取消预约", "取消spa", "取消预订"
    ]
    for p in cancel_patterns:
        X.append(clean_text(p))
        y.append("cancel_booking")

    # View bookings patterns
    view_patterns = [
        "view my bookings", "show my bookings", "my bookings", "view appointments",
        "查看我的预约", "我的预约", "预约记录"
    ]
    for p in view_patterns:
        X.append(clean_text(p))
        y.append("view_bookings")

    # Extend booking patterns
    extend_patterns = [
        "extend booking", "extend stay", "extend my stay", "extend room",
        "extend appointment", "延长住宿", "延长预约", "延期"
    ]
    for p in extend_patterns:
        X.append(clean_text(p))
        y.append("extend_booking")

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
    Process spa booking request with enhanced date/time validation
    """
    # Extract date, time, and service from user input
    date_str, time_str, service, error = extract_date_time_from_text(user_input)
    
    # If there's an error in extraction
    if error:
        return f"❌ {error}"
    
    # Check if date was provided
    if not date_str:
        return "📅 I need a date for your spa booking. Please tell me the date (e.g., '31/8/2026', 'today', or 'tomorrow') and I'll check availability!"
    
    # Check if time was provided
    if not time_str:
        return "🕐 I need a time for your spa booking. Please tell me the time (e.g., '2:30 PM', '14:30', '9pm', or '2 PM') and I'll check availability!"
    
    # Parse the date
    date_obj, date_error = parse_date_from_string(date_str)
    if date_error:
        return f"❌ {date_error}"
    
    # Parse the time
    hour, minute, time_error = parse_time_from_string(time_str)
    if time_error:
        return f"❌ {time_error}"
    
    # Combine date and time
    booking_datetime = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # --- DATE VALIDATION ---
    now = datetime.now()
    today_date = now.date()
    booking_date = booking_datetime.date()
    
    # Show a friendly message if date is in the past
    if booking_date < today_date:
        return f"""❌ <strong>Invalid Date</strong><br><br>
I'm sorry, but <strong>{booking_datetime.strftime('%A, %B %d, %Y')}</strong> is in the past.<br><br>
📅 <strong>Today is:</strong> {now.strftime('%A, %B %d, %Y')}<br><br>
💡 <i>Please select a future date for your spa appointment. You can simply type the corrected date and time, like:</i><br>
• "tomorrow at 2 PM"<br>
• "31/8/2026 at 9pm"<br>
• "next week Friday at 3 PM"
"""
    
    # Check if date is today but time is in the past
    if booking_date == today_date and booking_datetime < now:
        return f"""❌ <strong>Time Has Passed</strong><br><br>
I'm sorry, but <strong>{booking_datetime.strftime('%I:%M %p')}</strong> has already passed today.<br><br>
⏰ <strong>Current time:</strong> {now.strftime('%I:%M %p')}<br><br>
💡 <i>Please select a later time today or a future date. Just type the corrected time, like:</i><br>
• "3 PM"<br>
• "tomorrow at 10 AM"
"""
    
    # Check if booking is within operating hours (9 AM - 10 PM)
    if booking_datetime.hour < 9:
        return f"""❌ <strong>Too Early</strong><br><br>
I'm sorry, but our spa opens at <strong>9:00 AM</strong>. {booking_datetime.strftime('%I:%M %p')} is too early.<br><br>
🕒 <strong>Operating Hours:</strong> 9:00 AM - 10:00 PM<br><br>
💡 <i>Please try a later time. Just type the corrected time, like:</i><br>
• "9 AM"<br>
• "2 PM"
"""
    elif booking_datetime.hour >= 22 or (booking_datetime.hour == 22 and booking_datetime.minute > 0):
        return f"""❌ <strong>Too Late</strong><br><br>
I'm sorry, but our spa closes at <strong>10:00 PM</strong>. {booking_datetime.strftime('%I:%M %p')} is too late.<br><br>
🕒 <strong>Operating Hours:</strong> 9:00 AM - 10:00 PM<br><br>
💡 <i>Please try an earlier time. Just type the corrected time, like:</i><br>
• "9 PM"<br>
• "7 PM"
"""
    
    # --- TIME SLOT AVAILABILITY CHECK ---
    is_available, conflict = is_spa_slot_available(booking_datetime, 60)
    
    if not is_available:
        if conflict == "Past Booking":
            return f"""❌ <strong>Invalid Date</strong><br><br>
I'm sorry, but {booking_datetime.strftime('%A, %B %d, %Y at %I:%M %p')} is in the past.<br><br>
💡 <i>Please select a future date and time. Just type the corrected date and time, like:</i><br>
• "tomorrow at 2 PM"
"""
        elif conflict == "Outside Operating Hours":
            return f"""❌ <strong>Outside Operating Hours</strong><br><br>
I'm sorry, but our spa operates from <strong>9:00 AM to 10:00 PM</strong>.<br><br>
🕒 {booking_datetime.strftime('%I:%M %p')} is not available.<br><br>
💡 <i>Please select a time within our operating hours.</i>
"""
        elif isinstance(conflict, list):
            return format_conflict_message(conflict)
        else:
            return f"""❌ <strong>Time Slot Unavailable</strong><br><br>
I'm sorry, but the time slot <strong>{booking_datetime.strftime('%A, %B %d at %I:%M %p')}</strong> is not available.<br><br>
💡 <i>Please choose a different time. Just type the new time, like:</i><br>
• "3 PM"<br>
• "5 PM"
"""
    
    # --- CONFIRM BOOKING ---
    success, message = book_spa_slot("Mr. Alexander Vance", service, booking_datetime, 60)
    
    if success:
        st.session_state.latest_spa_booking = f"{booking_datetime.strftime('%b %d at %I:%M %p')} - {service}"
        st.session_state.awaiting_spa_booking = False
        return message
    else:
        return message

def process_cancel_booking(user_input):
    """
    Process booking cancellation request
    """
    # Check if user wants to view bookings first
    view_keywords = ["view", "show", "list", "see", "display", "查看", "显示", "列表", "我的预约"]
    if any(keyword in user_input.lower() for keyword in view_keywords) and "cancel" not in user_input.lower():
        return view_my_bookings()
    
    # If user just said "booking" or "my booking" without cancel/view context
    if user_input.lower().strip() in ["booking", "my booking", "bookings", "my bookings"]:
        return "📋 Would you like to <strong>view your bookings</strong> or <strong>cancel a booking</strong>? Please specify what you'd like to do."
    
    # Try to extract time from the input
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(?:am|pm)?',
        r'(\d{1,2})\s*(?:am|pm)',
        r'(\d{1,2})\s*o\'clock',
        r'at\s+(\d{1,2})\s*(?:am|pm)?',
        r'for\s+(\d{1,2})\s*(?:am|pm)?',
        r'(\d{1,2})\s*(?:am|pm)\s*(?:booking|appointment)?',
        r'(\d{1,2})(am|pm)',  # 9pm or 10am
    ]
    
    time_str = None
    for pattern in time_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                hour = int(match.group(1))
                if "pm" in user_input.lower() and hour < 12:
                    hour += 12
                elif "am" in user_input.lower() and hour == 12:
                    hour = 0
                time_str = f"{hour:02d}:00"
            else:
                hour = int(match.group(1))
                if "pm" in user_input.lower() and hour < 12:
                    hour += 12
                elif "am" in user_input.lower() and hour == 12:
                    hour = 0
                time_str = f"{hour:02d}:00"
            break
    
    if not time_str:
        return "🕐 Please tell me the time of the booking you'd like to cancel (e.g., 'Cancel my 2 PM booking' or 'Cancel my 10:30 AM appointment')"
    
    success, message = cancel_spa_booking(time_str)
    
    if success:
        st.session_state.awaiting_cancel_booking = False
        st.session_state.latest_spa_booking = None
    
    return message

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

    # ==========================================
    # SPA BOOKING DATE + TIME DETECTION
    # ==========================================
    # Use corrected_input instead of cleaned_input here.
    # clean_text() removes "/" and "-" from dates.
    # Example: 31/8/2026 9pm must remain unchanged.
    booking_text = corrected_input.lower().strip()

    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{1,2}[.]\d{1,2}[.]\d{2,4}\b',
        r'\b\d{1,2}\s+(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)\s+\d{4}\b',
        r'\b(?:today|todays|tomorrow|tmr|tomorow|yesterday|yest|yday|day after tomorrow|next week)\b'
    ]

    time_patterns = [
        r'\b\d{1,2}:\d{2}\s*(?:am|pm)?\b',
        r'\b\d{1,2}\s*(?:am|pm)\b',
        r'\b(?:noon|midday|midnight)\b',
        r'\b\d{1,2}\s*o\'clock\b',
        r'\b\d{1,2}\s+(?:in the\s+)?(?:morning|afternoon|evening|night)\b'
    ]

    has_date = any(
        re.search(pattern, booking_text, re.IGNORECASE)
        for pattern in date_patterns
    )

    has_time = any(
        re.search(pattern, booking_text, re.IGNORECASE)
        for pattern in time_patterns
    )

    # Do NOT treat standalone numbers as time.
    # Otherwise 31/8/2026 can be mistaken for an hour.
    is_spa_booking_likely = has_date and has_time

    # Date + time ALWAYS goes to spa booking first.
    if is_spa_booking_likely:
        result = process_spa_booking(corrected_input)

        if any(keyword in result.lower() for keyword in [
            "invalid",
            "too early",
            "too late",
            "already booked",
            "unavailable",
            "need a date",
            "need a time",
            "couldn't understand"
        ]):
            st.session_state.awaiting_spa_booking = True
        else:
            st.session_state.awaiting_spa_booking = False

        return correction_note + result

    # --- WEATHER: reached only when input is NOT a spa date + time booking ---
    weather_keywords = [
        "weather", "temperature", "forecast", "rain", "sunny", "cloudy", 
        "hot", "cold", "warm", "humid", "degrees", "°c", "°f",
        "今天天气", "天气预报", "温度", "下雨", "晴天", "气温",
        "weather today", "weather tomorrow", "how is the weather"
    ]
    
    is_weather_query = any(keyword in cleaned_input.lower() for keyword in weather_keywords)
    
    if is_weather_query:
        weather_res = get_realtime_weather()
        return correction_note + weather_res["weather_response"] + "|||" + weather_res["attraction_response"]

    # --- Check if this is a SPA BOOKING request (without date/time) ---
    spa_booking_phrases = ["spa booking", "booking spa", "book spa", "reserve spa"]
    is_spa_booking_phrase = any(phrase in cleaned_input.lower() for phrase in spa_booking_phrases)
    
    spa_keywords = ["spa", "massage", "facial", "hot stone", "aromatherapy", "预约spa", "订spa", "spa预约"]
    is_spa_related = any(keyword in cleaned_input.lower() for keyword in spa_keywords)
    
    if is_spa_booking_phrase or is_spa_related:
        result = process_spa_booking(user_input)
        if "I'm sorry" in result or "Invalid" in result or "Too Early" in result or "Too Late" in result or "already booked" in result or "Unavailable" in result or "needs a date" in result or "needs a time" in result:
            st.session_state.awaiting_spa_booking = True
        else:
            st.session_state.awaiting_spa_booking = False
        return correction_note + result

    # --- Check if this is a EXTEND BOOKING request ---
    extend_keywords = [
        "extend", "延长", "延期", "extend my stay", "extend booking",
        "extend room", "extend appointment", "add days", "add more days",
        "increase stay", "longer stay", "extend spa", "extend my room",
        "extend my spa", "extend check-out", "extend checkout"
    ]
    
    is_extend_request = any(keyword in cleaned_input.lower() for keyword in extend_keywords)
    
    if is_extend_request:
        result = process_extend_booking(user_input)
        if "How many additional days" in result or "Please tell me the time" in result or "Please tell me the new date" in result:
            st.session_state.awaiting_extend_booking = True
        else:
            st.session_state.awaiting_extend_booking = False
        return correction_note + result

    # --- Check if this is in extend booking context ---
    if st.session_state.awaiting_extend_booking:
        result = process_extend_booking(user_input)
        if "How many additional days" in result or "Please tell me the time" in result or "Please tell me the new date" in result:
            st.session_state.awaiting_extend_booking = True
        else:
            st.session_state.awaiting_extend_booking = False
        return correction_note + result

    # --- Check if this is a VIEW BOOKINGS request ---
    view_keywords = [
        "view my bookings", "show my bookings", "my bookings", "my reservation",
        "view appointments", "show appointments", "list my bookings",
        "查看我的预约", "我的预约", "预约记录", "查看预约"
    ]
    
    is_view_request = any(keyword in cleaned_input.lower() for keyword in view_keywords)
    
    if is_view_request:
        return correction_note + view_my_bookings()

    # --- Check if this is a CANCEL BOOKING request ---
    cancel_keywords = [
        "cancel my", "cancel this", "cancel the", "cancel booking",
        "取消我的", "取消预约", "取消预订", "cancellation",
        "i want to cancel", "i would like to cancel", "please cancel"
    ]
    
    is_cancel_request = any(keyword in cleaned_input.lower() for keyword in cancel_keywords)
    
    if "cancel" in cleaned_input.lower() and not is_view_request:
        is_cancel_request = True
    
    if is_cancel_request:
        result = process_cancel_booking(user_input)
        if "please tell me the time" in result.lower():
            st.session_state.awaiting_cancel_booking = True
        return correction_note + result

    # --- Check if this is in cancel booking context ---
    if st.session_state.awaiting_cancel_booking:
        st.session_state.awaiting_cancel_booking = False
        result = process_cancel_booking(user_input)
        if "please tell me the time" in result.lower():
            st.session_state.awaiting_cancel_booking = True
        return correction_note + result

    # --- If in spa booking context (user was previously booking) ---
    if st.session_state.awaiting_spa_booking:
        st.session_state.awaiting_spa_booking = False
        result = process_spa_booking(user_input)
        if "I'm sorry" in result or "Invalid" in result or "Too Early" in result or "Too Late" in result or "already booked" in result or "Unavailable" in result or "needs a date" in result or "needs a time" in result:
            st.session_state.awaiting_spa_booking = True
        return correction_note + result
        
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
        
        if predicted_tag == "extend_booking":
            result = process_extend_booking(user_input)
            if "How many additional days" in result or "Please tell me the time" in result or "Please tell me the new date" in result:
                st.session_state.awaiting_extend_booking = True
            return correction_note + result
        
        if predicted_tag == "cancel_booking":
            result = process_cancel_booking(user_input)
            if "please tell me the time" in result.lower():
                st.session_state.awaiting_cancel_booking = True
            return correction_note + result
        
        if predicted_tag == "view_bookings":
            return correction_note + view_my_bookings()
        
        if predicted_tag in ["ask_spa", "ask_spa_booking"]:
            st.session_state.awaiting_spa_booking = True
            result = process_spa_booking(user_input)
            if "I'm sorry" in result or "Invalid" in result or "Too Early" in result or "Too Late" in result or "already booked" in result or "Unavailable" in result or "needs a date" in result or "needs a time" in result:
                st.session_state.awaiting_spa_booking = True
            else:
                st.session_state.awaiting_spa_booking = False
            return correction_note + result

        if predicted_tag == "ask_weather":
            weather_res = get_realtime_weather()
            return correction_note + weather_res["weather_response"] + "|||" + weather_res["attraction_response"]

        if predicted_tag == "internal_call":
            return correction_note + render_internal_call_card()

        return correction_note + LUXURY_RESPONSES.get(predicted_tag, "Thank you. Our Concierge Desk is entirely at your service.")
        
    except Exception as e:
        return "I am at your service. Please feel free to ask about our room amenities, dining, or guest services."


# ==========================================
# 8. Styling Injection (Bright Luxury Theme)
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
# 9. PAGE 1: Luxury Dashboard & Banner Slider
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
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #7A7570; margin-bottom: 8px; font-weight: 600;">📅 Stay Duration</div>
            <div style="font-size: 20px; font-weight: 700; color: #1A1A1A;">{st.session_state.current_stay['check_in'].strftime('%d %b %Y')} – {st.session_state.current_stay['check_out'].strftime('%d %b %Y')}</div>
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
# 10. PAGE 2: Left/Right Chat Interface
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

        # --- Email Settings ---
        with st.expander("📧 Email Settings"):
            st.text_input("Your Email Address", value=st.session_state.guest_email, key="guest_email_input")
            if st.button("Update Email"):
                st.success(f"Email updated to: {st.session_state.guest_email}")

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
        user_prompt = st.chat_input("Type your request here (e.g., Wi-Fi, Spa, Weather, Breakfast, Extend Stay)...")
        if user_prompt:
            current_time = datetime.now().strftime("%I:%M %p")
            
            # Save User Message
            st.session_state.messages.append({
                "role": "user", 
                "content": user_prompt,
                "time": current_time
            })
            
            # Generate Response
            response_text = get_bot_response(user_prompt)
            
            # Check if response has split marker for weather
            if "|||" in response_text:
                parts = response_text.split("|||")
                # Send first response (weather)
                if parts[0].strip():
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": parts[0].strip(),
                        "time": current_time
                    })
                # Send second response (attractions) - only if it exists and is not empty
                if len(parts) > 1 and parts[1].strip():
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": parts[1].strip(),
                        "time": current_time
                    })
            else:
                # Normal single response
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text,
                    "time": current_time
                })
            
            st.rerun()
