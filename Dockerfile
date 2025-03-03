FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY .python-version .
COPY pyproject.toml .
RUN pip install uv
RUN uv sync

# Copy the application code
COPY src/ src/
COPY .env .

# Create directories for logs
RUN mkdir -p logs

# Expose port for the web dashboard
EXPOSE 5001

# Command to run the dashboard (can be overridden)
CMD ["uv", "run", "src/dashboard.py", "--port", "5001"]