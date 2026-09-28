import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.config import settings

logger = logging.getLogger("edugenie.database")

Base = declarative_base()

def init_engine():
    """
    Initialize SQLAlchemy database engine.
    Tries MySQL connection first. If unreachable and fallback is enabled,
    seamlessly falls back to local SQLite so learners can test immediately.
    """
    db_url = settings.DATABASE_URL
    is_sqlite = False
    
    try:
        if db_url.startswith("sqlite"):
            engine = create_engine(
                db_url, 
                connect_args={"check_same_thread": False}
            )
            is_sqlite = True
        else:
            # Try MySQL connection with short timeout to detect availability
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": 3}
            )
            # Test connectivity
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Successfully connected to MySQL database: %s", db_url.split("@")[-1])
            return engine, False
            
    except Exception as e:
        if settings.ALLOW_SQLITE_FALLBACK:
            logger.warning(
                "Could not connect to MySQL (%s). Falling back to SQLite database at %s. "
                "To use MySQL, make sure MySQL is running and execute database/schema.sql.",
                str(e),
                settings.SQLITE_URL
            )
            engine = create_engine(
                settings.SQLITE_URL,
                connect_args={"check_same_thread": False}
            )
            is_sqlite = True
        else:
            logger.error("MySQL connection failed and SQLite fallback is disabled: %s", str(e))
            raise e

    return engine, is_sqlite


engine, is_sqlite_mode = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI Dependency for database session management."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables automatically on app startup."""
    from backend import models  # Ensure models are imported
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully (SQLite fallback: %s)", is_sqlite_mode)
