from flask import Flask
from flask_login import LoginManager
from extensions import db, admin
from routes import main  
from models import User  
from auth import auth as auth_blueprint
from datetime import datetime
from admin import admin_bp
from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'  # حتماً یه کلید قوی بساز
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///beauty_clinic.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    # اتصال اکستنشن‌ها
    db.init_app(app)
    admin.init_app(app)

    # راه‌اندازی login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # اگر auth نداری می‌تونی برداری یا اصلاح کنی
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # رجیستر کردن blueprintها
    app.register_blueprint(main)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(admin_bp)

    # ایجاد جداول در اولین بار
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)