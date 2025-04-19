#!/bin/bash

# Deploy Lease Drop - Crude Oil Inquiry Application with Nginx
# This script sets up Nginx as a reverse proxy for your Streamlit application

# Stop script on error
set -e

echo "=== Lease Drop - Crude Oil Inquiry Application Deployment ==="
echo "This script will set up Nginx as a reverse proxy for your Streamlit application"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo"
  exit 1
fi

# Get the server IP or domain name
read -p "Enter your server's public IP address or domain name: " SERVER_NAME

# Update Nginx configuration with the server name
sed -i "s/your-server-domain-or-ip/$SERVER_NAME/g" nginx-congbot.conf

# Copy Nginx configuration to the appropriate directory
echo "Copying Nginx configuration..."
cp nginx-congbot.conf /etc/nginx/sites-available/congbot.conf

# Create symbolic link to enable the site
ln -sf /etc/nginx/sites-available/congbot.conf /etc/nginx/sites-enabled/

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Restart Nginx to apply changes
echo "Restarting Nginx..."
systemctl restart nginx

# Build and run the Docker container in detached mode
echo "Building and running the Docker container..."
docker build -t cong-app .
docker stop cong-app 2>/dev/null || true
docker rm cong-app 2>/dev/null || true
docker run -d --name cong-app -p 8505:8502 cong-app

echo "=== Deployment Complete ==="
echo "Your application should now be accessible at: http://$SERVER_NAME"
echo "To check the status of your container, run: docker ps"
echo "To view logs, run: docker logs cong-app"
