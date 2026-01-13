"""
Database initialization and session management.
Provides singleton pattern for database connections and table creation.
"""
from contextlib import contextmanager
from typing import Optional, Generator
from pathlib import Path
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.database.models import Base
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages database connections and sessions using singleton pattern.
    """
    
    _instance: Optional["DatabaseManager"] = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None
    
    def __new__(cls) -> "DatabaseManager":
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(
        self,
        database_url: str,
        echo: bool = False,
        create_tables: bool = True
    ) -> None:
        """
        Initialize the database connection and create tables.
        
        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements
            create_tables: Whether to create tables if they don't exist
        """
        if self._engine is not None:
            logger.warning("Database already initialized. Skipping re-initialization.")
            return
        
        try:
            logger.info(f"Initializing database: {database_url}")
            
            # Create data directory if using SQLite
            if database_url.startswith("sqlite"):
                db_path = database_url.replace("sqlite:///", "")
                db_dir = Path(db_path).parent
                db_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created database directory: {db_dir}")
            
            # Create engine with appropriate settings
            if "sqlite" in database_url:
                # SQLite-specific settings
                self._engine = create_engine(
                    database_url,
                    echo=echo,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool
                )
            else:
                # PostgreSQL/MySQL settings
                self._engine = create_engine(
                    database_url,
                    echo=echo,
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=10
                )
            
            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )
            
            # Create tables if requested
            if create_tables:
                self.create_tables()
            
            logger.info("Database initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    def create_tables(self) -> None:
        """Create all tables defined in the models."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        try:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=self._engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}", exc_info=True)
            raise
    
    def drop_tables(self) -> None:
        """Drop all tables (use with caution!)."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        try:
            logger.warning("Dropping all database tables...")
            Base.metadata.drop_all(bind=self._engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}", exc_info=True)
            raise
    
    @classmethod
    def get_session(cls) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy Session instance
        """
        instance = cls()
        if instance._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        return instance._session_factory()
    
    @staticmethod
    @contextmanager
    def get_session_context() -> Generator[Session, None, None]:
        """
        Get a database session as a context manager.
        Automatically commits on success and rolls back on error.
        
        Yields:
            SQLAlchemy Session instance
            
        Example:
            with DatabaseManager.get_session_context() as session:
                user = session.query(User).first()
        """
        instance = DatabaseManager()
        session = instance.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error, rolling back: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """Close database connections and cleanup."""
        if self._engine is not None:
            logger.info("Closing database connections...")
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")
    
    @property
    def engine(self) -> Engine:
        """Get the database engine."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._engine


# Global database manager instance
db_manager = DatabaseManager()


def init_database(
    database_url: Optional[str] = None,
    echo: bool = False,
    create_tables: bool = True
) -> DatabaseManager:
    """
    Initialize the database with configuration from settings.
    
    Args:
        database_url: Optional database URL (uses config if not provided)
        echo: Whether to echo SQL statements
        create_tables: Whether to create tables
        
    Returns:
        Initialized DatabaseManager instance
    """
    if database_url is None:
        from src.utils.config import get_settings
        settings = get_settings()
        database_url = settings.database_url
        echo = settings.database_echo
    
    db_manager.initialize(
        database_url=database_url,
        echo=echo,
        create_tables=create_tables
    )
    
    return db_manager


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI/Streamlit to get database sessions.
    
    Yields:
        Database session
    """
    with db_manager.get_session_context() as session:
        yield session
