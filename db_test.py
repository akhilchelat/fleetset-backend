# test_db.py

from app.db.session import engine

try:
    with engine.connect() as conn:
        print("Database connected successfully")
except Exception as e:
    print(f"Error: {e}")