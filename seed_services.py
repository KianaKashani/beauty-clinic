from extensions import db
from models import Service, Doctor
from app import create_app

app = create_app()

with app.app_context():
    # ایجاد خدمات
    services_data = [
        {"name": "پاکسازی پوست ویژه", "price": 450000, "description": "پاکسازی عمیق پوست صورت", "duration": 45},
        {"name": "لیزر موهای زائد", "price": 700000, "description": "لیزر کل بدن", "duration": 60},
        {"name": "بوتاکس و فیلر", "price": 600000, "description": "تزریق بوتاکس و فیلر", "duration": 45},
        {"name": "مزوتراپی", "price": 800000, "description": "مزوتراپی مو و صورت", "duration": 45},
    ]

    services = []
    for s in services_data:
        existing = Service.query.filter_by(name=s["name"]).first()
        if not existing:
            new_service = Service(**s)
            db.session.add(new_service)
            services.append(new_service)
        else:
            services.append(existing)

    db.session.commit()

    # ایجاد پزشک‌ها
    doctor1 = Doctor(name='احمد احمدی', title='متخصص پوست')
    doctor2 = Doctor(name='سارا رضایی', title='متخصص لیزر')
    doctor3 = Doctor(name='مریم میری', title='دکتر زیبایی')

    db.session.add_all([doctor1, doctor2, doctor3])
    db.session.commit()

    # اتصال پزشک‌ها به خدمات
    all_services = Service.query.all()
    doctor1.services = all_services
    doctor2.services = all_services
    doctor3.services = all_services

    db.session.commit()
    print("پزشک‌ها و خدمات با موفقیت اضافه و متصل شدند.")