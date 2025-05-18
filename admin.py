from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db, admin
from models import User, Doctor, Service, Appointment, Review, Portfolio, News
from utils import shamsi_to_gregorian, format_shamsi_date
from flask_admin.contrib.sqla import ModelView
from wtforms import TextAreaField, SelectField
from ai_service import generate_beauty_news
from datetime import date, time, datetime, timezone
from functools import wraps


admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')


# Middleware: فقط ادمین اجازه دسترسی دارد
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("شما دسترسی ندارید", "error")
            return redirect(url_for('main.index'))
        try:
            return f(*args, **kwargs)
        except Exception as e:
            flash(f"خطا در دسترسی: {e}", "error")
            return redirect(url_for('main.index'))
    return decorated


# Base Mixin برای همه ویوهای ادمین
class AdminRequiredMixin:
    def is_accessible(self):
        try:
            return current_user.is_authenticated and current_user.is_admin()
        except Exception as e:
            return False

    def inaccessible_callback(self, name, **kwargs):
        flash('دسترسی غیرمجاز', 'error')
        return redirect(url_for('main.index'))


# ویوهای ادمین
class UserModelView(AdminRequiredMixin, ModelView):
    column_list = ('username', 'email', 'phone', 'role', 'created_at', 'last_login')
    form_columns = ('username', 'email', 'phone', 'role', 'is_active')


class DoctorModelView(AdminRequiredMixin, ModelView):
    form_overrides = {'bio': TextAreaField}
    form_columns = ('name', 'title', 'bio', 'image_url', 'experience_years', 'education', 'certifications', 'services')


class ServiceModelView(AdminRequiredMixin, ModelView):
    form_overrides = {
        'description': TextAreaField,
        'short_description': TextAreaField
    }
    form_columns = ('name', 'description', 'short_description', 'price', 'duration', 'image_url', 'doctors')


class AppointmentModelView(AdminRequiredMixin, ModelView):
    form_overrides = {
        'notes': TextAreaField
    }

    form_choices = {
        'status': [
            ('pending', 'در انتظار'),
            ('confirmed', 'تایید شده'),
            ('canceled', 'لغو شده'),
            ('completed', 'انجام شده')
        ],
        'payment_status': [
            ('pending', 'در انتظار پرداخت'),
            ('paid', 'پرداخت شده')
        ]
    }

    form_columns = (
        'user',
        'doctor',
        'service',
        'date',
        'time',
        'status',
        'payment_status',
        'notes'
    )


class ReviewModelView(AdminRequiredMixin, ModelView):
    form_overrides = {'comment': TextAreaField}
    form_columns = ('user', 'service', 'rating', 'comment', 'is_approved')


class PortfolioModelView(AdminRequiredMixin, ModelView):
    form_overrides = {'description': TextAreaField}
    form_columns = ('service', 'title', 'description', 'before_image_url', 'after_image_url', 'is_featured')


class NewsModelView(AdminRequiredMixin, ModelView):
    form_overrides = {'content': TextAreaField}
    form_columns = ('title', 'content', 'image_url', 'is_published', 'is_ai_generated')

# ثبت ویوها در پنل ادمین
admin.add_view(UserModelView(User, db.session, name='کاربران', endpoint='users_admin'))
admin.add_view(DoctorModelView(Doctor, db.session, name='پزشکان', endpoint='doctors_admin'))
admin.add_view(ServiceModelView(Service, db.session, name='خدمات', endpoint='services_admin'))
admin.add_view(AppointmentModelView(Appointment, db.session, name='نوبت‌ها', endpoint='appointments_admin'))
admin.add_view(ReviewModelView(Review, db.session, name='نظرات', endpoint='reviews_admin'))
admin.add_view(PortfolioModelView(Portfolio, db.session, name='نمونه‌کارها', endpoint='portfolio_admin'))
admin.add_view(NewsModelView(News, db.session, name='اخبار', endpoint='news_admin'))


# داشبورد ادمین
@admin_bp.route('/')
@login_required
@admin_required
def index():
    stats = {
        "users": User.query.count(),
        "appointments": Appointment.query.count(),
        "pending": Appointment.query.filter_by(status='pending').count(),
        "today": Appointment.query.filter_by(date=date.today()).count()
    }

    recent_appointments = Appointment.query.order_by(Appointment.date.desc()).limit(5).all()
    formatted_appointments = []
    for a in recent_appointments:
        formatted_appointments.append({
            "id": a.id,
            "user_name": a.user.username if a.user else "_",
            "user_phone": a.user.phone if a.user else "_",
            "service_name": a.service.name if a.service else "_",
            "doctor_name": a.doctor.name if a.doctor else "_",
            "date": format_shamsi_date(a.date),
            "time": a.time.strftime('%H:%M'),
            "status": a.status,
            "payment_status": a.payment_status
        })

    return render_template('admin/index.html', stats=stats, recent_appointments=formatted_appointments)


# تولید خبر هوشمند با GPT
@admin_bp.route('/generate_news', methods=['GET', 'POST'])
@login_required
@admin_required
def generate_news():
    if request.method == 'POST':
        topic = request.form.get('topic')
        if not topic:
            flash('موضوع الزامی است', 'error')
            return redirect(url_for('admin_bp.generate_news'))
        try:
            title, content = generate_beauty_news(topic)
            db.session.add(News(title=title, content=content, is_published=True, is_ai_generated=True))
            db.session.commit()
            flash('خبر تولید شد', 'success')
            return redirect(url_for('news_admin.index_view'))
        except Exception as e:
            flash(f'خطا: {e}', 'error')

    return render_template('admin/generate_news.html')


# تولید چند خبر به‌صورت هم‌زمان
@admin_bp.route('/generate_multiple_news', methods=['POST'])
@login_required
@admin_required
def generate_multiple_news():
    topics = [
        "مراقبت از پوست در تابستان", "کرم ضدآفتاب", "روشن کردن پوست",
        "جوان‌سازی پوست", "درمان ریزش مو", "ماسک خانگی پوست",
        "تغذیه و پوست سالم", "مراقبت از پوست خشک"
    ]
    count, errors = 0, 0
    for topic in topics:
        try:
            title, content = generate_beauty_news(topic)
            if News.query.filter_by(title=title).first():
                continue
            db.session.add(News(title=title, content=content, is_published=True, is_ai_generated=True))
            count += 1
        except Exception as e:
            errors += 1
    db.session.commit()
    flash(f"{count} مقاله تولید شد - {errors} خطا", 'success' if count else 'warning')
    return redirect(url_for('admin_bp.index'))
