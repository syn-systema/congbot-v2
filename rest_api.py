#!/usr/bin/env python3
"""
REST API server for the Lease Drop - Crude Oil Inquiry application.
This server exposes the lease drop functionality via a REST API that can be called from Ignition.

Usage:
    python rest_api.py

The server will start on port 5000 by default.
"""

import os
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'rest_api_{datetime.now().strftime("%Y%m%d")}.log')
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
    raise

# Create the Flask app
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    """
    return jsonify({'status': 'healthy'})

@app.route('/api/retrieve_data', methods=['POST'])
def retrieve_data():
    """
    Retrieve lease drop data from the Texas Comptroller's website.
    
    Request JSON format:
    {
        "identifier_type": "Lease Number" or "Drilling Permit Number",
        "identifier_value": "123456",
        "beg_period": "2201",
        "end_period": "2301"
    }
    
    Returns:
        JSON: Lease drop data and analysis
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['identifier_type', 'identifier_value', 'beg_period', 'end_period']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Extract fields
        identifier_type = data['identifier_type']
        identifier_value = data['identifier_value']
        beg_period = data['beg_period']
        end_period = data['end_period']
        
        # Validate identifier type
        if identifier_type not in ['Lease Number', 'Drilling Permit Number']:
            return jsonify({
                'status': 'error',
                'message': 'Invalid identifier_type. Must be "Lease Number" or "Drilling Permit Number"'
            }), 400
        
        # Create query info dictionary for database storage and response
        query_info = {
            "timestamp": datetime.now().isoformat(),
            "identifier_type": identifier_type,
            "identifier_value": identifier_value,
            "beg_period": beg_period,
            "end_period": end_period,
            "status": "started"
        }
        
        # Set default database path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lease_drop.db')
        
        # Get database connection
        conn = get_connection(db_path)
        
        # Access the Texas Comptroller's website
        html_content, error_message = access_lease_drop(identifier_type, identifier_value, beg_period, end_period)
        
        if error_message:
            # Update query info with error
            query_info["status"] = "error"
            query_info["error_message"] = error_message
            
            # Save to database
            save_to_database(conn, query_info)
            
            return jsonify({
                'status': 'error',
                'message': error_message,
                'query_info': query_info
            }), 400
        
        # Process the HTML content
        tables, production_col, date_col, stats_df, pct_change, process_error = process_lease_data(html_content)
        
        if process_error:
            # Update query info with error
            query_info["status"] = "error"
            query_info["error_message"] = process_error
            
            # Save to database
            save_to_database(conn, query_info)
            
            return jsonify({
                'status': 'error',
                'message': process_error,
                'query_info': query_info
            }), 400
        
        # Update query info with success
        query_info["status"] = "success"
        
        # Convert tables to JSON
        tables_json = []
        for table in tables:
            tables_json.append(table.to_dict(orient='records'))
        
        # Convert stats_df to JSON
        stats_json = None
        if stats_df is not None:
            stats_json = stats_df.to_dict(orient='records')
        
        # Save to database
        save_to_database(conn, query_info, tables, stats_df, pct_change)
        
        # Create response
        response = {
            'status': 'success',
            'query_info': query_info,
            'tables': tables_json,
            'production_column': production_col,
            'date_column': date_col,
            'statistics': stats_json,
            'percentage_change': pct_change
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error in retrieve_lease_data: {e}")
        logger.error(traceback.format_exc())
        
        # Create error response
        error_response = {
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }
        
        return jsonify(error_response), 500
    finally:
        # Close database connection
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/api/get_queries', methods=['GET'])
def get_queries():
    """
    Get all historical queries from the database.
    """
    try:
        # Set default database path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lease_drop.db')
        
        # Get database connection
        conn = get_connection(db_path)
        
        # Get all queries
        queries = get_all_queries(conn)
        
        # Return success
        return jsonify({
            'status': 'success',
            'queries': queries
        })
    except Exception as e:
        logger.error(f"Error getting historical queries: {e}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting historical queries: {e}"
        }), 500
    finally:
        # Close database connection
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/api/get_query_details/<int:query_id>', methods=['GET'])
def get_query_details(query_id):
    """
    Get details of a specific query from the database.
    """
    try:
        # Set default database path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lease_drop.db')
        
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
            return jsonify({
                'status': 'success',
                'query': query,
                'data': data_json,
                'stats': stats_json,
                'pct_change': lease_data.get('pct_change') if lease_data else None
            })
        else:
            # Return error
            return jsonify({
                'status': 'error',
                'message': f"Query with ID {query_id} not found"
            }), 404
    except Exception as e:
        logger.error(f"Error getting query details: {e}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting query details: {e}"
        }), 500
    finally:
        # Close database connection
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/api/analyze_trend/<int:query_id>', methods=['GET'])
def analyze_trend(query_id):
    """
    Analyze the production trend for a specific query.
    """
    try:
        # Set default database path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'lease_drop.db')
        
        # Get database connection
        conn = get_connection(db_path)
        
        # Get query details
        query = get_query_by_id(conn, query_id)
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': f"Query with ID {query_id} not found"
            }), 404
        
        # Get lease data
        lease_data = get_lease_data_by_query_id(conn, query_id)
        
        if not lease_data or not lease_data.get('data_json'):
            return jsonify({
                'status': 'error',
                'message': f"No data found for query with ID {query_id}"
            }), 404
        
        # Parse JSON data
        data = json.loads(lease_data.get('data_json'))
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': f"No data found for query with ID {query_id}"
            }), 404
        
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
            return jsonify({
                'status': 'error',
                'message': f"Could not identify crude oil production column for analysis"
            }), 400
        
        # Convert to numeric, coercing errors to NaN
        df[production_col] = pd.to_numeric(df[production_col], errors='coerce')
        
        # Try to find date column
        date_col = None
        for col in df.columns:
            if "DATE" in str(col).upper() or "PERIOD" in str(col).upper():
                date_col = col
                break
        
        if not date_col:
            return jsonify({
                'status': 'error',
                'message': f"Could not identify date column for analysis"
            }), 400
        
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
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error analyzing production trend: {e}")
        return jsonify({
            'status': 'error',
            'message': f"Error analyzing production trend: {e}"
        }), 500
    finally:
        # Close database connection
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port)
