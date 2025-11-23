# Use Ubuntu as base image
FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install required dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libxml2 \
    libicu70 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files from current directory to /app in container
COPY . /app/

# Ensure ds-server and ds-client are executable
RUN chmod +x ds-server ds-client

# Default command (you can override this when running)
CMD ["/bin/bash"]

