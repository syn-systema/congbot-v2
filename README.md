# Lease Drop - Crude Oil Inquiry Application

A Streamlit-based web application designed to retrieve and analyze lease drop data from the Texas Comptroller's website, focusing on crude oil production for specific leases.

## Features

- **User-friendly Interface**: Input lease numbers or drilling permit numbers along with time periods
- **Robust Web Scraping**: Navigate the Texas Comptroller website with reliable form element detection
- **Data Visualization**: View production data with summary statistics and charts
- **AI Assistant**: Gemini-powered chatbot to help analyze and understand lease data
- **Error Handling**: Comprehensive logging and debugging capabilities

## Requirements

- Python 3.9+
- Streamlit
- Selenium
- pandas
- lxml
- Google Chrome (for Selenium WebDriver)
- Google Generative AI (for Gemini AI Assistant)

## Installation

### Using Docker (Recommended)

1. Build the Docker image:

   ```bash
   docker build -t cong-app .
   ```

2. Run the container:

   ```bash
   docker run --rm -p 8502:8502 -v "$(pwd)/screenshots:/app/screenshots" -e GEMINI_API_KEY=your_api_key_here cong-app
   ```

3. Access the application at http://localhost:8502

### Manual Installation

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Install Chrome WebDriver (compatible with your Chrome version)

3. Set your Gemini API key:

   ```bash
   # Option 1: Use the provided script
   ./set_api_key.sh your_api_key_here
   
   # Option 2: Set environment variable manually
   export GEMINI_API_KEY=your_api_key_here
   streamlit run app.py
   ```

4. Run the application:

   ```bash
   streamlit run app.py
   ```

## Usage

1. Enter either a Lease Number (6 digits) OR a Drilling Permit Number (6 digits)
2. Specify Begin Period and End Period in yymm or yy format
3. Click "Get Lease Drop Data"
4. View the retrieved data, summary statistics, and visualizations
5. Switch to the "AI Assistant" tab to ask questions about your lease data

## AI Assistant

The application includes a Gemini-powered AI assistant that can:

- Answer questions about your retrieved lease data
- Provide insights and analysis on production trends
- Explain terminology and concepts related to oil leases
- Help interpret the data in natural language

To use the AI Assistant:

1. First retrieve lease data in the "Data Retrieval" tab
2. Switch to the "AI Assistant" tab
3. Ask questions about your data in natural language

You'll need a Gemini API key from [Google AI Studio](https://ai.google.dev/) to use this feature.

## Troubleshooting

If you encounter issues with the web scraping:

1. Check the screenshots directory for debug information
2. Ensure you have a stable internet connection
3. Verify that your input parameters are correctly formatted

If the AI Assistant is not working:

1. Make sure you've set your Gemini API key correctly
2. Retrieve lease data before using the AI Assistant
3. Check your internet connection as the AI requires API calls

## License

This project is proprietary and confidential.

## Author

CPS
