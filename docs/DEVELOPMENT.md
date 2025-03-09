# Deployment Guide for LLM Mafia Game Competition

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your system
- OpenRouter API key
- Firebase credentials file

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/guzus/llm-mafia-game.git
cd llm-mafia-game
```

### 2. Prepare Environment

1. **Firebase Credentials**: Ensure you have your `firebase_credentials.json` file in the project root directory.

2. **Set OpenRouter API Key**: Create a `.env` file in the project root with your OpenRouter API key:

```bash
echo "OPENROUTER_API_KEY=your-openrouter-api-key" > .env
```

### 3. Deploy with Docker Compose

Deploy both the dashboard and simulation services:

```bash
docker-compose up -d
```

Deploy only the dashboard:

```bash
docker-compose up -d dashboard
```

Deploy only the simulation:

```bash
docker-compose up -d simulation
```

### 4. Access the Dashboard

Once the services are running, access the dashboard at:

```
http://localhost:5001
```

### 5. Managing the Deployment

**View logs:**

```bash
docker-compose logs -f
```

**Stop services:**

```bash
docker-compose down
```

**Rebuild after code changes:**

```bash
docker-compose build
docker-compose up -d
```

## Troubleshooting

- **Port conflict**: If port 5001 is already in use, modify the `ports` section in docker-compose.yml to use a different port (e.g., "5002:5001").
- **API key issues**: Ensure your `.env` file is correctly formatted and in the project root.
- **Firebase connectivity**: Verify that your `firebase_credentials.json` is valid and has the correct permissions.
