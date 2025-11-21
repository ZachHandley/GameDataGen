# GameDataGen Docker Image
FROM python:3.12-slim

# Install uv for fast package management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies with uv
RUN uv pip install --system .

# Create mount points for project data
VOLUME /project

# Expose API port
EXPOSE 8000

# Default command: show help
CMD ["gamedatagen", "--help"]

# To run API server:
# docker run -p 8000:8000 -v $(pwd):/project gamedatagen gamedatagen serve --host 0.0.0.0
