#!/usr/bin/env python3
"""
Test script for the Lease Drop REST API.
This script sends a test request to the REST API and prints the response.
"""

import requests
import json
import sys

def test_api(api_url="http://localhost:5000"):
    """
    Test the Lease Drop REST API.
    
    Args:
        api_url (str): The URL of the REST API server
    """
    print(f"Testing API at {api_url}")
    
    # Test health check endpoint
    try:
        response = requests.get(f"{api_url}/health")
        print(f"Health check status code: {response.status_code}")
        print(f"Health check response: {response.json()}")
    except Exception as e:
        print(f"Error testing health check endpoint: {e}")
        return
    
    # Test retrieve_data endpoint with sample data
    try:
        data = {
            "identifier_type": "Lease Number",
            "identifier_value": "011457",
            "beg_period": "1601",
            "end_period": "2001"
        }
        
        print(f"Sending test request with data: {data}")
        
        response = requests.post(f"{api_url}/api/retrieve_data", json=data)
        
        print(f"Retrieve data status code: {response.status_code}")
        
        # Pretty print the response
        try:
            response_json = response.json()
            print("Response:")
            print(json.dumps(response_json, indent=2))
        except:
            print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"Error testing retrieve_data endpoint: {e}")

if __name__ == "__main__":
    # Get API URL from command line argument or use default
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    # Test the API
    test_api(api_url)
