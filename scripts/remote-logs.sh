#!/bin/bash

# Load configuration
CONFIG_FILE="$(dirname "$0")/remote-config.sh"

if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
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

# SSH into the remote machine and run docker-compose logs -f
echo "Connecting to $SSH_USER@$SSH_HOST..."
ssh $SSH_OPTS $SSH_USER@$SSH_HOST "cd $COMPOSE_DIR && docker-compose logs -f" 