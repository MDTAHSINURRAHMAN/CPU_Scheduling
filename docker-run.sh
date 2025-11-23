#!/bin/bash
# Script to build and run the Docker container

echo "Building Docker image..."
docker build -t ds-test .

echo ""
echo "Running Docker container..."
docker run -it --rm ds-test

