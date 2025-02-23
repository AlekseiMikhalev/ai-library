FROM python:3.12-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create a non-root user and set up app directory
RUN groupadd -r appgroup \
    && useradd -r -g appgroup -G appgroup -m -d /home/appuser -s /sbin/nologin -c "App User" appuser


# Set the working directory
WORKDIR /app

# Copy the project files into the image
COPY . /app

# Export dependencies to requirements.txt
RUN uv export -o requirements.txt

# Install dependencies directly into the system environment
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user context
USER appuser

# Run the FastAPI application
CMD ["fastapi", "dev", "src/main.py", "--port", "8000", "--host", "0.0.0.0"]
