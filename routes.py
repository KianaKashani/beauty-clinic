from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app import db
from models import User, Doctor, Service, Appointment, Review, Portfolio, News
from utils import shamsi_to_gregorian, gregorian_to_shamsi, format_shamsi_date, admin_required, generate_available_time_slots
from ai_service import get_ai_consultation, generate_beauty_news
from payment_service import create_payment, verify_payment
from sms_service import send_confirmation_sms, send_reminder_sms
import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Get featured services (limit 4)
    featured_services = Service.query.limit(4).all()
    
    # Get featured doctors (limit 3)
    featured_doctors = Doctor.query.limit(3).all()
    
    # Get latest news (limit 3)
    latest_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).limit(3).all()
    
    # Get featured portfolio items (limit 6)
    featured_portfolio = Portfolio.query.filter_by(is_featured=True).limit(6).all()
    
    # Get approved reviews (limit 5)
    recent_reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                           services=featured_services,
                           doctors=featured_doctors,
                           news=latest_news,
                           portfolio=featured_portfolio,
                           reviews=recent_reviews)

@main.route('/about')
def about():
    # Get all doctors for the about page
    doctors = Doctor.query.all()
    return render_template('about.html', doctors=doctors)

@main.route('/services')
def services():
    # Get all services
    all_services = Service.query.all()
    return render_template('services.html', services=all_services)

@main.route('/service/<int:service_id>')
def service_detail(service_id):
    # Get service details
    service = Service.query.get_or_404(service_id)
    
    # Get doctors who provide this service
    service_doctors = service.doctors
    
    # Get related portfolio items
    portfolio = Portfolio.query.filter_by(service_id=service_id).all()
    
    # Get approved reviews for this service
    reviews = Review.query.filter_by(service_id=service_id, is_approved=True).order_by(Review.created_at.desc()).all()
    
    return render_template('service_detail.html', 
                           service=service, 
                           doctors=service_doctors,
                           portfolio=portfolio,
                           reviews=reviews)

@main.route('/doctors')
def doctors():
    # Get all doctors
    all_doctors = Doctor.query.all()
    return render_template('doctors.html', doctors=all_doctors)

@main.route('/portfolio')
def portfolio():
    # Get service filter from query parameters
    service_id = request.args.get('service_id', type=int)
    
    # Get all services for filter dropdown
    services = Service.query.all()
    
    # Get portfolio items, filtered by service if specified
    if service_id:
        portfolio_items = Portfolio.query.filter_by(service_id=service_id).all()
    else:
        portfolio_items = Portfolio.query.all()
    
    return render_template('portfolio.html', 
                           portfolio=portfolio_items,
                           services=services,
                           selected_service=service_id)

@main.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    if request.method == 'POST':
        service_id = request.form.get('service_id', type=int)
        doctor_id = request.form.get('doctor_id', type=int)
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        notes = request.form.get('notes', '')
        
        # Validate inputs
        if not all([service_id, doctor_id, date_str, time_str]):
            flash('لطفا تمامی فیلدها را پر کنید', 'error')
            return redirect(url_for('main.booking'))
        
        # Convert Shamsi date to Gregorian
        gregorian_date = shamsi_to_gregorian(date_str)
        if not gregorian_date:
            flash('تاریخ انتخابی نامعتبر است', 'error')
            return redirect(url_for('main.booking'))
        
        # Parse time string
        try:
            hours, minutes = map(int, time_str.split(':'))
            appointment_time = datetime.time(hour=hours, minute=minutes)
        except:
            flash('زمان انتخابی نامعتبر است', 'error')
            return redirect(url_for('main.booking'))
        
        # Create new appointment
        new_appointment = Appointment(
            user_id=current_user.id,
            service_id=service_id,
            doctor_id=doctor_id,
            date=gregorian_date,
            time=appointment_time,
            notes=notes,
            status='pending',
            payment_status='pending'
        )
        
        # Save to database
        db.session.add(new_appointment)
        db.session.commit()
        
        # Send confirmation SMS
        if current_user.phone:
            service = Service.query.get(service_id)
            doctor = Doctor.query.get(doctor_id)
            send_confirmation_sms(
                current_user.phone,
                current_user.username,
                service.name,
                doctor.name,
                date_str,
                time_str
            )
        
        # Redirect to payment
        return redirect(url_for('main.payment', appointment_id=new_appointment.id))
    
    # GET request - show booking form
    services = Service.query.all()
    doctors = Doctor.query.all()
    
    return render_template('booking.html', services=services, doctors=doctors)

@main.route('/get_available_times')
@login_required
def get_available_times():
    doctor_id = request.args.get('doctor_id', type=int)
    service_id = request.args.get('service_id', type=int)
    date_str = request.args.get('date')
    
    if not all([doctor_id, service_id, date_str]):
        return jsonify({'error': 'Missing parameters'}), 400
    
    # Convert Shamsi date to Gregorian
    gregorian_date = shamsi_to_gregorian(date_str)
    if not gregorian_date:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Generate available time slots
    available_slots = generate_available_time_slots(doctor_id, service_id, gregorian_date)
    
    # Format time slots for JSON response
    formatted_slots = [slot.strftime('%H:%M') for slot in available_slots]
    
    return jsonify({'available_times': formatted_slots})

@main.route('/payment/<int:appointment_id>')
@login_required
def payment(appointment_id):
    # Get appointment details
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if the appointment belongs to the current user
    if appointment.user_id != current_user.id:
        flash('شما دسترسی به این نوبت را ندارید', 'error')
        return redirect(url_for('main.profile'))
    
    # If payment is already completed
    if appointment.payment_status == 'paid':
        flash('پرداخت قبلا انجام شده است', 'info')
        return redirect(url_for('main.profile'))
    
    # Get service details for payment amount
    service = Service.query.get(appointment.service_id)
    amount = service.price
    
    # Create payment request
    payment_url, payment_id = create_payment(amount, f"رزرو نوبت {service.name}")
    
    # Update appointment with payment ID
    appointment.payment_id = payment_id
    db.session.commit()
    
    # Redirect to payment gateway
    return redirect(payment_url)

@main.route('/payment/verify')
def payment_verify():
    authority = request.args.get('Authority')
    status = request.args.get('Status')
    
    # Find appointment by payment ID
    appointment = Appointment.query.filter_by(payment_id=authority).first()
    
    if not appointment:
        flash('نوبت مورد نظر یافت نشد', 'error')
        return redirect(url_for('main.profile'))
    
    if status == 'OK':
        # Get service price
        service = Service.query.get(appointment.service_id)
        amount = service.price
        
        # Verify payment with payment service
        is_verified = verify_payment(authority, amount)
        
        if is_verified:
            # Update appointment status
            appointment.payment_status = 'paid'
            appointment.status = 'confirmed'
            db.session.commit()
            
            flash('پرداخت با موفقیت انجام شد و نوبت شما تایید شد', 'success')
        else:
            flash('خطا در تایید پرداخت', 'error')
    else:
        flash('پرداخت توسط کاربر لغو شد', 'warning')
    
    return redirect(url_for('main.profile'))

@main.route('/profile')
@login_required
def profile():
    # Get user's appointments
    user_appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.date.desc()).all()
    
    # Format appointments for display
    formatted_appointments = []
    for appointment in user_appointments:
        service = Service.query.get(appointment.service_id)
        doctor = Doctor.query.get(appointment.doctor_id)
        
        formatted_appointment = {
            'id': appointment.id,
            'service_name': service.name,
            'doctor_name': doctor.name,
            'date': format_shamsi_date(appointment.date),
            'time': appointment.time.strftime('%H:%M'),
            'status': appointment.status,
            'payment_status': appointment.payment_status
        }
        
        formatted_appointments.append(formatted_appointment)
    
    return render_template('profile.html', appointments=formatted_appointments, user=current_user)

@main.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if the appointment belongs to the current user
    if appointment.user_id != current_user.id:
        flash('شما دسترسی به این نوبت را ندارید', 'error')
        return redirect(url_for('main.profile'))
    
    # Check if the appointment can be canceled (not already completed or canceled)
    if appointment.status in ['completed', 'canceled']:
        flash('این نوبت قابل لغو نیست', 'error')
        return redirect(url_for('main.profile'))
    
    # Update appointment status
    appointment.status = 'canceled'
    db.session.commit()
    
    flash('نوبت با موفقیت لغو شد', 'success')
    return redirect(url_for('main.profile'))

@main.route('/submit_review', methods=['POST'])
@login_required
def submit_review():
    service_id = request.form.get('service_id', type=int)
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment')
    
    # Validate inputs
    if not all([rating, comment]) or rating < 1 or rating > 5:
        flash('لطفا امتیاز و نظر خود را وارد کنید', 'error')
        
        # Redirect back to the referring page
        if service_id:
            return redirect(url_for('main.service_detail', service_id=service_id))
        else:
            return redirect(url_for('main.index'))
    
    # Create new review
    new_review = Review(
        user_id=current_user.id,
        service_id=service_id,  # Can be None for general reviews
        rating=rating,
        comment=comment,
        is_approved=False  # Reviews need approval
    )
    
    # Save to database
    db.session.add(new_review)
    db.session.commit()
    
    flash('نظر شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد', 'success')
    
    # Redirect back to the referring page
    if service_id:
        return redirect(url_for('main.service_detail', service_id=service_id))
    else:
        return redirect(url_for('main.index'))

@main.route('/news')
def news():
    # Get all published news
    all_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).all()
    return render_template('news.html', news=all_news)

@main.route('/news/<int:news_id>')
def news_detail(news_id):
    # Get news item
    news_item = News.query.get_or_404(news_id)
    
    # Check if published
    if not news_item.is_published:
        flash('این خبر در دسترس نیست', 'error')
        return redirect(url_for('main.news'))
    
    # Get related news
    related_news = News.query.filter(News.id != news_id, News.is_published == True).order_by(News.created_at.desc()).limit(3).all()
    
    return render_template('news_detail.html', news=news_item, related_news=related_news)

@main.route('/ai_consultation', methods=['POST'])
def ai_consultation():
    question = request.form.get('question')
    
    if not question:
        return jsonify({'error': 'لطفا سوال خود را وارد کنید'}), 400
    
    try:
        response = get_ai_consultation(question)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
