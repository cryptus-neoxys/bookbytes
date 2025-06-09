#!/bin/bash

# BookBytes Docker Setup Script

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found."
    echo "Creating a template .env file. Please edit it with your OpenAI API key."
    cp .env.example .env
    echo "Please edit the .env file with your OpenAI API key and run this script again."
    exit 1
fi

# Check if OpenAI API key is set in .env
if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=your-openai-api-key-here" .env; then
    echo "Error: OpenAI API key not set in .env file."
    echo "Please edit the .env file with your OpenAI API key and run this script again."
    exit 1
fi

# Build and start the container
echo "Building and starting BookBytes container..."
docker-compose up -d --build

# Check if container is running
if [ "$(docker-compose ps -q)" ]; then
    echo "BookBytes is now running!"
    echo "Access the application at http://localhost:5000"
    echo ""
    echo "Useful commands:"
    echo "  - View logs: docker-compose logs -f"
    echo "  - Stop container: docker-compose down"
    echo "  - Restart container: docker-compose restart"
else
    echo "Error: Failed to start BookBytes container."
    echo "Check the logs for more information: docker-compose logs"
    exit 1
fi