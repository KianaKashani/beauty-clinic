from app import app
from extensions import db
from models import User

with app.app_context():
    users = User.query.all()
    print(f'تعداد کاربران در دیتابیس: {len(users)}')
    for user in users:
        print(f'نام کاربری: {user.username}, ایمیل: {user.email}, فعال: {user.is_active}')
