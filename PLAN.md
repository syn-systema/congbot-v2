# Streamlit Lease Search Application - Final Plan

This plan outlines the steps to create the Streamlit application, incorporating Selenium Manager for ChromeDriver handling and using a `requirements.txt` file for Python dependencies.

## 1. Create `requirements.txt`

Create a file named `requirements.txt` with the following content:

```
streamlit
selenium>=4.6.0
pandas
```

This file specifies the necessary Python packages, ensuring a recent enough Selenium version for Selenium Manager.

## 2. Create `app.py`

Create a file named `app.py` containing the Python code for the Streamlit application exactly as provided in the initial problem description. No changes are needed in the Python code itself, as Selenium Manager works automatically behind the scenes.

## 3. Create `Dockerfile`

Create a file named `Dockerfile` with the following content:

```dockerfile
FROM python:3.9-slim

# Install system dependencies (including wget for Chrome install)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome (latest stable)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set up application directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt /app/requirements.txt

# Install Python dependencies (Selenium Manager will handle ChromeDriver)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py /app/app.py

# Expose Streamlit port
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

This Dockerfile installs Google Chrome but **omits** the manual ChromeDriver installation, relying on Selenium Manager. It copies and uses `requirements.txt`.

## 4. Create `deploy.sh`

Create a file named `deploy.sh` containing the bash script exactly as provided in the initial problem description:

```bash
#!/bin/bash

# Build the Docker image
docker build -t lease-search-app .

# Stop and remove any existing container with the same name
docker stop lease-search-app-container 2>/dev/null
docker rm lease-search-app-container 2>/dev/null

# Run the container in detached mode
docker run -d --name lease-search-app-container -p 8501:8501 lease-search-app

echo "Application deployed. Access it at http://localhost:8501"
```

## Next Steps

Proceed to implement this plan by creating these four files (`requirements.txt`, `app.py`, `Dockerfile`, `deploy.sh`) with the specified content.