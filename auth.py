import os
import json
import requests
import random
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from oauthlib.oauth2 import WebApplicationClient
from app import db
from models import User
from utils import validate_phone_number, normalize_phone_number
from sms_service import send_verification_code

auth = Blueprint('auth', __name__)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Setup Google OAuth client
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Make sure to use this redirect URL. It has to match the one in the whitelist
DEV_REDIRECT_URL = f'https://{os.environ.get("REPLIT_DEV_DOMAIN", "localhost")}/google_login/callback'

# Display setup instructions
print(f"""To make Google authentication work:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {DEV_REDIRECT_URL} to Authorized redirect URIs

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Determine login method
        login_method = request.form.get('login_method', 'password')
        
        if login_method == 'password':
            # Login with password
            identifier = request.form.get('identifier')  # Email or phone
            password = request.form.get('password')
            
            # Validate inputs
            if not identifier or not password:
                flash('لطفا تمامی فیلدها را پر کنید', 'error')
                return render_template('login.html')
            
            # Check if identifier is email or phone
            if '@' in identifier:
                user = User.query.filter_by(email=identifier).first()
            else:
                # Normalize phone number
                phone = normalize_phone_number(identifier)
                if not phone:
                    flash('شماره تلفن نامعتبر است', 'error')
                    return render_template('login.html')
                
                user = User.query.filter_by(phone=phone).first()
            
            # Check if user exists and password is correct
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('main.index'))
            else:
                flash('نام کاربری یا رمز عبور اشتباه است', 'error')
        
        elif login_method == 'otp':
            # Login with OTP
            phone = normalize_phone_number(request.form.get('phone'))
            
            if not phone or not validate_phone_number(phone):
                flash('شماره تلفن نامعتبر است', 'error')
                return render_template('login.html')
            
            # Check if user exists
            user = User.query.filter_by(phone=phone).first()
            if not user:
                flash('کاربری با این شماره تلفن یافت نشد', 'error')
                return render_template('login.html')
            
            # Generate OTP code
            otp_code = str(random.randint(100000, 999999))
            
            # Save OTP in session
            session['otp_phone'] = phone
            session['otp_code'] = otp_code
            
            try:
                # Send OTP via SMS (if service available)
                send_verification_code(phone, otp_code)
                flash('کد تایید به شماره تلفن شما ارسال شد', 'info')
            except Exception as e:
                # If SMS service fails, display the code on screen (for demo purposes)
                flash(f'کد تایید: {otp_code} (برای اهداف نمایشی نمایش داده شد)', 'warning')
                print(f"SMS service error: {e}")
            
            return redirect(url_for('auth.verify_otp'))
    
    return render_template('login.html')

@auth.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Check if OTP information is in session
    if 'otp_phone' not in session or 'otp_code' not in session:
        flash('لطفا مجددا وارد شوید', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        entered_code = request.form.get('otp_code')
        
        if entered_code == session['otp_code']:
            # OTP is correct
            user = User.query.filter_by(phone=session['otp_phone']).first()
            
            if user:
                login_user(user)
                
                # Clear OTP session data
                session.pop('otp_phone', None)
                session.pop('otp_code', None)
                
                return redirect(url_for('main.index'))
            else:
                flash('خطایی رخ داد. لطفا مجددا تلاش کنید', 'error')
                return redirect(url_for('auth.login'))
        else:
            flash('کد وارد شده اشتباه است', 'error')
    
    return render_template('verify_otp.html', phone=session.get('otp_phone'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = normalize_phone_number(request.form.get('phone'))
        register_method = request.form.get('register_method', 'password')
        
        # Validate common inputs
        if not username or not phone:
            flash('لطفا تمامی فیلدهای الزامی را پر کنید', 'error')
            return render_template('register.html')
        
        if not validate_phone_number(phone):
            flash('شماره تلفن نامعتبر است', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(phone=phone).first():
            flash('این شماره تلفن قبلا ثبت شده است', 'error')
            return render_template('register.html')
        
        if email and User.query.filter_by(email=email).first():
            flash('این ایمیل قبلا ثبت شده است', 'error')
            return render_template('register.html')
            
        # Handle different registration methods
        if register_method == 'password':
            # Registration with password
            password = request.form.get('password')
            password_confirm = request.form.get('password_confirm')
            
            if not password:
                flash('لطفا رمز عبور را وارد کنید', 'error')
                return render_template('register.html')
                
            if password != password_confirm:
                flash('تکرار رمز عبور مطابقت ندارد', 'error')
                return render_template('register.html')
                
            # Create new user directly
            new_user = User(
                username=username,
                email=email,
                phone=phone
            )
            new_user.set_password(password)
            
            # Save to database
            db.session.add(new_user)
            db.session.commit()
            
            # Login the new user
            login_user(new_user)
            
            flash('ثبت نام با موفقیت انجام شد', 'success')
            return redirect(url_for('main.index'))
            
        elif register_method == 'otp':
            # Registration with OTP
            # Generate OTP code
            otp_code = str(random.randint(100000, 999999))
            
            # Save registration info and OTP in session
            session['register_username'] = username
            session['register_email'] = email
            session['register_phone'] = phone
            session['register_otp'] = otp_code
            
            # Generate a random password for the user
            random_password = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
            session['register_password'] = random_password
            
            try:
                # Send OTP via SMS (if service available)
                send_verification_code(phone, otp_code)
                flash('کد تایید به شماره تلفن شما ارسال شد', 'info')
            except Exception as e:
                # If SMS service fails, display the code on screen (for demo purposes)
                flash(f'کد تایید: {otp_code} (برای اهداف نمایشی نمایش داده شد)', 'warning')
                print(f"SMS service error: {e}")
            
            return redirect(url_for('auth.verify_register'))
        
        else:
            flash('روش ثبت نام نامعتبر است', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@auth.route('/verify_register', methods=['GET', 'POST'])
def verify_register():
    # Check if registration information is in session
    if not all(k in session for k in ['register_username', 'register_phone', 'register_password', 'register_otp']):
        flash('لطفا مجددا ثبت نام کنید', 'error')
        return redirect(url_for('auth.register'))
    
    if request.method == 'POST':
        entered_code = request.form.get('otp_code')
        
        if entered_code == session['register_otp']:
            # OTP is correct, create new user
            new_user = User(
                username=session['register_username'],
                email=session['register_email'],
                phone=session['register_phone']
            )
            new_user.set_password(session['register_password'])
            
            # Save to database
            db.session.add(new_user)
            db.session.commit()
            
            # Clear registration session data
            for key in ['register_username', 'register_email', 'register_phone', 'register_password', 'register_otp']:
                session.pop(key, None)
            
            # Login the new user
            login_user(new_user)
            
            flash('ثبت نام با موفقیت انجام شد', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('کد وارد شده اشتباه است', 'error')
    
    return render_template('verify_register.html', phone=session.get('register_phone'))

@auth.route('/google_login')
def google_login():
    # Get Google provider configuration
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Prepare request URI for Google login
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        # Replacing http:// with https:// is important as the external
        # protocol must be https to match the URI whitelisted
        redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
        scope=["openid", "email", "profile"],
    )
    
    # Redirect to Google's OAuth 2.0 server
    return redirect(request_uri)

@auth.route('/google_login/callback')
def google_callback():
    # Get authorization code from Google
    code = request.args.get("code")
    
    # Get Google provider configuration
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Prepare token request
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        # Replacing http:// with https:// is important as the external
        # protocol must be https to match the URI whitelisted
        authorization_response=request.url.replace("http://", "https://"),
        redirect_url=request.base_url.replace("http://", "https://"),
        code=code
    )
    
    # Exchange authorization code for tokens
    try:
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET else None,
        )
        
        if token_response.status_code != 200:
            flash("خطا در احراز هویت با گوگل. لطفا مجددا تلاش کنید.", "error")
            print(f"Google auth error: {token_response.text}")
            return redirect(url_for("auth.login"))
    except Exception as e:
        flash("خطا در ارتباط با سرور گوگل. لطفا مجددا تلاش کنید.", "error")
        print(f"Google auth connection error: {str(e)}")
        return redirect(url_for("auth.login"))
    
    # Parse the token response
    client.parse_request_body_response(json.dumps(token_response.json()))
    
    # Get user info from Google
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    
    # Process user info
    if userinfo_response.json().get("email_verified"):
        email = userinfo_response.json()["email"]
        username = userinfo_response.json().get("given_name", "")
    else:
        flash("ایمیل کاربر توسط گوگل تایید نشده است", "error")
        return redirect(url_for("auth.login"))
    
    # Find or create user
    user = User.query.filter_by(email=email).first()
    if not user:
        # Create new user
        user = User(username=username, email=email)
        # Generate a random password for the user
        random_password = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
        user.set_password(random_password)
        
        db.session.add(user)
        db.session.commit()
    
    # Log in the user
    login_user(user)
    
    return redirect(url_for("main.index"))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('شما با موفقیت خارج شدید', 'info')
    return redirect(url_for('main.index'))
