#!/bin/bash

# BookBytes Docker Health Check Script

# Default URL
URL="http://localhost:5000/health"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -u|--url)
      URL="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [-u|--url URL]"
      exit 1
      ;;
  esac
done

echo "Checking BookBytes health at $URL..."

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "Error: curl is not installed. Please install curl first."
    exit 1
fi

# Check if the container is running
if ! docker-compose ps | grep -q "bookbytes-app"; then
    echo "Error: BookBytes container is not running."
    echo "Start the container with: docker-compose up -d"
    exit 1
fi

# Make the health check request
response=$(curl -s -w "\n%{http_code}" $URL)
status_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | sed '$d')

# Check the status code
if [ "$status_code" -eq 200 ]; then
    echo "✅ BookBytes is healthy!"
    echo "Response:"
    echo "$response_body" | python -m json.tool
    exit 0
else
    echo "❌ BookBytes health check failed with status code: $status_code"
    echo "Response:"
    echo "$response_body"
    exit 1
fi