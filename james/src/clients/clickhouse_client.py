import logging
import os
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from clickhouse_driver import Client
from clickhouse_driver.errors import UnexpectedPacketFromServerError
from datetime import datetime
from dateutil import parser as date_parser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClickHouseClient:
    """Client for interacting with ClickHouse database"""
    
    def __init__(
        self,
        url: str = None,
        user: str = None,
        password: str = None,
        database: str = "default",
        batch_size: int = 100,
        flush_interval_seconds: int = 10
    ):
        """
        Initialize ClickHouse client
        
        Args:
            url: ClickHouse server URL (format: clickhouse://host:port or http://host:port)
            user: Username for authentication
            password: Password for authentication
            database: Database name
            batch_size: Number of records to batch before inserting
            flush_interval_seconds: Maximum time to wait before flushing batched records
        """
        # Parse URL if provided, otherwise use host and port
        if url is None:
            url = os.getenv("CLICKHOUSE_URL", None)
        
        if url:
            parsed_url = urlparse(url)
            # Remove any leading '//' from netloc if present
            netloc = parsed_url.netloc.lstrip('/')
            
            # Parse host and port from URL
            if ':' in netloc:
                self.host, port_str = netloc.split(':', 1)
                self.port = int(port_str)
            else:
                self.host = netloc
                self.port = 9000  # Default ClickHouse port
            
            # Check if HTTP protocol is used
            self.is_http = parsed_url.scheme in ['http', 'https']
            if self.is_http:
                logger.info(f"Using HTTP connection to ClickHouse")
                # Note: clickhouse-driver doesn't directly support HTTP
                # We'd need to use a different client for HTTP
                logger.warning("HTTP protocol is not directly supported by clickhouse-driver, using native protocol")
            
            logger.info(f"Using native protocol for ClickHouse connection")
        else:
            logger.error("No ClickHouse URL provided")
            raise ValueError("No ClickHouse URL provided")
        
        self.user = user or os.getenv("CLICKHOUSE_USERNAME", os.getenv("CLICKHOUSE_USER", "default"))
        self.password = password or os.getenv("CLICKHOUSE_PASSWORD", os.getenv("CLICKHOUSE_PASSWORD", ""))
        self.database = database or os.getenv("CLICKHOUSE_DATABASE", "default")
        self.client = None
        
        # Batch insertion configuration
        self.batch_size = batch_size
        self.flush_interval = flush_interval_seconds
        
        # Initialize batched data caches
        self._thread_events_cache = []
        self._turn_events_cache = []
        self._citation_events_cache = []
        
        # Track last flush time
        self._last_flush_time = time.time()
        
        logger.info(f"Initializing ClickHouse client for {self.host}:{self.port}, database '{self.database}' (batch size: {batch_size})")
    
    def connect(self) -> None:
        """Establish connection to ClickHouse"""
        temp_client = None
        try:
            # First connect without specifying database
            print(f"Connecting to ClickHouse at {self.host}:{self.port}")
            temp_client = Client(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            
            # Check if database exists and create it if needed
            databases = temp_client.execute("SHOW DATABASES")
            databases = [db[0] for db in databases]
            
            if self.database not in databases:
                logger.info(f"Database '{self.database}' does not exist. Creating it.")
                temp_client.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                logger.info(f"Database '{self.database}' created successfully")
            
            # Now connect with the database
            self.client = Client(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            
            # Test connection
            self.client.execute("SELECT 1")
            logger.info("Successfully connected to ClickHouse")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {str(e)}")
            raise
        finally:
            # Clean up the temporary client
            if temp_client is not None:
                temp_client.disconnect()
                logger.debug("Temporary ClickHouse client disconnected")
    
    def get_client(self) -> Client:
        """Get or create ClickHouse client"""
        if not self.client:
            self.connect()
        return self.client
    
    def reset_client_connection(self):
        """Forces the current client connection to be closed and discarded."""
        if self.client:
            logger.info("Resetting ClickHouse client connection: attempting to disconnect old client.")
            try:
                self.client.disconnect()
            except Exception as e:
                logger.warning(f"Error during explicit client disconnect (may already be broken): {type(e).__name__}: {e}")
            finally:
                self.client = None # Crucial: ensures a new client is created next time get_client() is called
            logger.info("ClickHouse client connection has been marked for reset.")
        else:
            logger.info("No active client to reset.")
    
    def execute_query(self, query: str, params: Optional[List[Dict[str, Any]]] = None) -> List[tuple]:
        logger.info(f"Executing query: '{query}' with parameters: {params}")
        max_attempts = 2 # Initial attempt + one retry with new connection
        for attempt in range(max_attempts):
            try:
                client = self.get_client() # Get the current client (or a new one if reset)
                logger.info(f"Executing query (Attempt {attempt+1}/{max_attempts}): '{query}' with parameters: {params}")
                result = client.execute(query, params)
                logger.info(f"Query executed successfully (Attempt {attempt+1}). Rows returned: {len(result) if result is not None else 0}")
                return result
            except UnexpectedPacketFromServerError as e:
                logger.error(
                    f"UnexpectedPacketFromServerError caught (Attempt {attempt+1}). "
                    f"Error: {str(e)}. Query: '{query}'. "
                    f"Action: Resetting connection and retrying if not last attempt."
                )
                self.reset_client_connection() # This ensures get_client() makes a NEW connection next loop
                if attempt == max_attempts - 1:
                    logger.error(f"All {max_attempts} attempts failed for query: '{query}'. Re-raising.")
                    raise # Re-raise if all retries exhausted
                # If not last attempt, loop will continue and get_client will return a new one
            except Exception as e:
                logger.error(
                    f"General error executing query (Attempt {attempt+1}): {type(e).__name__}: {str(e)}. "
                    f"Query: '{query}'. Parameters: {params}"
                )
                # For any critical error, it's safer to reset the connection too
                self.reset_client_connection()
                raise # Re-raise immediately for other types of errors

    def close(self) -> None:
        """Close the client connection after flushing any remaining data"""
        try:
            # Disconnect the client
            if self.client:
                self.client.disconnect()
                self.client = None
                logger.info("ClickHouse client disconnected")
        except Exception as e:
            logger.error(f"Error closing ClickHouse client: {str(e)}")

if __name__ == "__main__":
    # Example usage
    client = ClickHouseClient(batch_size=50, flush_interval_seconds=5)
    try:
        client.connect()
        
        # Test query
        result = client.execute_query("SELECT 1")
        logger.info(f"Test query result: {result}")
    except Exception as e:
        logger.error(f"Error in example usage: {str(e)}")
    finally:
        client.close() 