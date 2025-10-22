import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Validate DATABASE_URL exists
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Handle potential connection URL format issues
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with NullPool and SSL configuration
# Use SSL only if SSL_MODE is set to 'require' (for hosted databases)
ssl_mode = os.getenv("SSL_MODE", "prefer")
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable connection pooling to avoid SSL timeout issues
    connect_args={
        "sslmode": ssl_mode,
        "connect_timeout": 10,
        "options": "-c statement_timeout=60000"  # 60 second timeout
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session with proper error handling"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()