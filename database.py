import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default to SQLite for local development/testing if DB env vars not present,
# otherwise use MariaDB/MySQL.
db_host = os.environ.get("DB_HOST", "localhost")
db_port = os.environ.get("DB_PORT", "3306")
db_name = os.environ.get("DB_NAME", "ebilling_scrape")
db_user = os.environ.get("DB_USER", "root")
db_pass = os.environ.get("DB_PASS", "")

if db_user and db_pass:
    DATABASE_URL = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
else:
    # Fallback to local sqlite for testing without running a DB server
    DATABASE_URL = "sqlite:///./ebilling_scrape.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
