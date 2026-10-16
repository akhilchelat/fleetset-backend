
import app.models  # Register the SQLAlchemy models
from sqlalchemy import text

from app.db.session import engine
from app.models.base import Base


def initialize_database():
    print("Models registered:")
    for table_name in sorted(Base.metadata.tables):
        print(f" - {table_name}")

    print("\nCreating any missing database tables...")
    Base.metadata.create_all(bind=engine)

    with engine.connect() as connection:
        tables = connection.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        ).scalars().all()

    print(f"\nDatabase initialized. Tables found: {len(tables)}")
    for table_name in tables:
        print(f" - {table_name}")

    engine.dispose()


if __name__ == "__main__":
    initialize_database()