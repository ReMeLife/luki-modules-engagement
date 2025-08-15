"""
Database connection and session management for LUKi Engagement Module
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from .config import get_config
from .models import Base


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.config = get_config()
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database engine and session factory"""
        # Configure engine based on database URL
        if self.config.database_url.startswith("sqlite"):
            # SQLite configuration
            self.engine = create_engine(
                self.config.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            # PostgreSQL or other database configuration
            self.engine = create_engine(
                self.config.database_url,
                pool_pre_ping=True,
                echo=False
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Create tables
        self.create_tables()
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (for testing)"""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get a database session (manual management)"""
        return self.SessionLocal()


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session"""
    with db_manager.get_session() as session:
        yield session


def get_db_session() -> Session:
    """Get database session for direct use"""
    return db_manager.get_session_sync()


def init_database():
    """Initialize database (create tables)"""
    db_manager.create_tables()


def reset_database():
    """Reset database (drop and recreate tables) - for testing"""
    db_manager.drop_tables()
    db_manager.create_tables()