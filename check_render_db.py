
from sqlalchemy import text
from app.db.session import engine

try:
    with engine.connect() as connection:
        database = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        tables = connection.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        ).scalars().all()

        print("Database connection: SUCCESS")
        print("Connected database:", database)
        print("Tables found:", len(tables))

        for table in tables:
            print("-", table)

except Exception as error:
    print("Database connection: FAILED")
    print("Error type:", type(error).__name__)
    print("Error:", str(error).splitlines()[0])
finally:
    engine.dispose()