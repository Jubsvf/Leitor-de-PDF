import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(override=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:admin@127.0.0.1:5433/fintrack_db"
)

def _make_engine(url):
    is_postgres = url.startswith("postgresql") or url.startswith("postgres://")
    kwargs = {"echo": False, "pool_pre_ping": True}
    if is_postgres:
        kwargs["connect_args"] = {"connect_timeout": 5}
    return create_engine(url, **kwargs)

try:
    engine = _make_engine(DATABASE_URL)
    # Test the connection; if it fails, fallback will be used
    with engine.connect() as _:
        pass
except Exception:
    # Fallback to SQLite local file if PostgreSQL is unavailable
    fallback_url = "sqlite:///fintrack.db"
    engine = create_engine(fallback_url, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
