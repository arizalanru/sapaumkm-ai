from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import settings


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine_options = {"connect_args": connect_args}
if settings.database_url in {"sqlite://", "sqlite:///:memory:"}:
    engine_options["poolclass"] = StaticPool
engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
