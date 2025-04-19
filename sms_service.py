import os
import requests
from config import Config

# Kavenegar SMS API key
KAVENEGAR_API_KEY = os.environ.get("KAVENEGAR_API_KEY")
KAVENEGAR_URL = "https://api.kavenegar.com/v1/{}/sms/send.json".format(KAVENEGAR_API_KEY)

def send_sms(receptor, message):
    """
    Send SMS using Kavenegar API
    """
    if not KAVENEGAR_API_KEY:
        print("Warning: KAVENEGAR_API_KEY not set. SMS not sent.")
        return False
    
    try:
        payload = {
            'receptor': receptor,
            'message': message,
        }
        
        response = requests.post(KAVENEGAR_URL, data=payload)
        
        if response.status_code == 200:
            print(f"SMS sent successfully to {receptor}")
            return True
        else:
            print(f"Failed to send SMS: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False

def send_verification_code(phone, code):
    """
    Send verification code via SMS
    """
    message = f"کد تایید کلینیک زیبایی: {code}"
    return send_sms(phone, message)

def send_confirmation_sms(phone, name, service, doctor, date, time):
    """
    Send appointment confirmation via SMS
    """
    message = f"کاربر گرامی {name}،\nنوبت شما برای خدمت {service} با دکتر {doctor} در تاریخ {date} ساعت {time} ثبت شد. لطفا 15 دقیقه قبل از نوبت در کلینیک حضور داشته باشید."
    return send_sms(phone, message)

def send_reminder_sms(phone, name, service, doctor, date, time):
    """
    Send appointment reminder via SMS
    """
    message = f"کاربر گرامی {name}،\nیادآوری نوبت شما برای خدمت {service} با دکتر {doctor} فردا در تاریخ {date} ساعت {time}. لطفا 15 دقیقه قبل از نوبت در کلینیک حضور داشته باشید."
    return send_sms(phone, message)

def send_appointment_status_sms(phone, name, status, service, doctor, date, time):
    """
    Send appointment status update via SMS
    """
    status_persian = {
        'confirmed': 'تایید',
        'canceled': 'لغو',
        'rescheduled': 'زمان‌بندی مجدد'
    }.get(status, status)
    
    message = f"کاربر گرامی {name}،\nنوبت شما برای خدمت {service} با دکتر {doctor} در تاریخ {date} ساعت {time} {status_persian} شد."
    
    if status == 'rescheduled':
        message += " لطفا برای اطلاعات بیشتر به پروفایل خود مراجعه کنید."
    
    return send_sms(phone, message)

# Function to send daily appointment reminders (to be called by a scheduler)
def send_daily_reminders():
    """
    Send reminders for tomorrow's appointments
    This should be scheduled to run once daily
    """
    from app import app
    from models import Appointment, User, Service, Doctor
    import datetime
    
    # Use application context
    with app.app_context():
        # Get tomorrow's date
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        
        # Get all confirmed appointments for tomorrow
        appointments = Appointment.query.filter_by(
            date=tomorrow,
            status='confirmed'
        ).all()
        
        for appointment in appointments:
            user = User.query.get(appointment.user_id)
            service = Service.query.get(appointment.service_id)
            doctor = Doctor.query.get(appointment.doctor_id)
            
            # Skip if user doesn't have phone number
            if not user.phone:
                continue
            
            # Convert to Shamsi date
            shamsi_date = utils.format_shamsi_date(tomorrow)
            time_str = appointment.time.strftime("%H:%M")
            
            # Send reminder
            send_reminder_sms(
                user.phone,
                user.username,
                service.name,
                doctor.name,
                shamsi_date,
                time_str
            )
