FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy requirements and install dependencies
COPY .python-version .
COPY pyproject.toml .
COPY uv.lock .
RUN pip install uv
RUN uv sync --frozen

# Copy the application code
COPY src/ src/

# Create directories for logs
RUN mkdir -p logs

# Expose port for the web dashboard
EXPOSE 5001

# Command to run the dashboard (can be overridden)
CMD ["uv", "run", "src/dashboard.py"]
