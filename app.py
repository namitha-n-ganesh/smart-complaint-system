from flask import Flask, redirect, url_for
from flask_login import LoginManager
from models import db, User
from routes.auth import auth
from routes.complaints import complaints
from routes.admin import admin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'scms-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth)
app.register_blueprint(complaints)
app.register_blueprint(admin)

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Add missing columns if they don't exist (safe migration)
        from sqlalchemy import text
        with db.engine.connect() as conn:
            try:
                conn.execute(text('ALTER TABLE complaint ADD COLUMN assigned_to VARCHAR(50) DEFAULT "Unassigned"'))
                conn.commit()
            except Exception:
                pass  # Column already exists
        # Create default admin if not exists
        from werkzeug.security import generate_password_hash
        if not User.query.filter_by(email='admin@scms.com').first():
            admin_user = User(
                name='Admin',
                email='admin@scms.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created: admin@scms.com / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
