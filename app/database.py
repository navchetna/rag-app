"""
Database setup and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in settings.DATABASE_URL else None,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db():
    """Add any missing columns to existing tables (SQLite migration)"""
    with engine.connect() as conn:
        # Check and add in_qdrant column to ingestion_files table
        try:
            result = conn.execute(text("PRAGMA table_info(ingestion_files)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'in_qdrant' not in columns:
                conn.execute(text("ALTER TABLE ingestion_files ADD COLUMN in_qdrant BOOLEAN DEFAULT 0"))
                conn.commit()
            
            if 'output_tree_path' not in columns:
                conn.execute(text("ALTER TABLE ingestion_files ADD COLUMN output_tree_path VARCHAR(512)"))
                conn.commit()
        except Exception as e:
            # Table might not exist yet, that's fine
            pass


def init_db():
    """Initialize database tables"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)
    # Run migrations for any new columns
    migrate_db()
