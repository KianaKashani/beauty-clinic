import os
import logging
import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_admin import Admin
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "beauty_clinic_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'لطفا برای دسترسی به این صفحه وارد شوید'

# Initialize Flask-Admin
admin = Admin(app, name='مدیریت کلینیک', template_mode='bootstrap4')

# Template context processor - add variables available to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# Import and register blueprints
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import User, Doctor, Service, Appointment, Review, Portfolio, News
    
    # Create all database tables
    db.create_all()
    
    # Import and register blueprints after models are available
    from routes import main as main_blueprint
    from auth import auth as auth_blueprint
    from admin import admin_bp as admin_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(admin_blueprint)
    
    # Setup login user loader
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
