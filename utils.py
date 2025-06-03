import re
import random
import string
import jdatetime
from datetime import datetime, timedelta
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def shamsi_to_gregorian(shamsi_date_str):
    """Convert Shamsi (Jalali) date to Gregorian date"""
    try:
        # Parse Shamsi date string (assumed format: YYYY/MM/DD)
        year, month, day = map(int, shamsi_date_str.split('/'))
        
        # Convert to Gregorian date
        jalali_date = jdatetime.date(year, month, day)
        gregorian_date = jalali_date.togregorian()
        
        return gregorian_date
    except Exception as e:
        print(f"Error converting date: {e}")
        return None

def gregorian_to_shamsi(gregorian_date):
    """Convert Gregorian date to Shamsi (Jalali) date"""
    try:
        jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
        return jalali_date
    except Exception as e:
        print(f"Error converting date: {e}")
        return None

def format_shamsi_date(gregorian_date):
    """Format Gregorian date as a Shamsi (Jalali) date string"""
    if not gregorian_date:
        return ""
    
    jalali_date = gregorian_to_shamsi(gregorian_date)
    return jalali_date.strftime("%Y/%m/%d")

def format_time(time_obj):
    """Format time object as HH:MM string"""
    if not time_obj:
        return ""
    
    return time_obj.strftime("%H:%M")

def generate_unique_code(length=6):
    """Generate a random alphanumeric code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def validate_phone_number(phone):
    """Validate Iranian phone number format"""
    # number format: +98XXXXXXXXXX or 09XXXXXXXXXX
    # Also accepting the 9XXXXXXXXX format from the form
    pattern = r'^(\+98|0)?9\d{9}$'
    return bool(re.match(pattern, phone))

def normalize_phone_number(phone):
    """Normalize phone number to standard format (09XXXXXXXXXX)"""
    if not phone:
        return None
    
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # If starts with 98, replace with 0
    if phone.startswith('98'):
        phone = '0' + phone[2:]
    
    # If it's just a 10-digit number starting with 9, add a leading 0
    if len(phone) == 10 and phone.startswith('9'):
        phone = '0' + phone
    
    # Ensure it starts with 09
    if not phone.startswith('09'):
        return None
    
    # Ensure it has the correct length
    if len(phone) != 11:
        return None
    
    return phone

def admin_required(f):
    """Decorator to require admin role for a view function"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('شما دسترسی لازم برای این صفحه را ندارید', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def generate_available_time_slots(doctor_id, service_id, selected_date):
    """Generate available time slots for appointments"""
    from models import Appointment, Service
    from app import db
    from config import Config
    
    # Convert selected date to Gregorian if it's in Shamsi format
    if isinstance(selected_date, str):
        selected_date = shamsi_to_gregorian(selected_date)
    
    # Get service duration or use default
    service = Service.query.get(service_id)
    duration = service.duration if service else Config.DEFAULT_APPOINTMENT_DURATION
    
    # Define working hours
    start_hour = Config.WORKING_HOURS_START
    end_hour = Config.WORKING_HOURS_END
    
    # Generate all possible time slots
    all_slots = []
    current_time = datetime.combine(selected_date, datetime.min.time().replace(hour=start_hour))
    end_time = datetime.combine(selected_date, datetime.min.time().replace(hour=end_hour))
    
    while current_time + timedelta(minutes=duration) <= end_time:
        all_slots.append(current_time.time())
        current_time += timedelta(minutes=duration)
    
    # Get existing appointments for the selected doctor and date
    existing_appointments = Appointment.query.filter_by(
        doctor_id=doctor_id,
        date=selected_date
    ).all()
    
    # Exclude booked slots
    booked_slots = [appointment.time for appointment in existing_appointments]
    available_slots = [slot for slot in all_slots if slot not in booked_slots]
    
    return available_slots
