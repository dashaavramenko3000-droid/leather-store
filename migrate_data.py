from app import app, db
from models import Product, User
import sqlite3

# Подключение к старой SQLite
sqlite_conn = sqlite3.connect('leather_store.db')
cursor = sqlite_conn.cursor()

# Перенос товаров
cursor.execute("SELECT id, name, description, price, image, product_type FROM product")
rows = cursor.fetchall()
for row in rows:
    product = Product(
        id=row[0],
        name=row[1],
        description=row[2],
        price=row[3],
        image=row[4],
        product_type=row[5]
    )
    db.session.add(product)

# Перенос пользователей (если нужно)
cursor.execute("SELECT id, username, password_hash FROM user")
users = cursor.fetchall()
for u in users:
    user = User(id=u[0], username=u[1], password_hash=u[2])
    db.session.add(user)

db.session.commit()
sqlite_conn.close()
print("Данные перенесены")