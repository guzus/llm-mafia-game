#!/bin/bash

# Check if service parameter is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <service_name>"
    echo "Example: $0 dashboard"
    echo "Example: $0 simulation"
    exit 1
fi

SERVICE_NAME=$1

# Load configuration
CONFIG_FILE="$(dirname "$0")/remote-config.sh"

if [ -f "$CONFIG_FILE" ]; then
    . "$CONFIG_FILE"
else
    echo "Error: Configuration file not found at $CONFIG_FILE"
    echo "Please create the configuration file with SSH_USER, SSH_HOST, and COMPOSE_DIR variables."
    exit 1
fi

# Validate required variables
if [ -z "$SSH_USER" ] || [ -z "$SSH_HOST" ] || [ -z "$COMPOSE_DIR" ]; then
    echo "Error: Missing required configuration variables."
    echo "Please ensure SSH_USER, SSH_HOST, and COMPOSE_DIR are defined in $CONFIG_FILE"
    exit 1
fi

# Set up SSH key option if PEM_KEY_PATH is defined
SSH_OPTS=""
if [ -n "$PEM_KEY_PATH" ]; then
    SSH_OPTS="-i $PEM_KEY_PATH"
fi

# SSH into the remote machine, pull the image and start only the specified service
echo "Connecting to $SSH_USER@$SSH_HOST..."
echo "Pulling latest Docker images and starting $SERVICE_NAME service..."
ssh $SSH_OPTS $SSH_USER@$SSH_HOST "cd $COMPOSE_DIR && docker-compose pull && docker-compose down $SERVICE_NAME && docker-compose up -d $SERVICE_NAME"

echo "$SERVICE_NAME service started successfully."
echo "You can access the $SERVICE_NAME at the configured URL." 