FROM python:3.12-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy the project files into the image
COPY . /app

# Export dependencies to requirements.txt
RUN uv export -o requirements.txt

# Install dependencies directly into the system environment
RUN pip install --no-cache-dir -r requirements.txt

# Run the FastAPI application
CMD ["fastapi", "dev", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]
