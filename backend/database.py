import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:////app/data/resume_ai.db"
)

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create the database tables.

    Also performs a lightweight SQLite migration for older versions
    of the project where the candidates table may already exist
    with different columns.
    """

    Base.metadata.create_all(bind=engine)

    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)

    if "candidates" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("candidates")
    }

    required_columns = {
        "candidate_name": "VARCHAR(255)",
        "resume_filename": "VARCHAR(255)",
        "job_description": "TEXT",
        "resume_text": "TEXT",
        "analysis_json": "TEXT",
        "resume_hash": "VARCHAR(64)",
        "job_hash": "VARCHAR(64)",
    }

    with engine.begin() as connection:
        for column_name, column_type in required_columns.items():

            if column_name not in existing_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE candidates "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )