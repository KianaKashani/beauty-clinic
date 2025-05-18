from app import create_app
from extensions import db
from models import Doctor, Service

app = create_app()

with app.app_context():
    all_services = Service.query.all()
    all_doctors = Doctor.query.all()

    for doctor in all_doctors:
        doctor.services = all_services

    db.session.commit()
    print("ارتباط پزشکان با خدمات انجام شد.")