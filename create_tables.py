from app.db.session import engine
from app.models import *
from app.models.base import Base

Base.metadata.create_all(bind=engine)

print("Tables created successfully")