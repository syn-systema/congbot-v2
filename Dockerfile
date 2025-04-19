# Use a lightweight Python base image
FROM python:3.9-slim

# Install system dependencies, Google Chrome, Nginx, and Supervisor
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    nginx \
    supervisor \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the entire project directory into the container
COPY . .

# Set up Nginx
COPY nginx.conf /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

# Set up Supervisor to manage processes
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the default Nginx port
EXPOSE 80

# Command to start Supervisor which will start both Nginx and Streamlit
CMD ["/usr/bin/supervisord"]