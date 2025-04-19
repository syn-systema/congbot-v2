#!/bin/bash

# Define image and container names
IMAGE_NAME="lease-search-app"
CONTAINER_NAME="lease-search-app-container"

echo "Building the Docker image: $IMAGE_NAME..."
# Build the Docker image, tag it with the defined name
docker build -t $IMAGE_NAME .

# Check if build was successful
if [ $? -ne 0 ]; then
  echo "Docker build failed. Exiting."
  exit 1
fi

echo "Stopping and removing any existing container named $CONTAINER_NAME..."
# Stop the container if it's running (ignore errors if it doesn't exist)
docker stop $CONTAINER_NAME > /dev/null 2>&1
# Remove the container if it exists (ignore errors if it doesn't exist)
docker rm $CONTAINER_NAME > /dev/null 2>&1

echo "Running the new container: $CONTAINER_NAME..."
# Run the container in detached mode (-d)
# Map host port 8501 to container port 8501 (-p 8501:8501)
# Name the container (--name)
docker run -d --name $CONTAINER_NAME -p 8501:8501 $IMAGE_NAME

# Check if container started successfully
if [ $? -ne 0 ]; then
  echo "Failed to start the Docker container. Check Docker logs for $CONTAINER_NAME."
  exit 1
fi

echo "-----------------------------------------------------"
echo "Application deployed successfully!"
echo "Access it in your browser at: http://localhost:8501"
echo "To view logs: docker logs $CONTAINER_NAME"
echo "To stop the container: docker stop $CONTAINER_NAME"
echo "-----------------------------------------------------"