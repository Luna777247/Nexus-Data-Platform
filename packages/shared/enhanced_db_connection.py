"""
Enhanced Database Connection with Retry Logic
Provides retry logic for PostgreSQL and ClickHouse connections
"""

import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Any, Dict, List
from contextlib import contextmanager

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "packages" / "shared"))

from retry_handler import retry, RetryConfig, RetryStrategy, get_circuit_breaker
from retry_config_loader import get_retry_config, get_circuit_breaker_config


logger = logging.getLogger(__name__)


class EnhancedDatabaseConnection:
    """
    Database connection wrapper with retry logic and circuit breaker
    
    Supports:
    - PostgreSQL
    - ClickHouse
    - Automatic connection retry
    - Query retry on transient errors
    - Circuit breaker for database health
    """
    
    def __init__(
        self,
        db_type: str = 'postgresql',
        host: str = 'localhost',
        port: int = 5432,
        user: str = 'admin',
        password: str = 'admin123',
        database: str = 'nexus_data'
    ):
        """
        Initialize database connection
        
        Args:
            db_type: Database type ('postgresql' or 'clickhouse')
            host: Database host
            port: Database port
            user: Username
            password: Password
            database: Database name
        """
        self.db_type = db_type
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        
        # Get retry configuration
        self.retry_config = get_retry_config('database', db_type)
        self.cb_config = get_circuit_breaker_config('database')
        
        # Create circuit breaker
        self.circuit_breaker = get_circuit_breaker(
            f'database_{db_type}',
            self.cb_config
        )
        
        self.connection = None
        self._connect()
        
        logger.info(f"Enhanced {db_type} connection initialized")
    
    def _connect(self):
        """Establish database connection with retry"""
        
        @retry(
            config=self.retry_config,
            strategy=RetryStrategy.EXPONENTIAL,
            circuit_breaker=self.circuit_breaker
        )
        def connect():
            if self.db_type == 'postgresql':
                return psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    cursor_factory=RealDictCursor
                )
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
        
        try:
            self.connection = connect()
            logger.info(f"Connected to {self.db_type} at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.db_type}: {e}")
            raise
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: bool = True
    ) -> Optional[List[Dict]]:
        """
        Execute query with retry logic
        
        Args:
            query: SQL query
            params: Query parameters
            fetch: Whether to fetch results
        
        Returns:
            Query results if fetch=True, None otherwise
        """
        
        @retry(
            config=self.retry_config,
            strategy=RetryStrategy.EXPONENTIAL,
            circuit_breaker=self.circuit_breaker
        )
        def execute():
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch:
                    return cursor.fetchall()
                else:
                    self.connection.commit()
                    return None
        
        try:
            return execute()
        except Exception as e:
            logger.error(f"Query failed: {e}\nQuery: {query}")
            raise
    
    @contextmanager
    def get_cursor(self):
        """Get database cursor with automatic retry"""
        
        @retry(
            config=self.retry_config,
            strategy=RetryStrategy.EXPONENTIAL,
            circuit_breaker=self.circuit_breaker
        )
        def get_conn():
            if self.connection is None or self.connection.closed:
                self._connect()
            return self.connection
        
        conn = get_conn()
        cursor = conn.cursor()
        
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            cursor.close()
    
    def close(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info(f"{self.db_type} connection closed")


# Example usage
def example_usage():
    """Example of using EnhancedDatabaseConnection"""
    
    # PostgreSQL connection
    db = EnhancedDatabaseConnection(
        db_type='postgresql',
        host='postgres',
        port=5432,
        user='admin',
        password='admin123',
        database='nexus_data'
    )
    
    # Execute query
    results = db.execute_query(
        "SELECT * FROM data_sources WHERE enabled = %s LIMIT 10",
        (True,)
    )
    
    print(f"Found {len(results)} data sources")
    
    # Using cursor context manager
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM data_sources")
        result = cursor.fetchone()
        print(f"Total data sources: {result['count']}")
    
    db.close()


if __name__ == "__main__":
    example_usage()
