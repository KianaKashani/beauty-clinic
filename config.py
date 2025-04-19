import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'beauty_clinic_secret_key')
    FLASK_APP = 'app.py'
    FLASK_ENV = 'development'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAI configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Google OAuth configuration
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    
    # SMS service configuration (Kavenegar)
    KAVENEGAR_API_KEY = os.environ.get('KAVENEGAR_API_KEY')
    
    # Payment gateway configuration (ZarinPal)
    ZARINPAL_MERCHANT_ID = os.environ.get('ZARINPAL_MERCHANT_ID')
    ZARINPAL_CALLBACK_URL = os.environ.get('ZARINPAL_CALLBACK_URL', 'https://yourdomain.com/payment/verify')
    
    # Other application settings
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@beautyclinic.com')
    CLINIC_PHONE = os.environ.get('CLINIC_PHONE', '021-12345678')
    CLINIC_ADDRESS = os.environ.get('CLINIC_ADDRESS', 'تهران، خیابان ولیعصر، پلاک 123')
    CLINIC_INSTAGRAM = os.environ.get('CLINIC_INSTAGRAM', 'beauty_clinic')
    
    # Working hours (24-hour format)
    WORKING_HOURS_START = 9  # 9 AM
    WORKING_HOURS_END = 19   # 7 PM
    
    # Appointment duration in minutes
    DEFAULT_APPOINTMENT_DURATION = 60
