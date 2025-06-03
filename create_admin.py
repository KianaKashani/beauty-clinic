from extensions import db
from models import User, UserRole
from app import create_app

app = create_app()

with app.app_context():
    
    admin_user = User(
        username='admin',
        email='admin_new@example.com',
        phone='09120301048',
        role=UserRole.ADMIN,
        is_active=True,
    )
    admin_user.set_password('admin123')  
    db.session.add(admin_user)
    db.session.commit()
    print("ادمین جدید ساخته شد.")