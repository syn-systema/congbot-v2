import sqlite3
import logging
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_database(db_path):
    """
    Create a SQLite database with the necessary tables for storing lease drop data.
    
    Args:
        db_path (str): Path to the SQLite database file
        
    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        # Connect to the database
        conn = sqlite3.connect(db_path)
        logger.info(f"Connected to database at {db_path}")
        
        # Create tables
        cursor = conn.cursor()
        
        # Table for storing query information
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lease_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            identifier_type TEXT,
            identifier_value TEXT,
            beg_period TEXT,
            end_period TEXT,
            status TEXT,
            error_message TEXT,
            query_info TEXT
        )
        ''')
        
        # Table for storing lease data
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lease_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER,
            data_json TEXT,
            pct_change REAL,
            FOREIGN KEY (query_id) REFERENCES lease_queries (id)
        )
        ''')
        
        # Table for storing statistics
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lease_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER,
            statistics_json TEXT,
            FOREIGN KEY (query_id) REFERENCES lease_queries (id)
        )
        ''')
        
        # Commit the changes
        conn.commit()
        logger.info("Database tables created successfully")
        
        return conn
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise

def get_connection(db_path):
    """
    Get a connection to the SQLite database.
    
    Args:
        db_path (str): Path to the SQLite database file
        
    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        # Check if database exists
        if not os.path.exists(db_path):
            # Create database if it doesn't exist
            return create_database(db_path)
        else:
            # Connect to existing database
            conn = sqlite3.connect(db_path)
            logger.info(f"Connected to existing database at {db_path}")
            return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def get_all_queries(conn):
    """
    Get all queries from the database.
    
    Args:
        conn (sqlite3.Connection): Database connection object
        
    Returns:
        list: List of dictionaries containing query information
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, timestamp, identifier_type, identifier_value, beg_period, end_period, status
        FROM lease_queries
        ORDER BY timestamp DESC
        ''')
        
        rows = cursor.fetchall()
        
        # Convert rows to list of dictionaries
        queries = []
        for row in rows:
            queries.append({
                'id': row[0],
                'timestamp': row[1],
                'identifier_type': row[2],
                'identifier_value': row[3],
                'beg_period': row[4],
                'end_period': row[5],
                'status': row[6]
            })
        
        return queries
    except Exception as e:
        logger.error(f"Error getting queries: {e}")
        return []

def get_query_by_id(conn, query_id):
    """
    Get a query by its ID.
    
    Args:
        conn (sqlite3.Connection): Database connection object
        query_id (int): ID of the query
        
    Returns:
        dict: Dictionary containing query information
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, timestamp, identifier_type, identifier_value, beg_period, end_period, status, error_message, query_info
        FROM lease_queries
        WHERE id = ?
        ''', (query_id,))
        
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'timestamp': row[1],
                'identifier_type': row[2],
                'identifier_value': row[3],
                'beg_period': row[4],
                'end_period': row[5],
                'status': row[6],
                'error_message': row[7],
                'query_info': row[8]
            }
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting query by ID: {e}")
        return None

def get_lease_data_by_query_id(conn, query_id):
    """
    Get lease data by query ID.
    
    Args:
        conn (sqlite3.Connection): Database connection object
        query_id (int): ID of the query
        
    Returns:
        dict: Dictionary containing lease data
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, data_json, pct_change
        FROM lease_data
        WHERE query_id = ?
        ''', (query_id,))
        
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'data_json': row[1],
                'pct_change': row[2]
            }
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting lease data by query ID: {e}")
        return None

def get_statistics_by_query_id(conn, query_id):
    """
    Get statistics by query ID.
    
    Args:
        conn (sqlite3.Connection): Database connection object
        query_id (int): ID of the query
        
    Returns:
        dict: Dictionary containing statistics
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, statistics_json
        FROM lease_statistics
        WHERE query_id = ?
        ''', (query_id,))
        
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'statistics_json': row[1]
            }
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting statistics by query ID: {e}")
        return None
