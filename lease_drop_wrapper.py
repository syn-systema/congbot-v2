#!/usr/bin/env python3
"""
Wrapper script for lease drop functionality to be called from Ignition.
This script accepts command line arguments and returns results as JSON.

Usage:
    python lease_drop_wrapper.py <command> <arg1> <arg2> ...

Commands:
    retrieve_data - Retrieve lease drop data
        Args: identifier_type identifier_value beg_period end_period
    get_queries - Get all historical queries
        Args: none
    get_query_details - Get details of a specific query
        Args: query_id
    analyze_trend - Analyze production trend for a specific query
        Args: query_id
"""

import sys
import json
import os
import logging
from datetime import datetime

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'lease_drop_wrapper_{datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the lease drop modules
try:
    from lease_drop_core import access_lease_drop, process_lease_data, save_to_database
    from database_schema import get_connection, get_all_queries, get_query_by_id, get_lease_data_by_query_id, get_statistics_by_query_id
    logger.info("Successfully imported lease_drop_core and database_schema modules")
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    print(json.dumps({
        'status': 'error',
        'message': f"Error importing modules: {e}"
    }))
    sys.exit(1)

def retrieve_data(args):
    """
    Retrieve lease drop data.
    
    Args:
        args (list): [identifier_type, identifier_value, beg_period, end_period]
    """
    if len(args) < 4:
        return {
            'status': 'error',
            'message': 'Not enough arguments. Expected: identifier_type identifier_value beg_period end_period'
        }
    
    identifier_type = args[0]
    identifier_value = args[1]
    beg_period = args[2]
    end_period = args[3]
    
    # Set default database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lease_drop.db')
    
    try:
        # Get database connection
        conn = get_connection(db_path)
        
        # Access lease drop data
        html_content, error_message, query_info = access_lease_drop(identifier_type, identifier_value, beg_period, end_period)
        
        if error_message:
            # Save query information with error
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
            save_to_database(conn, query_info)
            
            # Return error
            return {
                'status': 'error',
                'message': process_error,
                'query_info': query_info
            }
        
        # Save data to database
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

def get_queries(args):
    """
    Get all historical queries from the database.
    
    Args:
        args (list): []
    """
    # Set default database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lease_drop.db')
    
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

def get_query_details(args):
    """
    Get details of a specific query from the database.
    
    Args:
        args (list): [query_id]
    """
    if len(args) < 1:
        return {
            'status': 'error',
            'message': 'Not enough arguments. Expected: query_id'
        }
    
    query_id = int(args[0])
    
    # Set default database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lease_drop.db')
    
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

def analyze_trend(args):
    """
    Analyze the production trend for a specific query.
    
    Args:
        args (list): [query_id]
    """
    if len(args) < 1:
        return {
            'status': 'error',
            'message': 'Not enough arguments. Expected: query_id'
        }
    
    query_id = int(args[0])
    
    # Set default database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lease_drop.db')
    
    try:
        # Get database connection
        conn = get_connection(db_path)
        
        # Get query details
        query_details = get_query_details([query_id])
        
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
        import pandas as pd
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

def main():
    """
    Main function to parse command line arguments and call the appropriate function.
    """
    if len(sys.argv) < 2:
        print(json.dumps({
            'status': 'error',
            'message': 'Not enough arguments. Expected: command [arg1 arg2 ...]'
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    try:
        if command == 'retrieve_data':
            result = retrieve_data(args)
        elif command == 'get_queries':
            result = get_queries(args)
        elif command == 'get_query_details':
            result = get_query_details(args)
        elif command == 'analyze_trend':
            result = analyze_trend(args)
        else:
            result = {
                'status': 'error',
                'message': f"Unknown command: {command}"
            }
        
        # Print the result as JSON
        print(json.dumps(result))
    except Exception as e:
        logger.error(f"Error executing command {command}: {e}")
        print(json.dumps({
            'status': 'error',
            'message': f"Error executing command {command}: {e}"
        }))
        sys.exit(1)

if __name__ == '__main__':
    main()
