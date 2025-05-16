from app import app, db  # noqa: F401
from models import User, Doctor, Service, UserRole
import os
from werkzeug.security import generate_password_hash

# Create initial data when the app starts
def create_sample_data():
    # Check if there are any services or doctors in the database
    if Service.query.count() == 0 and Doctor.query.count() == 0:
        print("Creating sample data...")
        
        # Create services
        services = [
            {
                'name': 'بوتاکس صورت',
                'description': 'تزریق بوتاکس برای کاهش چین و چروک صورت و حالت دادن به ابروها.',
                'short_description': 'رفع چین و چروک صورت با بوتاکس',
                'price': 1800000,
                'duration': 30,
                'image_url': '/static/img/services/botox.jpg'
            },
            {
                'name': 'فیلر لب',
                'description': 'تزریق فیلر برای حجیم کردن و فرم دادن به لب ها.',
                'short_description': 'حجیم سازی و فرم دهی به لب ها',
                'price': 2500000,
                'duration': 45,
                'image_url': '/static/img/services/lip_filler.jpg'
            },
            {
                'name': 'لیزر موهای زائد',
                'description': 'از بین بردن موهای زائد با استفاده از تکنولوژی لیزر پیشرفته.',
                'short_description': 'حذف دائمی موهای زائد با لیزر',
                'price': 1200000,
                'duration': 60,
                'image_url': '/static/img/services/laser.jpg'
            },
            {
                'name': 'پاکسازی پوست',
                'description': 'پاکسازی عمیق پوست برای از بین بردن آلودگی‌ها، جوش‌ها و منافذ باز.',
                'short_description': 'پاکسازی عمیق و رفع جوش‌های سطحی',
                'price': 900000,
                'duration': 90,
                'image_url': '/static/img/services/facial.jpg'
            },
            {
                'name': 'میکرونیدلینگ',
                'description': 'بهبود بافت پوست و کاهش اسکارها با استفاده از سوزن‌های ریز.',
                'short_description': 'بهبود بافت پوست و رفع اسکار',
                'price': 1500000,
                'duration': 60,
                'image_url': '/static/img/services/microneedling.jpg'
            }
        ]

        # Create doctors
        doctors = [
            {
                'name': 'دکتر سارا محمدی',
                'title': 'متخصص پوست و زیبایی',
                'bio': 'دکتر محمدی با بیش از 10 سال تجربه در زمینه پوست و زیبایی، فارغ‌التحصیل دانشگاه تهران می‌باشد.',
                'image_url': '/static/img/doctors/doctor1.jpg',
                'experience_years': 10,
                'education': 'دکترای تخصصی پوست - دانشگاه تهران\nفلوشیپ زیبایی - دانشگاه هاروارد',
                'certifications': 'عضو انجمن متخصصین پوست ایران\nدارای بورد تخصصی پوست'
            },
            {
                'name': 'دکتر علی کریمی',
                'title': 'متخصص جراحی پلاستیک',
                'bio': 'دکتر کریمی متخصص جراحی پلاستیک و ترمیمی با تجربه در انواع جراحی‌های زیبایی صورت و بدن است.',
                'image_url': '/static/img/doctors/doctor2.jpg',
                'experience_years': 15,
                'education': 'دکترای تخصصی جراحی پلاستیک - دانشگاه شهید بهشتی\nفلوشیپ جراحی زیبایی صورت - آلمان',
                'certifications': 'عضو انجمن جراحان پلاستیک ایران\nعضو انجمن جراحان پلاستیک آمریکا'
            },
            {
                'name': 'دکتر مریم احمدی',
                'title': 'متخصص پوست و مو',
                'bio': 'دکتر احمدی متخصص در درمان مشکلات پوست و مو با استفاده از روش‌های نوین و پیشرفته است.',
                'image_url': '/static/img/doctors/doctor3.jpg',
                'experience_years': 8,
                'education': 'دکترای تخصصی پوست - دانشگاه شیراز\nدوره تخصصی درمان ریزش مو - فرانسه',
                'certifications': 'عضو انجمن متخصصین پوست ایران\nدارای مدرک معتبر از مرکز تحقیقات پوست و مو اروپا'
            }
        ]

        # Add services to database
        service_objects = []
        for service_data in services:
            service = Service(**service_data)
            db.session.add(service)
            service_objects.append(service)
        
        # Commit to get IDs
        db.session.commit()
        
        # Add doctors to database
        doctor_objects = []
        for doctor_data in doctors:
            doctor = Doctor(**doctor_data)
            db.session.add(doctor)
            doctor_objects.append(doctor)
        
        # Commit to get IDs
        db.session.commit()
        
        # Assign services to doctors (each doctor can do certain services)
        doctor_objects[0].services.extend([service_objects[0], service_objects[1], service_objects[4]])  # Dr. Mohammadi: Botox, Lip Filler, Microneedling
        doctor_objects[1].services.extend([service_objects[0], service_objects[1]])  # Dr. Karimi: Botox, Lip Filler
        doctor_objects[2].services.extend([service_objects[2], service_objects[3], service_objects[4]])  # Dr. Ahmadi: Laser, Facial, Microneedling
        
        # Create admin user if not exists
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@beautyclinic.com')
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                username='مدیر سیستم',
                email=admin_email,
                role=UserRole.ADMIN,
                is_active=True
            )
            admin.set_password('admin12345')  # Use set_password method instead of direct assignment
            db.session.add(admin)
            
        # Create a test user for easier testing
        test_email = 'test@example.com'
        if not User.query.filter_by(email=test_email).first():
            test_user = User(
                username='کاربر تست',
                email=test_email,
                phone='09123456789',
                role=UserRole.PATIENT,
                is_active=True
            )
            test_user.set_password('password123')  # Simple password for testing
            db.session.add(test_user)
        
        # Commit all changes
        db.session.commit()
        print("Sample data created successfully!")

# Call the function with app context
with app.app_context():
    create_sample_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
