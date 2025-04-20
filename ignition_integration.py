"""
Ignition Integration for Lease Drop - Crude Oil Inquiry

This module provides functions that can be called from Ignition Maker to:
1. Retrieve lease drop data from the Texas Comptroller's website
2. Store the data in a database
3. Retrieve stored data for display in Ignition

Usage in Ignition:
1. Place this file in your Ignition project's script directory
2. Import the functions in your Ignition scripts
3. Call the functions from your Ignition scripts

Example:
    # In an Ignition script
    import system
    
    # Get the path to this script
    script_path = system.file.getAbsolutePath('.')
    
    # Add the script directory to the Python path
    system.util.execute(['python', '-c', 'import sys; sys.path.append("' + script_path + '")'])
    
    # Import the module
    from ignition_integration import retrieve_lease_data, get_historical_queries
    
    # Retrieve lease data
    result = retrieve_lease_data('Lease Number', '12345', '2201', '2301')
    
    # Update an Ignition table component with the data
    if result['status'] == 'success':
        system.gui.updateTable('Table', result['data'])
"""

import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import the lease_drop_core and database_schema modules
try:
    from lease_drop_core import access_lease_drop, process_lease_data
    from database_schema import get_connection, get_all_queries, get_query_by_id, get_lease_data_by_query_id, get_statistics_by_query_id
    logger.info("Successfully imported lease_drop_core and database_schema modules")
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    raise

def retrieve_lease_data(identifier_type, identifier_value, beg_period, end_period, db_path=None):
    """
    Retrieve lease drop data from the Texas Comptroller's website and store it in the database.
    
    Args:
        identifier_type (str): Either "Lease Number" or "Drilling Permit Number"
        identifier_value (str): The value of the identifier
        beg_period (str): Beginning period in yymm or yy format
        end_period (str): Ending period in yymm or yy format
        db_path (str): Path to the SQLite database file. If None, uses default path.
        
    Returns:
        dict: Dictionary containing the result of the operation
    """
    # Set default database path if not provided
    if db_path is None:
        db_path = os.path.join(current_dir, 'data', 'lease_drop.db')
    
    try:
        # Get database connection
        conn = get_connection(db_path)
        
        # Access lease drop data
        html_content, error_message, query_info = access_lease_drop(identifier_type, identifier_value, beg_period, end_period)
        
        if error_message:
            # Save query information with error
            from lease_drop_core import save_to_database
            save_to_database(conn, query_info)
            
            # Return error
            return {
                'status': 'error',
                'message': error_message,
                'query_info': query_info
            }
        
        # Process lease data
        tables, production_col, date_col, stats_df, pct_change, process_error = process_lease_data(html_content)
        
        if process_error:
            # Update query information with error
            query_info['status'] = 'error'
            query_info['error_message'] = process_error
            
            # Save query information with error
            from lease_drop_core import save_to_database
            save_to_database(conn, query_info)
            
            # Return error
            return {
                'status': 'error',
                'message': process_error,
                'query_info': query_info
            }
        
        # Save data to database
        from lease_drop_core import save_to_database
        save_to_database(conn, query_info, tables, stats_df, pct_change)
        
        # Convert tables to JSON for Ignition
        data_json = []
        if tables and len(tables) > 0:
            data_json = tables[0].to_dict(orient='records')
        
        # Convert stats_df to JSON for Ignition
        stats_json = []
        if stats_df is not None:
            stats_json = stats_df.to_dict(orient='records')
        
        # Return success
        return {
            'status': 'success',
            'data': data_json,
            'stats': stats_json,
            'production_col': production_col,
            'date_col': date_col,
            'pct_change': pct_change,
            'query_info': query_info
        }
    except Exception as e:
        logger.error(f"Error retrieving lease data: {e}")
        return {
            'status': 'error',
            'message': f"Error retrieving lease data: {e}"
        }
    finally:
        # Close database connection
        if 'conn' in locals() and conn:
            conn.close()

def get_historical_queries(db_path=None):
    """
    Get all historical queries from the database.
    
    Args:
        db_path (str): Path to the SQLite database file. If None, uses default path.
        
    Returns:
        dict: Dictionary containing the result of the operation
    """
    # Set default database path if not provided
    if db_path is None:
        db_path = os.path.join(current_dir, 'data', 'lease_drop.db')
    
    try:
        # Get database connection
        conn = get_connection(db_path)
        
        # Get all queries
        queries = get_all_queries(conn)
        
        # Return success
        return {
            'status': 'success',
            'queries': queries
        }
    except Exception as e:
        logger.error(f"Error getting historical queries: {e}")
        return {
            'status': 'error',
            'message': f"Error getting historical queries: {e}"
        }
    finally:
        # Close database connection
        if 'conn' in locals() and conn:
            conn.close()

def get_query_details(query_id, db_path=None):
    """
    Get details of a specific query from the database.
    
    Args:
        query_id (int): ID of the query
        db_path (str): Path to the SQLite database file. If None, uses default path.
        
    Returns:
        dict: Dictionary containing the result of the operation
    """
    # Set default database path if not provided
    if db_path is None:
        db_path = os.path.join(current_dir, 'data', 'lease_drop.db')
    
    try:
        # Get database connection
        conn = get_connection(db_path)
        
        # Get query details
        query = get_query_by_id(conn, query_id)
        
        if query:
            # Get lease data
            lease_data = get_lease_data_by_query_id(conn, query_id)
            
            # Get statistics
            statistics = get_statistics_by_query_id(conn, query_id)
            
            # Parse JSON data
            data_json = []
            if lease_data and lease_data.get('data_json'):
                data_json = json.loads(lease_data.get('data_json'))
            
            # Parse statistics JSON
            stats_json = []
            if statistics and statistics.get('statistics_json'):
                stats_json = json.loads(statistics.get('statistics_json'))
            
            # Return success
            return {
                'status': 'success',
                'query': query,
                'data': data_json,
                'stats': stats_json,
                'pct_change': lease_data.get('pct_change') if lease_data else None
            }
        else:
            # Return error
            return {
                'status': 'error',
                'message': f"Query with ID {query_id} not found"
            }
    except Exception as e:
        logger.error(f"Error getting query details: {e}")
        return {
            'status': 'error',
            'message': f"Error getting query details: {e}"
        }
    finally:
        # Close database connection
        if 'conn' in locals() and conn:
            conn.close()

def analyze_production_trend(query_id, db_path=None):
    """
    Analyze the production trend for a specific query.
    
    Args:
        query_id (int): ID of the query
        db_path (str): Path to the SQLite database file. If None, uses default path.
        
    Returns:
        dict: Dictionary containing the result of the operation
    """
    # Set default database path if not provided
    if db_path is None:
        db_path = os.path.join(current_dir, 'data', 'lease_drop.db')
    
    try:
        # Get database connection
        conn = get_connection(db_path)
        
        # Get query details
        query_details = get_query_details(query_id, db_path)
        
        if query_details['status'] == 'error':
            return query_details
        
        # Get data
        data = query_details['data']
        
        if not data:
            return {
                'status': 'error',
                'message': f"No data found for query with ID {query_id}"
            }
        
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        # Try to find production column
        production_col = None
        for col in df.columns:
            if "CRUDE" in str(col).upper() and "OIL" in str(col).upper():
                production_col = col
                break
        
        if not production_col:
            return {
                'status': 'error',
                'message': f"Could not identify crude oil production column for analysis"
            }
        
        # Convert to numeric, coercing errors to NaN
        df[production_col] = pd.to_numeric(df[production_col], errors='coerce')
        
        # Try to find date column
        date_col = None
        for col in df.columns:
            if "DATE" in str(col).upper() or "PERIOD" in str(col).upper():
                date_col = col
                break
        
        if not date_col:
            return {
                'status': 'error',
                'message': f"Could not identify date column for analysis"
            }
        
        # Sort by date
        df = df.sort_values(by=date_col)
        
        # Calculate monthly changes
        df['previous_production'] = df[production_col].shift(1)
        df['monthly_change'] = df[production_col] - df['previous_production']
        df['monthly_pct_change'] = (df['monthly_change'] / df['previous_production']) * 100
        
        # Calculate cumulative change
        first_production = df[production_col].iloc[0]
        df['cumulative_change'] = df[production_col] - first_production
        df['cumulative_pct_change'] = (df['cumulative_change'] / first_production) * 100
        
        # Calculate moving averages
        df['3_month_avg'] = df[production_col].rolling(window=3).mean()
        df['6_month_avg'] = df[production_col].rolling(window=6).mean()
        
        # Calculate overall trend
        from scipy import stats
        if len(df) >= 2:
            x = range(len(df))
            y = df[production_col].values
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            trend_direction = "increasing" if slope > 0 else "decreasing"
            trend_strength = abs(r_value)
        else:
            slope = 0
            r_value = 0
            trend_direction = "unknown"
            trend_strength = 0
        
        # Prepare result
        result = {
            'status': 'success',
            'data': df.to_dict(orient='records'),
            'production_col': production_col,
            'date_col': date_col,
            'trend': {
                'direction': trend_direction,
                'strength': trend_strength,
                'slope': slope,
                'r_value': r_value
            }
        }
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing production trend: {e}")
        return {
            'status': 'error',
            'message': f"Error analyzing production trend: {e}"
        }
    finally:
        # Close database connection
        if 'conn' in locals() and conn:
            conn.close()

# Example Ignition script functions that can be called directly from Ignition

def ignition_retrieve_lease_data(identifier_type, identifier_value, beg_period, end_period):
    """
    Function to be called directly from Ignition to retrieve lease data.
    
    Args:
        identifier_type (str): Either "Lease Number" or "Drilling Permit Number"
        identifier_value (str): The value of the identifier
        beg_period (str): Beginning period in yymm or yy format
        end_period (str): Ending period in yymm or yy format
        
    Returns:
        dict: Dictionary containing the result of the operation
    """
    # This function can be called directly from Ignition
    return retrieve_lease_data(identifier_type, identifier_value, beg_period, end_period)

def ignition_get_historical_queries():
    """
    Function to be called directly from Ignition to get all historical queries.
    
    Returns:
        dict: Dictionary containing the result of the operation
    """
    # This function can be called directly from Ignition
    return get_historical_queries()

def ignition_get_query_details(query_id):
    """
    Function to be called directly from Ignition to get details of a specific query.
    
    Args:
        query_id (int): ID of the query
        
    Returns:
        dict: Dictionary containing the result of the operation
    """
    # This function can be called directly from Ignition
    return get_query_details(query_id)

def ignition_analyze_production_trend(query_id):
    """
    Function to be called directly from Ignition to analyze the production trend for a specific query.
    
    Args:
        query_id (int): ID of the query
        
    Returns:
        dict: Dictionary containing the result of the operation
    """
    # This function can be called directly from Ignition
    return analyze_production_trend(query_id)
