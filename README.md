# Lease Drop - Crude Oil Inquiry Application

A containerized REST API solution for retrieving and analyzing lease drop data from the Texas Comptroller's website, designed for integration with Ignition Maker.

## Features

- **Dockerized Solution**: Fully containerized application with all dependencies included
- **REST API**: Flask-based API for easy integration with Ignition Maker
- **Robust Web Scraping**: Navigate the Texas Comptroller website with reliable form element detection
- **Data Processing**: Extract and analyze production data with summary statistics
- **Persistent Storage**: Database storage for query results and historical data
- **Error Handling**: Comprehensive logging and debugging capabilities

## Architecture

The application has been transformed from a Streamlit-based web app to a Docker-containerized REST API solution:

1. **Docker Container**: Based on the official Selenium Chrome Node image with Python 3 support
2. **REST API**: Flask server exposing endpoints for lease data retrieval and analysis
3. **Database**: SQLite database for persistent storage of query results
4. **Web Scraping**: Selenium WebDriver for reliable interaction with the Texas Comptroller's website
5. **Ignition Integration**: Python client for calling the REST API from Ignition Maker

## Requirements

- Docker and Docker Compose
- Ignition Maker (for UI integration)

## Installation

### Using Docker Compose (Recommended)

1. Build and start the Docker container:

   ```bash
   docker compose up -d
   ```

2. The REST API will be available at http://localhost:5000

### Manual Installation (Development Only)

1. Install dependencies:

   ```bash
   pip install -r ignition_requirements.txt
   pip install flask
   ```

2. Install Chrome and ChromeDriver (compatible with your Chrome version)

3. Run the REST API server:

   ```bash
   python rest_api.py
   ```

## API Endpoints

- **GET /health**: Check if the API is running
- **POST /api/retrieve_data**: Retrieve lease drop data
  - Parameters:
    - identifier_type: "Lease Number" or "Drilling Permit Number"
    - identifier_value: The value of the identifier
    - beg_period: Beginning period in yymm or yy format
    - end_period: Ending period in yymm or yy format
- **GET /api/history**: Get historical queries
- **GET /api/query/{query_id}**: Get details for a specific query

## API Usage

The REST API provides the following endpoints:

- `/health` - Health check endpoint
- `/api/retrieve_data` - Retrieve lease drop data

### Example API Request

```json
{
  "identifier_type": "Lease Number",
  "identifier_value": "011457",
  "beg_period": "1601",
  "end_period": "2001"
}
```

### Example API Response

```json
{
  "status": "success",
  "query_info": {
    "timestamp": "2025-04-20T04:14:31.303140",
    "identifier_type": "Lease Number",
    "identifier_value": "011457",
    "beg_period": "1601",
    "end_period": "2001",
    "status": "success"
  },
  "production_column": "Gross Barrels",
  "date_column": "Period",
  "percentage_change": 7614.62,
  "statistics": [
    {
      "Statistic": "Count",
      "Value": 54.0
    },
    {
      "Statistic": "Mean",
      "Value": 22912.81
    },
    {
      "Statistic": "Median",
      "Value": 9768.5
    },
    {
      "Statistic": "Min",
      "Value": 0.0
    },
    {
      "Statistic": "Max",
      "Value": 203514.0
    },
    {
      "Statistic": "Std Dev",
      "Value": 41465.53
    }
  ]
}
```

## Testing

Use the provided test script to verify the API functionality:

```bash
python test_api.py
```

## Ignition Integration

The `ignition_rest_client.py` script provides methods for calling the REST API from Ignition Maker:

1. Import the script into your Ignition project
2. Use the provided functions to retrieve and process lease data
3. Display the results in your Ignition UI

## Troubleshooting

If you encounter issues with the Docker container:

1. Check the container logs:
   ```bash
   docker compose logs
   ```

2. Ensure the container has access to the internet for web scraping

3. Verify that your input parameters are correctly formatted

## License

This project is proprietary and confidential.

## Author

CPS
