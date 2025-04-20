"""
Ignition script to call the lease drop wrapper script.
This script should be added to your Ignition project as a Script Module.

Usage:
1. Create a new Script Module in Ignition Designer
2. Copy this code into the Script Module
3. Call these functions from your Ignition components
"""

import system
import subprocess
import json

# Path to the Python 3 interpreter
PYTHON_PATH = "/usr/bin/python3"  # Update this to match your Python 3 installation

# Path to the wrapper script
WRAPPER_SCRIPT = "/home/farseer/ignition_scripts/lease_drop_wrapper.py"  # Update this path

def call_wrapper(command, *args):
    """
    Call the wrapper script with the given command and arguments.
    
    Args:
        command (str): The command to execute
        *args: Additional arguments to pass to the command
        
    Returns:
        dict: The result of the command
    """
    try:
        # Build the command
        cmd = [PYTHON_PATH, WRAPPER_SCRIPT, command]
        for arg in args:
            cmd.append(str(arg))
        
        # Call the wrapper script
        result = subprocess.check_output(cmd)
        
        # Parse the JSON result
        return system.util.jsonDecode(result)
    except Exception as e:
        # Handle any errors
        system.util.getLogger("LeaseDropIntegration").error(f"Error calling wrapper script: {e}")
        return {
            'status': 'error',
            'message': f"Error calling wrapper script: {e}"
        }

def retrieve_lease_data(identifier_type, identifier_value, beg_period, end_period):
    """
    Retrieve lease drop data.
    
    Args:
        identifier_type (str): Either "Lease Number" or "Drilling Permit Number"
        identifier_value (str): The value of the identifier
        beg_period (str): Beginning period in yymm or yy format
        end_period (str): Ending period in yymm or yy format
        
    Returns:
        dict: The result of the operation
    """
    return call_wrapper("retrieve_data", identifier_type, identifier_value, beg_period, end_period)

def get_historical_queries():
    """
    Get all historical queries.
    
    Returns:
        dict: The result of the operation
    """
    return call_wrapper("get_queries")

def get_query_details(query_id):
    """
    Get details of a specific query.
    
    Args:
        query_id (int): ID of the query
        
    Returns:
        dict: The result of the operation
    """
    return call_wrapper("get_query_details", query_id)

def analyze_production_trend(query_id):
    """
    Analyze the production trend for a specific query.
    
    Args:
        query_id (int): ID of the query
        
    Returns:
        dict: The result of the operation
    """
    return call_wrapper("analyze_trend", query_id)

# Example button event handler for retrieving lease data
def retrieveLeaseDataButtonClick(event):
    """
    Example event handler for a button click to retrieve lease data.
    
    Args:
        event: The button click event
    """
    # Get values from form components
    identifier_type = event.source.parent.getComponent('IdentifierTypeDropdown').selectedValue
    identifier_value = event.source.parent.getComponent('IdentifierValueField').text
    beg_period = event.source.parent.getComponent('BegPeriodField').text
    end_period = event.source.parent.getComponent('EndPeriodField').text
    
    # Call the function to retrieve lease data
    result = retrieve_lease_data(identifier_type, identifier_value, beg_period, end_period)
    
    # Check if the operation was successful
    if result['status'] == 'success':
        # Update table with data
        event.source.parent.getComponent('ResultsTable').data = result['data']
        
        # Update statistics display
        stats_text = ""
        for stat in result['stats']:
            stats_text += f"{stat['Statistic']}: {stat['Value']}\n"
        event.source.parent.getComponent('StatsText').text = stats_text
        
        # Display percentage change
        if result['pct_change'] is not None:
            if result['pct_change'] <= -50:
                event.source.parent.getComponent('AlertText').text = f"⚠️ Significant lease drop detected! Production decreased by {abs(result['pct_change']):.2f}%"
            elif result['pct_change'] < 0:
                event.source.parent.getComponent('AlertText').text = f"Production decreased by {abs(result['pct_change']):.2f}%"
            else:
                event.source.parent.getComponent('AlertText').text = f"Production increased by {result['pct_change']:.2f}%"
    else:
        # Display error message
        system.gui.messageBox(result['message'])

# Example button event handler for viewing historical queries
def viewHistoricalQueriesButtonClick(event):
    """
    Example event handler for a button click to view historical queries.
    
    Args:
        event: The button click event
    """
    # Call the function to get historical queries
    result = get_historical_queries()
    
    # Check if the operation was successful
    if result['status'] == 'success':
        # Update table with queries
        event.source.parent.getComponent('QueriesTable').data = result['queries']
    else:
        # Display error message
        system.gui.messageBox(result['message'])

# Example button event handler for viewing query details
def viewQueryDetailsButtonClick(event):
    """
    Example event handler for a button click to view query details.
    
    Args:
        event: The button click event
    """
    # Get selected query ID from table
    selected_row = event.source.parent.getComponent('QueriesTable').selectedRow
    if selected_row < 0:
        system.gui.messageBox("Please select a query")
        return
    
    query_id = event.source.parent.getComponent('QueriesTable').data[selected_row]['id']
    
    # Call the function to get query details
    result = get_query_details(query_id)
    
    # Check if the operation was successful
    if result['status'] == 'success':
        # Update table with data
        event.source.parent.getComponent('ResultsTable').data = result['data']
        
        # Update statistics display
        stats_text = ""
        for stat in result['stats']:
            stats_text += f"{stat['Statistic']}: {stat['Value']}\n"
        event.source.parent.getComponent('StatsText').text = stats_text
        
        # Display percentage change
        if result['pct_change'] is not None:
            if result['pct_change'] <= -50:
                event.source.parent.getComponent('AlertText').text = f"⚠️ Significant lease drop detected! Production decreased by {abs(result['pct_change']):.2f}%"
            elif result['pct_change'] < 0:
                event.source.parent.getComponent('AlertText').text = f"Production decreased by {abs(result['pct_change']):.2f}%"
            else:
                event.source.parent.getComponent('AlertText').text = f"Production increased by {result['pct_change']:.2f}%"
    else:
        # Display error message
        system.gui.messageBox(result['message'])

# Example button event handler for analyzing production trend
def analyzeProductionTrendButtonClick(event):
    """
    Example event handler for a button click to analyze production trend.
    
    Args:
        event: The button click event
    """
    # Get selected query ID from table
    selected_row = event.source.parent.getComponent('QueriesTable').selectedRow
    if selected_row < 0:
        system.gui.messageBox("Please select a query")
        return
    
    query_id = event.source.parent.getComponent('QueriesTable').data[selected_row]['id']
    
    # Call the function to analyze production trend
    result = analyze_production_trend(query_id)
    
    # Check if the operation was successful
    if result['status'] == 'success':
        # Update table with data
        event.source.parent.getComponent('TrendTable').data = result['data']
        
        # Update trend information display
        trend_text = f"Trend Direction: {result['trend']['direction']}\n"
        trend_text += f"Trend Strength: {result['trend']['strength']:.2f}\n"
        trend_text += f"Slope: {result['trend']['slope']:.2f}\n"
        trend_text += f"R-Value: {result['trend']['r_value']:.2f}"
        event.source.parent.getComponent('TrendText').text = trend_text
    else:
        # Display error message
        system.gui.messageBox(result['message'])
