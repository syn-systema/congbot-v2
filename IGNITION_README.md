# Lease Drop - Crude Oil Inquiry for Ignition Maker

This project provides Python scripts that can be used within Ignition Maker to retrieve and analyze lease drop data from the Texas Comptroller's website. The scripts handle web scraping, data processing, and database storage, allowing you to build a comprehensive lease drop analysis system within Ignition.

## Overview

The Lease Drop - Crude Oil Inquiry application allows you to:

1. Search for lease data using either a Lease Number or a Drilling Permit Number
2. Specify a date range for the search
3. Retrieve and parse data from the Texas Comptroller's website
4. Store the data in a database for historical analysis
5. Display the data in Ignition tables and graphs
6. Analyze production trends and detect significant lease drops

## Files

- `lease_drop_core.py`: Core functionality for web scraping and data processing
- `database_schema.py`: Database schema and utility functions
- `ignition_integration.py`: Ignition-specific functions for integration

## Setup Instructions

### Prerequisites

1. Ignition Maker Edition installed
2. Python 3.6+ with the following packages:
   - selenium
   - pandas
   - lxml
   - scipy (for trend analysis)
3. Chrome WebDriver installed and configured

### Installation

1. Create a directory for the scripts in your Ignition project
2. Copy the following files to that directory:
   - `lease_drop_core.py`
   - `database_schema.py`
   - `ignition_integration.py`
3. Create a `data` subdirectory for the SQLite database

### Database Configuration

By default, the scripts use SQLite and store the database in a `data` subdirectory. You can modify the database path in the scripts if needed.

## Using in Ignition

### 1. Import the Scripts

In your Ignition project, you'll need to import the scripts. This can be done in several ways:

#### Option 1: Using Ignition's Script Module

1. In Ignition Designer, go to the Script Module
2. Create a new script
3. Add the following code to import the functions:

```python
# Import the ignition_integration module
import sys
import os

# Get the path to the scripts directory
script_path = system.file.getAbsolutePath('path/to/scripts')

# Add the script directory to the Python path
if script_path not in sys.path:
    sys.path.append(script_path)

# Import the module
try:
    from ignition_integration import (
        ignition_retrieve_lease_data,
        ignition_get_historical_queries,
        ignition_get_query_details,
        ignition_analyze_production_trend
    )
    print("Successfully imported ignition_integration module")
except ImportError as e:
    print(f"Error importing module: {e}")
```

#### Option 2: Using Ignition's Project Library

1. In Ignition Designer, go to the Project Library
2. Create a new Python module
3. Copy the contents of the scripts into the module
4. Use the functions directly in your Ignition scripts

### 2. Create Ignition Components

#### Data Entry Form

Create a form with the following components:

1. Dropdown for selecting identifier type (Lease Number or Drilling Permit Number)
2. Text field for entering the identifier value
3. Text fields for entering beginning and ending periods
4. Button to submit the query

#### Results Display

Create components to display the results:

1. Table component for displaying the lease data
2. Chart component for visualizing production trends
3. Text components for displaying statistics and alerts

### 3. Script the Components

#### Submit Button Script

```python
# Get values from form components
identifier_type = event.source.parent.getComponent('IdentifierTypeDropdown').selectedValue
identifier_value = event.source.parent.getComponent('IdentifierValueField').text
beg_period = event.source.parent.getComponent('BegPeriodField').text
end_period = event.source.parent.getComponent('EndPeriodField').text

# Call the function to retrieve lease data
result = ignition_retrieve_lease_data(identifier_type, identifier_value, beg_period, end_period)

# Check if the operation was successful
if result['status'] == 'success':
    # Update table with data
    event.source.parent.getComponent('ResultsTable').data = result['data']
    
    # Update statistics display
    stats_text = ""
    for stat in result['stats']:
        stats_text += f"{stat['Statistic']}: {stat['Value']}\n"
    event.source.parent.getComponent('StatsText').text = stats_text
    
    # Update chart with data
    chart_data = []
    for row in result['data']:
        chart_data.append({
            'x': row[result['date_col']],
            'y': row[result['production_col']]
        })
    event.source.parent.getComponent('ProductionChart').data = chart_data
    
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
```

#### Historical Queries Button Script

```python
# Call the function to get historical queries
result = ignition_get_historical_queries()

# Check if the operation was successful
if result['status'] == 'success':
    # Update table with queries
    event.source.parent.getComponent('QueriesTable').data = result['queries']
else:
    # Display error message
    system.gui.messageBox(result['message'])
```

#### Query Details Button Script

```python
# Get selected query ID from table
selected_row = event.source.parent.getComponent('QueriesTable').selectedRow
if selected_row < 0:
    system.gui.messageBox("Please select a query")
    return

query_id = event.source.parent.getComponent('QueriesTable').data[selected_row]['id']

# Call the function to get query details
result = ignition_get_query_details(query_id)

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
```

#### Analyze Trend Button Script

```python
# Get selected query ID from table
selected_row = event.source.parent.getComponent('QueriesTable').selectedRow
if selected_row < 0:
    system.gui.messageBox("Please select a query")
    return

query_id = event.source.parent.getComponent('QueriesTable').data[selected_row]['id']

# Call the function to analyze production trend
result = ignition_analyze_production_trend(query_id)

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
    
    # Update chart with data
    chart_data = []
    for row in result['data']:
        chart_data.append({
            'x': row[result['date_col']],
            'y': row[result['production_col']]
        })
    event.source.parent.getComponent('TrendChart').data = chart_data
else:
    # Display error message
    system.gui.messageBox(result['message'])
```

## Troubleshooting

### Common Issues

1. **ImportError**: Make sure the script path is correct and the required modules are installed.
2. **WebDriver Error**: Ensure Chrome WebDriver is installed and properly configured.
3. **Database Error**: Check that the database directory exists and is writable.

### Logging

The scripts use Python's logging module to log information and errors. You can view the logs in Ignition's console or configure the logging to write to a file.

## Advanced Configuration

### Customizing the Database

By default, the scripts use SQLite for simplicity. You can modify the database connection code in `database_schema.py` to use other database systems supported by Ignition, such as MySQL or PostgreSQL.

### Customizing Web Scraping

The web scraping logic is in `lease_drop_core.py`. You may need to update this code if the Texas Comptroller's website changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
