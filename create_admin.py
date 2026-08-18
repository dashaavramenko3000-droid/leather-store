from app import app, db
from models import User

with app.app_context():
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin')
        admin_user.set_password('admin123')  # смените пароль!
        db.session.add(admin_user)
        db.session.commit()
        print('Администратор создан')
        