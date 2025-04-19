# Lease Drop - Crude Oil Inquiry Application

A Streamlit-based web application designed to retrieve and analyze lease drop data from the Texas Comptroller's website, focusing on crude oil production for specific leases.

## Features

- **User-friendly Interface**: Input lease numbers or drilling permit numbers along with time periods
- **Robust Web Scraping**: Navigate the Texas Comptroller website with reliable form element detection
- **Data Visualization**: View production data with summary statistics and charts
- **Error Handling**: Comprehensive logging and debugging capabilities

## Requirements

- Python 3.9+
- Streamlit
- Selenium
- pandas
- lxml
- Google Chrome (for Selenium WebDriver)

## Installation

### Using Docker (Recommended)

1. Build the Docker image:
   ```
   docker build -t cong-app .
   ```

2. Run the container:
   ```
   docker run --rm -p 8502:8502 -v "$(pwd)/screenshots:/app/screenshots" cong-app
   ```

3. Access the application at http://localhost:8502

### Manual Installation

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Install Chrome WebDriver (compatible with your Chrome version)

3. Run the application:
   ```
   streamlit run app.py
   ```

## Usage

1. Enter either a Lease Number (6 digits) OR a Drilling Permit Number (6 digits)
2. Specify Begin Period and End Period in yymm or yy format
3. Click "Get Lease Drop Data"
4. View the retrieved data, summary statistics, and visualizations

## Troubleshooting

If you encounter issues with the web scraping:

1. Check the screenshots directory for debug information
2. Ensure you have a stable internet connection
3. Verify that your input parameters are correctly formatted

## License

This project is proprietary and confidential.

## Author

Created for Texas Comptroller Lease Data Analysis
