"""
Ignition script to call the lease drop REST API.
This script should be added to your Ignition project as a Script Module.

Usage:
1. Create a new Script Module in Ignition Designer
2. Copy this code into the Script Module
3. Call these functions from your Ignition components
"""

import system
import json

# URL of the REST API server
API_URL = "http://localhost:5000/api"  # Update this to match your Docker container's address

def call_api(endpoint, method="GET", data=None):
    """
    Call the REST API with the given endpoint, method, and data.
    
    Args:
        endpoint (str): The API endpoint to call
        method (str): The HTTP method to use (GET, POST, etc.)
        data (dict): The data to send in the request body (for POST requests)
        
    Returns:
        dict: The result of the API call
    """
    try:
        # Create HTTP client
        client = system.net.httpClient()
        
        # Build the URL
        url = f"{API_URL}/{endpoint}"
        
        # Make the request
        if method == "GET":
            response = client.get(url)
        elif method == "POST":
            headers = {"Content-Type": "application/json"}
            json_data = system.util.jsonEncode(data)
            response = client.post(url, json_data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Check if the request was successful
        if response.getStatusCode() >= 200 and response.getStatusCode() < 300:
            # Parse the JSON response
            return system.util.jsonDecode(response.getBody())
        else:
            # Handle error response
            error_message = f"API call failed with status code {response.getStatusCode()}: {response.getBody()}"
            system.util.getLogger("LeaseDropIntegration").error(error_message)
            return {
                'status': 'error',
                'message': error_message
            }
    except Exception as e:
        # Handle any errors
        system.util.getLogger("LeaseDropIntegration").error(f"Error calling API: {e}")
        return {
            'status': 'error',
            'message': f"Error calling API: {e}"
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
    data = {
        "identifier_type": identifier_type,
        "identifier_value": identifier_value,
        "beg_period": beg_period,
        "end_period": end_period
    }
    return call_api("retrieve_data", method="POST", data=data)

def get_historical_queries():
    """
    Get all historical queries.
    
    Returns:
        dict: The result of the operation
    """
    return call_api("get_queries")

def get_query_details(query_id):
    """
    Get details of a specific query.
    
    Args:
        query_id (int): ID of the query
        
    Returns:
        dict: The result of the operation
    """
    return call_api(f"get_query_details/{query_id}")

def analyze_production_trend(query_id):
    """
    Analyze the production trend for a specific query.
    
    Args:
        query_id (int): ID of the query
        
    Returns:
        dict: The result of the operation
    """
    return call_api(f"analyze_trend/{query_id}")

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
