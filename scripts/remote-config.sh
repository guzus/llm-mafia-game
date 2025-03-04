# Remote server configuration
# Load variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo ".env file not found"
  exit 1
fi

# Use variables from .env or fallback to defaults
SSH_USER="${SSH_USER}"
SSH_HOST="${SSH_HOST}"
COMPOSE_DIR="${COMPOSE_DIR}"
PEM_KEY_PATH="${PEM_KEY_PATH}"

# Check if all variables are set
if [ -z "${SSH_USER}" ] || [ -z "${SSH_HOST}" ] || [ -z "${COMPOSE_DIR}" ] || [ -z "${PEM_KEY_PATH}" ]; then
  echo "Error: Some environment variables are not set"
  exit 1
fi