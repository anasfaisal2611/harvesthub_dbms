# database/database.py
# Database connection for raw SQL DML operations (DDL tables pre-created in PgAdmin)

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)
DB_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DB_DIR.parent

# ============ DATABASE CONFIGURATION ============

# Get credentials from environment variables
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "cropdb")

# Build connection URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.info(f"Connecting to PostgreSQL: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


# --- DEBUGGING SECTION ---
print("--- DEBUG START ---")
print(f"Looking for DB_PASSWORD in environment...")
pwd = os.getenv("DB_PASSWORD")
print(f"Found password in env: '{pwd}'") 
print(f"DATABASE_URL being built: postgresql://{DB_USER}:{pwd}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
print("--- DEBUG END ---")
# -------------------------





# ============ CREATE ENGINE ============

engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True to see SQL queries in terminal (for debugging)
    pool_size=10,  # Number of connections to keep in pool
    max_overflow=20,  # Additional connections when pool is exhausted
    pool_pre_ping=True,  # Test connection before using (prevents timeout errors)
    pool_recycle=3600,  # Recycle connections after 1 hour (prevents stale connections)
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
        "application_name": "crop_dbms_api"
    }
)

# ============ CREATE SESSION FACTORY ============

SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-commit, use db.commit()
    autoflush=False,   # Don't auto-flush, use db.flush()
    bind=engine        # Bind to our engine
)

# ============ NO TABLE CREATION ============
# Important: Do NOT create tables here!
# All tables are created via DDL statements in PgAdmin
# Using: ddl.sql file
# Tables are already in the database

# ============ CONNECTION VERIFICATION ============

def verify_tables():
    """Verify that all 10 required tables exist in database"""
    required_tables = [
        'users',
        'regions',
        'fields',
        'satellites',
        'crop_cycles',
        'observations',
        'band_values',
        'weather_records',
        'derived_metrics',
        'alerts'
    ]
    
    db = SessionLocal()
    try:
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        result = db.execute(query)
        existing_tables = [row[0] for row in result.fetchall()]
        
        missing = [t for t in required_tables if t not in existing_tables]
        
        if missing:
            logger.error(f"Missing tables: {', '.join(missing)}")
            logger.error("Please run ddl.sql in PgAdmin to create tables")
            return False
        else:
            logger.info(f" All 10 tables verified in database")
            return True
    except Exception as e:
        logger.error(f" Error verifying tables: {e}")
        return False
    finally:
        db.close()

def test_connection():
    """Test database connection and basic functionality"""
    db = SessionLocal()
    try:
        # Simple test query
        query = text("SELECT 1")
        result = db.execute(query)
        result.fetchone()
        logger.info(" Database connection successful!")
        
        # Verify tables exist
        tables_ok = verify_tables()
        
        return tables_ok
    except Exception as e:
        logger.error(f" Database connection failed: {e}")
        logger.error(f"Connection string: {DATABASE_URL}")
        return False
    finally:
        db.close()

def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def apply_startup_migrations():
    """Apply safe additive migrations needed by the current app version."""
    migration_files = [
        DB_DIR / "001_add_user_avatar.sql",
    ]

    with engine.begin() as conn:
        for migration_path in migration_files:
            if not migration_path.exists():
                logger.warning(f"Migration file not found: {migration_path.name}")
                continue
            sql = migration_path.read_text(encoding="utf-8").strip()
            if not sql:
                continue
            conn.execute(text(sql))
            logger.info(f"Applied startup migration: {migration_path.name}")

# ============ INITIALIZATION ============

if __name__ == "__main__":
    # Test connection when run directly
    print("\n" + "="*50)
    print("DATABASE CONNECTION TEST")
    print("="*50)
    success = test_connection()
    if success:
        print("\nDatabase is ready for use!")
    else:
        print("\n Database connection failed!")
        print("\nTroubleshooting steps:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check .env file for correct credentials")
        print("3. Run ddl.sql in PgAdmin to create tables")
        print("4. Run seed_data.sql to populate initial data")
    print("="*50 + "\n")