from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db, admin
from models import User, Doctor, Service, Appointment, Review, Portfolio, News
from utils import admin_required, shamsi_to_gregorian, format_shamsi_date
from flask_admin.contrib.sqla import ModelView
from wtforms import TextAreaField, SelectField
from ai_service import generate_beauty_news
import datetime

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

# Custom ModelView classes with admin_required
class AdminRequiredMixin:
    def is_accessible(self):
        from flask_login import current_user
        return current_user.is_authenticated and current_user.is_admin()
    
    def inaccessible_callback(self, name, **kwargs):
        flash('شما دسترسی لازم برای این صفحه را ندارید', 'error')
        return redirect(url_for('main.index'))

class UserModelView(AdminRequiredMixin, ModelView):
    column_list = ('id', 'username', 'email', 'phone', 'role', 'created_at', 'last_login', 'is_active')
    column_searchable_list = ('username', 'email', 'phone')
    column_filters = ('role', 'is_active', 'created_at')
    form_columns = ('username', 'email', 'phone', 'role', 'is_active')
    column_labels = {
        'id': 'شناسه',
        'username': 'نام کاربری',
        'email': 'ایمیل',
        'phone': 'تلفن',
        'role': 'نقش',
        'created_at': 'تاریخ ثبت نام',
        'last_login': 'آخرین ورود',
        'is_active': 'فعال'
    }

class DoctorModelView(AdminRequiredMixin, ModelView):
    column_list = ('id', 'name', 'title', 'experience_years')
    form_columns = ('name', 'title', 'bio', 'image_url', 'experience_years', 'education', 'certifications', 'services')
    form_overrides = {
        'bio': TextAreaField,
        'education': TextAreaField,
        'certifications': TextAreaField
    }
    column_labels = {
        'id': 'شناسه',
        'name': 'نام',
        'title': 'تخصص',
        'bio': 'بیوگرافی',
        'image_url': 'تصویر',
        'experience_years': 'سابقه (سال)',
        'education': 'تحصیلات',
        'certifications': 'گواهینامه ها',
        'services': 'خدمات'
    }

class ServiceModelView(AdminRequiredMixin, ModelView):
    column_list = ('id', 'name', 'price', 'duration')
    form_columns = ('name', 'description', 'short_description', 'price', 'duration', 'image_url', 'doctors')
    form_overrides = {
        'description': TextAreaField,
        'short_description': TextAreaField
    }
    column_labels = {
        'id': 'شناسه',
        'name': 'نام خدمت',
        'description': 'توضیحات کامل',
        'short_description': 'توضیحات کوتاه',
        'price': 'قیمت',
        'duration': 'مدت زمان (دقیقه)',
        'image_url': 'تصویر',
        'doctors': 'پزشکان'
    }

class AppointmentModelView(AdminRequiredMixin, ModelView):
    column_list = ('id', 'user', 'doctor', 'service', 'date', 'time', 'status', 'payment_status')
    column_searchable_list = ('user.username', 'user.phone', 'doctor.name')
    column_filters = ('status', 'payment_status', 'date')
    form_columns = ('user', 'doctor', 'service', 'date', 'time', 'status', 'payment_status', 'notes')
    form_overrides = {
        'notes': TextAreaField,
        'status': SelectField
    }
    form_args = {
        'status': {
            'choices': [
                ('pending', 'در انتظار'),
                ('confirmed', 'تایید شده'),
                ('canceled', 'لغو شده'),
                ('completed', 'انجام شده')
            ]
        },
        'payment_status': {
            'choices': [
                ('pending', 'در انتظار پرداخت'),
                ('paid', 'پرداخت شده')
            ]
        }
    }
    column_labels = {
        'id': 'شناسه',
        'user': 'کاربر',
        'doctor': 'پزشک',
        'service': 'خدمت',
        'date': 'تاریخ',
        'time': 'زمان',
        'status': 'وضعیت',
        'payment_status': 'وضعیت پرداخت',
        'notes': 'یادداشت',
        'created_at': 'تاریخ ایجاد'
    }

class ReviewModelView(AdminRequiredMixin, ModelView):
    column_list = ('id', 'user', 'service', 'rating', 'created_at', 'is_approved')
    column_filters = ('rating', 'is_approved', 'created_at')
    form_columns = ('user', 'service', 'rating', 'comment', 'is_approved')
    form_overrides = {
        'comment': TextAreaField,
    }
    column_labels = {
        'id': 'شناسه',
        'user': 'کاربر',
        'service': 'خدمت',
        'rating': 'امتیاز',
        'comment': 'نظر',
        'created_at': 'تاریخ ثبت',
        'is_approved': 'تایید شده'
    }

class PortfolioModelView(AdminRequiredMixin, ModelView):
    column_list = ('id', 'service', 'title', 'is_featured')
    form_columns = ('service', 'title', 'description', 'before_image_url', 'after_image_url', 'is_featured')
    form_overrides = {
        'description': TextAreaField,
    }
    column_labels = {
        'id': 'شناسه',
        'service': 'خدمت',
        'title': 'عنوان',
        'description': 'توضیحات',
        'before_image_url': 'تصویر قبل',
        'after_image_url': 'تصویر بعد',
        'is_featured': 'ویژه'
    }

class NewsModelView(AdminRequiredMixin, ModelView):
    column_list = ('id', 'title', 'created_at', 'is_published', 'is_ai_generated')
    column_filters = ('is_published', 'is_ai_generated', 'created_at')
    form_columns = ('title', 'content', 'image_url', 'is_published', 'is_ai_generated')
    form_overrides = {
        'content': TextAreaField,
    }
    column_labels = {
        'id': 'شناسه',
        'title': 'عنوان',
        'content': 'محتوا',
        'image_url': 'تصویر',
        'created_at': 'تاریخ انتشار',
        'is_published': 'منتشر شده',
        'is_ai_generated': 'تولید شده توسط هوش مصنوعی'
    }

# Register ModelViews
admin.add_view(UserModelView(User, db.session, name='کاربران'))
admin.add_view(DoctorModelView(Doctor, db.session, name='پزشکان'))
admin.add_view(ServiceModelView(Service, db.session, name='خدمات'))
admin.add_view(AppointmentModelView(Appointment, db.session, name='نوبت ها'))
admin.add_view(ReviewModelView(Review, db.session, name='نظرات'))
admin.add_view(PortfolioModelView(Portfolio, db.session, name='نمونه کارها'))
admin.add_view(NewsModelView(News, db.session, name='اخبار'))

# Custom admin views
@admin_bp.route('/')
@login_required
@admin_required
def index():
    # Get counts for dashboard
    total_users = User.query.count()
    total_appointments = Appointment.query.count()
    pending_appointments = Appointment.query.filter_by(status='pending').count()
    today_appointments = Appointment.query.filter_by(date=datetime.date.today()).count()
    
    # Get latest appointments
    recent_appointments = Appointment.query.order_by(Appointment.date.desc()).limit(5).all()
    
    # Format appointments for display
    formatted_appointments = []
    for appointment in recent_appointments:
        user = User.query.get(appointment.user_id)
        service = Service.query.get(appointment.service_id)
        doctor = Doctor.query.get(appointment.doctor_id)
        
        formatted_appointment = {
            'id': appointment.id,
            'user_name': user.username,
            'user_phone': user.phone,
            'service_name': service.name,
            'doctor_name': doctor.name,
            'date': format_shamsi_date(appointment.date),
            'time': appointment.time.strftime('%H:%M'),
            'status': appointment.status,
            'payment_status': appointment.payment_status
        }
        
        formatted_appointments.append(formatted_appointment)
    
    return render_template('admin/index.html', 
                           total_users=total_users,
                           total_appointments=total_appointments,
                           pending_appointments=pending_appointments,
                           today_appointments=today_appointments,
                           recent_appointments=formatted_appointments)

@admin_bp.route('/generate_news', methods=['GET', 'POST'])
@login_required
@admin_required
def generate_news():
    if request.method == 'POST':
        topic = request.form.get('topic')
        
        if not topic:
            flash('لطفا موضوع خبر را وارد کنید', 'error')
            return redirect(url_for('admin_bp.generate_news'))
        
        try:
            # Generate AI news content
            title, content = generate_beauty_news(topic)
            
            # Create news article
            news = News(
                title=title,
                content=content,
                is_published=True,
                is_ai_generated=True
            )
            
            db.session.add(news)
            db.session.commit()
            
            flash('خبر با موفقیت تولید و منتشر شد', 'success')
            return redirect(url_for('admin.newsmodeview.edit_view', id=news.id))
        
        except Exception as e:
            flash(f'خطا در تولید محتوا: {str(e)}', 'error')
    
    return render_template('admin/generate_news.html')
