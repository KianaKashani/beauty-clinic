from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# User role enum (Admin, Doctor, Patient)
class UserRole:
    ADMIN = 'admin'
    DOCTOR = 'doctor'
    PATIENT = 'patient'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default=UserRole.PATIENT)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='user', lazy='dynamic')
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_doctor(self):
        return self.role == UserRole.DOCTOR

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)  # تخصص
    bio = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    experience_years = db.Column(db.Integer)
    education = db.Column(db.Text)
    certifications = db.Column(db.Text)
    
    # Relationships
    services = db.relationship('Service', secondary='doctor_service', backref='doctors')
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic')

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    short_description = db.Column(db.String(255))
    price = db.Column(db.Integer)
    duration = db.Column(db.Integer)  # in minutes
    image_url = db.Column(db.String(255))
    
    # Relationships
    appointments = db.relationship('Appointment', backref='service', lazy='dynamic')
    portfolio_items = db.relationship('Portfolio', backref='service', lazy='dynamic')

# Doctor-Service association table
doctor_service = db.Table('doctor_service',
    db.Column('doctor_id', db.Integer, db.ForeignKey('doctor.id'), primary_key=True),
    db.Column('service_id', db.Integer, db.ForeignKey('service.id'), primary_key=True)
)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, canceled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid
    payment_id = db.Column(db.String(100))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    
    # Relationship with Service is optional (general review vs service-specific)
    service = db.relationship('Service')

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    before_image_url = db.Column(db.String(255))
    after_image_url = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)
    is_ai_generated = db.Column(db.Boolean, default=False)
