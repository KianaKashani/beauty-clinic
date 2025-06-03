
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, Doctor, Service, Appointment, Review, Portfolio, News
from utils import shamsi_to_gregorian, format_shamsi_date, admin_required
from ai_service import get_ai_consultation, generate_beauty_news
from payment_service import create_payment, verify_payment
from sms_service import send_confirmation_sms
from datetime import datetime, timedelta, time as dt_time
import re

main = Blueprint('main', __name__)

def generate_available_time_slots(doctor_id, service_id, gregorian_date):
    start_time = dt_time(9, 0)  # ساعت شروع کاری (9 صبح)
    end_time = dt_time(17, 0)   # ساعت پایان کاری (5 عصر)

    slots = []
    current_dt = datetime.combine(gregorian_date, start_time)
    end_dt = datetime.combine(gregorian_date, end_time)

    now = datetime.now()

    while current_dt <= end_dt:
        # فقط تایم‌های آینده و هنوز نرسیده رو اضافه کن
        if current_dt > now:
            slots.append(current_dt)
        current_dt += timedelta(minutes=30)

    # گرفتن وقت‌های رزرو شده برای آن دکتر، سرویس و تاریخ (و وضعیت pending یا confirmed)
    booked_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.service_id == service_id,
        Appointment.date == gregorian_date,
        Appointment.status.in_(["pending", "confirmed"])
    ).all()

    booked_times = [datetime.combine(appt.date, appt.time) for appt in booked_appointments]

    # حذف تایم‌های رزرو شده از لیست تایم‌های آزاد
    available_slots = [slot for slot in slots if slot not in booked_times]

    return available_slots

@main.route('/')
def index():
    featured_services = Service.query.limit(4).all()
    featured_doctors = Doctor.query.limit(3).all()
    latest_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).limit(3).all()
    featured_portfolio = Portfolio.query.filter_by(is_featured=True).limit(6).all()
    recent_reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(5).all()
    return render_template('index.html',
                           services=featured_services,
                           doctors=featured_doctors,
                           news=latest_news,
                           portfolio=featured_portfolio,
                           reviews=recent_reviews)

@main.route('/about')
def about():
    doctors = Doctor.query.all()
    return render_template('about.html', doctors=doctors)

@main.route('/services')
def services():
    all_services = Service.query.all()
    return render_template('services.html', services=all_services)

@main.route('/service/<int:service_id>')
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    service_doctors = service.doctors
    portfolio = Portfolio.query.filter_by(service_id=service_id).all()
    reviews = Review.query.filter_by(service_id=service_id, is_approved=True).order_by(Review.created_at.desc()).all()
    return render_template('service_detail.html',
                           service=service,
                           doctors=service_doctors,
                           portfolio=portfolio,
                           reviews=reviews)

@main.route('/doctors')
def doctors():
    all_doctors = Doctor.query.all()
    return render_template('doctors.html', doctors=all_doctors)

@main.route('/portfolio')
def portfolio():
    service_id = request.args.get('service_id', type=int)
    services = Service.query.all()
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
        date_str = request.form.get('date', '').strip()
        time_str = request.form.get('time', '').strip()
        notes = request.form.get('notes', '')

        if not all([service_id, doctor_id, date_str, time_str]):
            flash('لطفا تمامی فیلدها را پر کنید', 'error')
            return redirect(url_for('main.booking'))

        if not re.match(r'^\d{4}/\d{2}/\d{2}$', date_str):
            flash('فرمت تاریخ نامعتبر است. مثال: 1403/02/28', 'error')
            return redirect(url_for('main.booking'))

        gregorian_date = shamsi_to_gregorian(date_str)
        if not gregorian_date:
            flash('تاریخ انتخابی نامعتبر است', 'error')
            return redirect(url_for('main.booking'))

        if not re.match(r'^\d{2}:\d{2}$', time_str):
            flash('فرمت زمان معتبر نیست. مثال: 09:30', 'error')
            return redirect(url_for('main.booking'))

        try:
            hours, minutes = map(int, time_str.split(':'))
            appointment_time = dt_time(hour=hours, minute=minutes)
        except Exception as e:
            print('Error parsing time:', e)
            flash('زمان انتخابی نامعتبر است', 'error')
            return redirect(url_for('main.booking'))

        # بررسی تداخل رزرو: تایم انتخابی آزاد باشد
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            service_id=service_id,
            date=gregorian_date,
            time=appointment_time,
            status='confirmed'
        ).first()
        if existing:
            flash('این زمان قبلا رزرو شده است. لطفا زمان دیگری انتخاب کنید.', 'error')
            return redirect(url_for('main.booking'))

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

        db.session.add(new_appointment)
        db.session.commit()

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

        return redirect(url_for('main.profile'))

    services = Service.query.all()
    doctors = Doctor.query.all()
    return render_template('booking.html', services=services, doctors=doctors)

@main.route('/get_service_doctors')
def get_service_doctors():
    service_id = request.args.get('service_id', type=int)
    if not service_id:
        return jsonify({'error': 'Service ID is required'}), 400
    service = Service.query.get_or_404(service_id)
    doctors = service.doctors
    return jsonify({
        'doctors': [{'id': doctor.id, 'name': doctor.name} for doctor in doctors]
    })

@main.route('/get_available_times')
@login_required
def get_available_times():
    doctor_id = request.args.get('doctor_id', type=int)
    service_id = request.args.get('service_id', type=int)
    date_str = request.args.get('date')

    if not all([doctor_id, service_id, date_str]):
        return jsonify({'error': 'Missing parameters'}), 400

    gregorian_date = shamsi_to_gregorian(date_str)
    if not gregorian_date:
        return jsonify({'error': 'Invalid date format'}), 400

    available_slots = generate_available_time_slots(doctor_id, service_id, gregorian_date)
    formatted_slots = [slot.strftime('%H:%M') for slot in available_slots]
    return jsonify({'available_times': formatted_slots})

@main.route('/payment/<int:appointment_id>')
@login_required
def payment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.user_id != current_user.id:
        flash('شما دسترسی به این نوبت را ندارید', 'error')
        return redirect(url_for('main.profile'))
    if appointment.payment_status == 'paid':
        flash('پرداخت قبلا انجام شده است', 'info')
        return redirect(url_for('main.profile'))
    service = Service.query.get(appointment.service_id)
    amount = service.price
    payment_url, payment_id = create_payment(amount, f"رزرو نوبت {service.name}")
    appointment.payment_id = payment_id
    db.session.commit()
    return redirect(payment_url)

@main.route('/payment/verify')
def payment_verify():
    authority = request.args.get('Authority')
    status = request.args.get('Status')
    appointment = Appointment.query.filter_by(payment_id=authority).first()
    if not appointment:
        flash('نوبت مورد نظر یافت نشد', 'error')
        return redirect(url_for('main.profile'))
    if status == 'OK':
        service = Service.query.get(appointment.service_id)
        amount = service.price
        is_verified = verify_payment(authority, amount)
        if is_verified:
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
    user_appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.date.desc()).all()
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
    if appointment.user_id != current_user.id:
        flash('شما دسترسی به این نوبت را ندارید', 'error')
        return redirect(url_for('main.profile'))
    if appointment.status in ['completed', 'canceled']:
        flash('این نوبت قابل لغو نیست', 'error')
        return redirect(url_for('main.profile'))
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
    if not all([rating, comment]) or rating < 1 or rating > 5:
        flash('لطفا امتیاز و نظر خود را وارد کنید', 'error')
        if service_id:
            return redirect(url_for('main.service_detail', service_id=service_id))
        else:
            return redirect(url_for('main.index'))
    new_review = Review(
        user_id=current_user.id,
        service_id=service_id,
        rating=rating,
        comment=comment,
        is_approved=False
    )
    db.session.add(new_review)
    db.session.commit()
    flash('نظر شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد', 'success')
    if service_id:
        return redirect(url_for('main.service_detail', service_id=service_id))
    else:
        return redirect(url_for('main.index'))

@main.route('/news')
def news():
    all_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).all()
    if not all_news:
        try:
            from ai_service import generate_beauty_news
            topics = [
                "مراقبت از پوست در فصل تابستان",
                "اهمیت استفاده از کرم ضد آفتاب",
                "روش‌های طبیعی برای روشن کردن پوست"
            ]
            for topic in topics:
                try:
                    title, content = generate_beauty_news(topic)
                    news = News(
                        title=title,
                        content=content,
                        is_published=True,
                        is_ai_generated=True
                    )
                    db.session.add(news)
                except Exception as e:
                    print(f"Error generating article for topic {topic}: {str(e)}")
            db.session.commit()
            all_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).all()
        except Exception as e:
            print(f"Error generating sample articles: {e}")
            flash('خطا در بارگذاری مقالات', 'error')
    return render_template('news.html', news=all_news)

@main.route('/news/<int:news_id>')
def news_detail(news_id):
    news_item = News.query.get_or_404(news_id)
    if not news_item.is_published:
        flash('این خبر در دسترس نیست', 'error')
        return redirect(url_for('main.news'))
    related_news = News.query.filter(News.id != news_id, News.is_published == True).order_by(News.created_at.desc()).limit(3).all()
    return render_template('news_detail.html', news=news_item, related_news=related_news)

@main.route('/generate_ai_news')
@login_required
@admin_required
def generate_ai_news():
    topics = [
        "روش‌های نوین جوانسازی پوست",
        "تکنولوژی‌های جدید در لیزر درمانی",
        "مراقبت‌های پس از تزریق ژل و بوتاکس",
        "تغذیه و تأثیر آن بر زیبایی پوست"
    ]
    for topic in topics:
        title, content = generate_beauty_news(topic)
        if not title or not content:
            continue
        news = News(
            title=title,
            content=content,
            is_published=True,
            is_ai_generated=True
        )
        db.session.add(news)
    db.session.commit()
    flash("مقالات جدید با موفقیت تولید و منتشر شدند", "success")
    return redirect(url_for("main.news"))

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