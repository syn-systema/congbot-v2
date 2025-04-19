#!/bin/bash
# Script to set the Gemini API key as an environment variable

# Check if an API key was provided
if [ -z "$1" ]; then
  echo "Usage: ./set_api_key.sh YOUR_GEMINI_API_KEY"
  echo "You can get a Gemini API key from https://ai.google.dev/"
  exit 1
fi

# Set the API key as an environment variable
export GEMINI_API_KEY="$1"

# Run the Streamlit app with the API key set
echo "Starting Streamlit app with Gemini API key set..."
streamlit run app.py
