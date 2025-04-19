# Use a lightweight Python base image
FROM python:3.9-slim

# Install system dependencies and Google Chrome
RUN apt-get update && apt-get install -y wget gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Set the working directory inside the container
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the entire project directory into the container
COPY . .

# Expose the default Streamlit port
EXPOSE 8502

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port", "8502"]