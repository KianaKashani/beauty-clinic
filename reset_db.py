from extensions import db
from models import User, UserRole

with app.app_context():
    # Reset tables
    db.drop_all()
    db.create_all()
    
    # Create admin user
    admin = User(
        username='مدیر سیستم',
        email='admin@beautyclinic.com',
        role=UserRole.ADMIN,
        is_active=True
    )
    admin.set_password('admin12345')
    db.session.add(admin)
    
    # Create test user
    test_user = User(
        username='کاربر تست',
        email='test@example.com',
        phone='09123456789',
        role=UserRole.PATIENT,
        is_active=True
    )
    test_user.set_password('password123')
    db.session.add(test_user)
    
    # Commit changes
    db.session.commit()
    
    # Verify
    users = User.query.all()
    print(f'تعداد کاربران جدید در دیتابیس: {len(users)}')
    for user in users:
        print(f'نام کاربری: {user.username}, ایمیل: {user.email}, نقش: {user.role}, فعال: {user.is_active}')
